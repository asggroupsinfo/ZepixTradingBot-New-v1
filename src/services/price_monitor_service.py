import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from src.models import Trade
from src.config import Config
import logging

class PriceMonitorService:
    """
    Background service to monitor prices every 30 seconds for:
    1. SL hunt re-entry (price reaches SL + offset)
    2. TP continuation re-entry (after TP hit with price gap)
    3. Reversal exit opportunities
    """
    
    def __init__(self, config: Config, mt5_client, reentry_manager, 
                 trend_manager, pip_calculator, trading_engine):
        self.config = config
        self.mt5_client = mt5_client
        self.reentry_manager = reentry_manager
        self.trend_manager = trend_manager
        self.pip_calculator = pip_calculator
        self.trading_engine = trading_engine
        
        self.is_running = False
        self.monitor_task = None
        
        # Track symbols being monitored
        self.monitored_symbols = set()
        
        # SL hunt re-entry tracking
        self.sl_hunt_pending = {}  # symbol -> {'price': sl+offset, 'direction': 'buy', 'chain_id': ...}
        
        # TP re-entry tracking
        self.tp_continuation_pending = {}  # symbol -> {'tp_price': ..., 'direction': ...}
        
        # Exit continuation tracking (Exit Appeared/Reversal signals)
        self.exit_continuation_pending = {}  # symbol -> {'exit_price': ..., 'direction': ..., 'exit_reason': ...}
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the background price monitoring task"""
        if self.is_running:
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        self.logger.info("SUCCESS: Price Monitor Service started")
    
    async def stop(self):
        """Stop the background price monitoring task"""
        self.is_running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("STOPPED: Price Monitor Service stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop - runs every 30 seconds"""
        interval = self.config["re_entry_config"]["price_monitor_interval_seconds"]
        
        while self.is_running:
            try:
                await self._check_all_opportunities()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(interval)
    
    async def _check_all_opportunities(self):
        """Check all pending re-entry opportunities"""
        
        # Check SL hunt re-entries
        await self._check_sl_hunt_reentries()
        
        # Check TP continuation re-entries
        await self._check_tp_continuation_reentries()
        
        # Check Exit continuation re-entries (NEW)
        await self._check_exit_continuation_reentries()
        
        # Check Profit Booking chains (NEW)
        await self._check_profit_booking_chains()
    
    async def _check_sl_hunt_reentries(self):
        """
        Check if price has reached SL + offset for automatic re-entry
        After SL hunt, wait for price to recover to SL + 1 pip, then re-enter
        """
        if not self.config["re_entry_config"]["sl_hunt_reentry_enabled"]:
            return
        
        for symbol in list(self.sl_hunt_pending.keys()):
            pending = self.sl_hunt_pending[symbol]
            
            # Get current price from MT5
            current_price = self._get_current_price(symbol, pending['direction'])
            if current_price is None:
                continue
            
            target_price = pending['target_price']
            direction = pending['direction']
            chain_id = pending['chain_id']
            
            # Check if price has reached target
            price_reached = False
            if direction == 'buy':
                price_reached = current_price >= target_price
            else:
                price_reached = current_price <= target_price
            
            if price_reached:
                # Validate trend alignment before re-entry
                logic = pending.get('logic', 'LOGIC1')
                alignment = self.trend_manager.check_logic_alignment(symbol, logic)
                
                if not alignment['aligned']:
                    self.logger.info(f"ERROR: SL hunt re-entry blocked - trend not aligned for {symbol}")
                    del self.sl_hunt_pending[symbol]
                    continue
                
                # Check signal direction matches alignment
                signal_direction = "BULLISH" if direction == "buy" else "BEARISH"
                if alignment['direction'] != signal_direction:
                    self.logger.info(f"ERROR: SL hunt re-entry blocked - direction mismatch for {symbol}")
                    del self.sl_hunt_pending[symbol]
                    continue
                
                # Execute SL hunt re-entry
                self.logger.info(f"TRIGGERED: SL Hunt Re-Entry Triggered: {symbol} @ {current_price}")
                
                # Create re-entry order with reduced SL
                await self._execute_sl_hunt_reentry(
                    symbol=symbol,
                    direction=direction,
                    price=current_price,
                    chain_id=chain_id,
                    logic=logic
                )
                
                # Remove from pending
                del self.sl_hunt_pending[symbol]
    
    async def _check_tp_continuation_reentries(self):
        """
        Check if price has moved enough after TP hit for re-entry
        After TP, wait for price gap (e.g., 2 pips), then re-enter with reduced SL
        """
        if not self.config["re_entry_config"]["tp_reentry_enabled"]:
            return
        
        for symbol in list(self.tp_continuation_pending.keys()):
            pending = self.tp_continuation_pending[symbol]
            
            # Get current price from MT5
            current_price = self._get_current_price(symbol, pending['direction'])
            if current_price is None:
                continue
            
            tp_price = pending['tp_price']
            direction = pending['direction']
            chain_id = pending['chain_id']
            price_gap_pips = self.config["re_entry_config"]["tp_continuation_price_gap_pips"]
            
            # Calculate pip value for symbol
            symbol_config = self.config["symbol_config"][symbol]
            pip_size = symbol_config["pip_size"]
            price_gap = price_gap_pips * pip_size
            
            # Check if price has moved enough from TP
            gap_reached = False
            if direction == 'buy':
                gap_reached = current_price >= (tp_price + price_gap)
            else:
                gap_reached = current_price <= (tp_price - price_gap)
            
            if gap_reached:
                # Validate trend alignment
                logic = pending.get('logic', 'LOGIC1')
                alignment = self.trend_manager.check_logic_alignment(symbol, logic)
                
                if not alignment['aligned']:
                    self.logger.info(f"ERROR: TP re-entry blocked - trend not aligned for {symbol}")
                    del self.tp_continuation_pending[symbol]
                    continue
                
                signal_direction = "BULLISH" if direction == "buy" else "BEARISH"
                if alignment['direction'] != signal_direction:
                    self.logger.info(f"ERROR: TP re-entry blocked - direction mismatch for {symbol}")
                    del self.tp_continuation_pending[symbol]
                    continue
                
                # Execute TP continuation re-entry
                self.logger.info(f"TRIGGERED: TP Continuation Re-Entry Triggered: {symbol} @ {current_price}")
                
                await self._execute_tp_continuation_reentry(
                    symbol=symbol,
                    direction=direction,
                    price=current_price,
                    chain_id=chain_id,
                    logic=logic
                )
                
                # Remove from pending
                del self.tp_continuation_pending[symbol]
    
    async def _check_exit_continuation_reentries(self):
        """
        Check for re-entry after Exit Appeared/Reversal exit signals
        After exit (Exit Appeared/Reversal), continue monitoring for re-entry with price gap
        Example: Exit @ 3640.200 → Monitor → Re-entry @ 3642.200 (gap required)
        """
        if not self.config["re_entry_config"].get("exit_continuation_enabled", True):
            return
        
        for symbol in list(self.exit_continuation_pending.keys()):
            pending = self.exit_continuation_pending[symbol]
            
            # Get current price from MT5
            current_price = self._get_current_price(symbol, pending['direction'])
            if current_price is None:
                continue
            
            exit_price = pending['exit_price']
            direction = pending['direction']
            logic = pending.get('logic', 'LOGIC1')
            exit_reason = pending.get('exit_reason', 'EXIT')
            price_gap_pips = self.config["re_entry_config"]["tp_continuation_price_gap_pips"]
            
            # Calculate pip value for symbol
            symbol_config = self.config["symbol_config"][symbol]
            pip_size = symbol_config["pip_size"]
            price_gap = price_gap_pips * pip_size
            
            # Check if price has moved enough from exit price (continuation direction)
            gap_reached = False
            if direction == 'buy':
                gap_reached = current_price >= (exit_price + price_gap)
            else:
                gap_reached = current_price <= (exit_price - price_gap)
            
            if gap_reached:
                # Validate trend alignment (CRITICAL - must match logic)
                alignment = self.trend_manager.check_logic_alignment(symbol, logic)
                
                if not alignment['aligned']:
                    self.logger.info(f"ERROR: Exit continuation blocked - trend not aligned for {symbol} after {exit_reason}")
                    del self.exit_continuation_pending[symbol]
                    continue
                
                signal_direction = "BULLISH" if direction == "buy" else "BEARISH"
                if alignment['direction'] != signal_direction:
                    self.logger.info(f"ERROR: Exit continuation blocked - direction mismatch for {symbol}")
                    del self.exit_continuation_pending[symbol]
                    continue
                
                # Execute Exit continuation re-entry
                self.logger.info(f"TRIGGERED: Exit Continuation Re-Entry Triggered: {symbol} @ {current_price} after {exit_reason}")
                
                # Create new chain for exit continuation
                from src.models import Alert
                entry_signal = Alert(
                    symbol=symbol,
                    tf=pending.get('timeframe', '15M'),
                    signal='buy' if direction == 'buy' else 'sell',
                    type='entry',
                    price=current_price
                )
                
                # Execute via trading engine
                await self.trading_engine.process_alert(entry_signal)
                
                # Remove from pending
                del self.exit_continuation_pending[symbol]
                
                self.logger.info(f"SUCCESS: Exit continuation re-entry executed for {symbol}")
    
    async def _execute_sl_hunt_reentry(self, symbol: str, direction: str, 
                                       price: float, chain_id: str, logic: str):
        """Execute automatic SL hunt re-entry"""
        
        # Get chain info
        chain = self.reentry_manager.active_chains.get(chain_id)
        if not chain or chain.current_level >= chain.max_level:
            return
        
        # Calculate new SL with reduction
        reduction_per_level = self.config["re_entry_config"]["sl_reduction_per_level"]
        sl_adjustment = (1 - reduction_per_level) ** chain.current_level
        
        account_balance = self.mt5_client.get_account_balance()
        lot_size = self.trading_engine.risk_manager.get_fixed_lot_size(account_balance)
        
        # Calculate SL and TP
        sl_price, sl_distance = self.pip_calculator.calculate_sl_price(
            symbol, price, direction, lot_size, account_balance, sl_adjustment
        )
        
        tp_price = self.pip_calculator.calculate_tp_price(
            price, sl_price, direction, self.config["rr_ratio"]
        )
        
        # Create trade
        trade = Trade(
            symbol=symbol,
            entry=price,
            sl=sl_price,
            tp=tp_price,
            lot_size=lot_size,
            direction=direction,
            strategy=logic,
            open_time=datetime.now().isoformat(),
            chain_id=chain_id,
            chain_level=chain.current_level + 1,
            is_re_entry=True
        )
        
        # Place order
        if not self.config["simulate_orders"]:
            trade_id = self.mt5_client.place_order(
                symbol=symbol,
                order_type=direction,
                lot_size=lot_size,
                price=price,
                sl=sl_price,
                tp=tp_price,
                comment=f"{logic}_SL_HUNT_REENTRY"
            )
            if trade_id:
                trade.trade_id = trade_id
        
        # Update chain
        self.reentry_manager.update_chain_level(chain_id, trade.trade_id)
        
        # Add to open trades
        self.trading_engine.open_trades.append(trade)
        self.trading_engine.risk_manager.add_open_trade(trade)
        
        # Send Telegram notification
        sl_reduction_percent = (1 - sl_adjustment) * 100
        self.trading_engine.telegram_bot.send_message(
            f"🔄 SL HUNT RE-ENTRY #{chain.current_level + 1}\n"
            f"Strategy: {logic}\n"
            f"Symbol: {symbol}\n"
            f"Direction: {direction.upper()}\n"
            f"Entry: {price:.5f}\n"
            f"SL: {sl_price:.5f} (-{sl_reduction_percent:.0f}% reduction)\n"
            f"TP: {tp_price:.5f}\n"
            f"Lots: {lot_size:.2f}\n"
            f"Chain: {chain_id}\n"
            f"Level: {chain.current_level + 1}/{chain.max_level}"
        )
    
    async def _execute_tp_continuation_reentry(self, symbol: str, direction: str,
                                               price: float, chain_id: str, logic: str):
        """Execute automatic TP continuation re-entry"""
        
        # Get chain info
        chain = self.reentry_manager.active_chains.get(chain_id)
        if not chain or chain.current_level >= chain.max_level:
            return
        
        # Calculate new SL with reduction
        reduction_per_level = self.config["re_entry_config"]["sl_reduction_per_level"]
        sl_adjustment = (1 - reduction_per_level) ** chain.current_level
        
        account_balance = self.mt5_client.get_account_balance()
        lot_size = self.trading_engine.risk_manager.get_fixed_lot_size(account_balance)
        
        # Calculate SL and TP
        sl_price, sl_distance = self.pip_calculator.calculate_sl_price(
            symbol, price, direction, lot_size, account_balance, sl_adjustment
        )
        
        tp_price = self.pip_calculator.calculate_tp_price(
            price, sl_price, direction, self.config["rr_ratio"]
        )
        
        # Create trade
        trade = Trade(
            symbol=symbol,
            entry=price,
            sl=sl_price,
            tp=tp_price,
            lot_size=lot_size,
            direction=direction,
            strategy=logic,
            open_time=datetime.now().isoformat(),
            chain_id=chain_id,
            chain_level=chain.current_level + 1,
            is_re_entry=True
        )
        
        # Place order
        if not self.config["simulate_orders"]:
            trade_id = self.mt5_client.place_order(
                symbol=symbol,
                order_type=direction,
                lot_size=lot_size,
                price=price,
                sl=sl_price,
                tp=tp_price,
                comment=f"{logic}_TP{chain.current_level}_REENTRY"
            )
            if trade_id:
                trade.trade_id = trade_id
        
        # Update chain
        self.reentry_manager.update_chain_level(chain_id, trade.trade_id)
        
        # Add to open trades
        self.trading_engine.open_trades.append(trade)
        self.trading_engine.risk_manager.add_open_trade(trade)
        
        # Save to database
        tp_level = chain.current_level + 1
        self.trading_engine.db.conn.cursor().execute('''
            INSERT INTO tp_reentry_events VALUES (?,?,?,?,?,?,?,?,?)
        ''', (None, chain_id, symbol, tp_level, chain.total_profit, price, 
              (1-sl_adjustment)*100, 0, datetime.now().isoformat()))
        self.trading_engine.db.conn.commit()
        
        # Send Telegram notification
        sl_reduction_percent = (1 - sl_adjustment) * 100
        self.trading_engine.telegram_bot.send_message(
            f"✅ TP{tp_level} RE-ENTRY\n"
            f"Strategy: {logic}\n"
            f"Symbol: {symbol}\n"
            f"Direction: {direction.upper()}\n"
            f"Entry: {price:.5f}\n"
            f"SL: {sl_price:.5f} (-{sl_reduction_percent:.0f}% reduction)\n"
            f"TP: {tp_price:.5f}\n"
            f"Lots: {lot_size:.2f}\n"
            f"Chain Profit: ${chain.total_profit:.2f}\n"
            f"Level: {tp_level}/{chain.max_level}"
        )
    
    def _get_current_price(self, symbol: str, direction: str) -> Optional[float]:
        """Get current price from MT5 (or simulation)"""
        try:
            if self.config.get("simulate_orders", True):
                # Simulation mode - return None or mock price
                return None
            
            import MetaTrader5 as mt5
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                return tick.ask if direction == 'buy' else tick.bid
            return None
        except:
            return None
    
    def register_sl_hunt(self, trade: Trade, logic: str):
        """Register a trade for SL hunt monitoring"""
        
        symbol_config = self.config["symbol_config"][trade.symbol]
        offset_pips = self.config["re_entry_config"]["sl_hunt_offset_pips"]
        pip_size = symbol_config["pip_size"]
        
        # Calculate target price (SL + offset)
        if trade.direction == 'buy':
            target_price = trade.sl + (offset_pips * pip_size)
        else:
            target_price = trade.sl - (offset_pips * pip_size)
        
        self.sl_hunt_pending[trade.symbol] = {
            'target_price': target_price,
            'direction': trade.direction,
            'chain_id': trade.chain_id,
            'sl_price': trade.sl,
            'logic': logic
        }
        
        self.monitored_symbols.add(trade.symbol)
        self.logger.info(f"REGISTERED: SL Hunt monitoring registered: {trade.symbol} @ {target_price:.5f}")
    
    def register_tp_continuation(self, trade: Trade, tp_price: float, logic: str):
        """Register a trade for TP continuation monitoring"""
        
        self.tp_continuation_pending[trade.symbol] = {
            'tp_price': tp_price,
            'direction': trade.direction,
            'chain_id': trade.chain_id,
            'logic': logic
        }
        
        self.monitored_symbols.add(trade.symbol)
        self.logger.info(f"REGISTERED: TP continuation monitoring registered: {trade.symbol} after TP @ {tp_price:.5f}")
    
    def stop_tp_continuation(self, symbol: str, reason: str = "Opposite signal received"):
        """Stop TP continuation monitoring for a symbol"""
        if symbol in self.tp_continuation_pending:
            del self.tp_continuation_pending[symbol]
            self.logger.info(f"STOPPED: TP continuation stopped for {symbol}: {reason}")
    
    def register_exit_continuation(self, trade: Trade, exit_price: float, exit_reason: str, logic: str, timeframe: str = '15M'):
        """
        Register continuation monitoring after Exit Appeared/Reversal exit
        Bot will monitor for re-entry with price gap after exit signal
        """
        
        self.exit_continuation_pending[trade.symbol] = {
            'exit_price': exit_price,
            'direction': trade.direction,
            'logic': logic,
            'exit_reason': exit_reason,
            'timeframe': timeframe
        }
        
        self.monitored_symbols.add(trade.symbol)
        self.logger.info(f"REGISTERED: Exit continuation monitoring registered: {trade.symbol} after {exit_reason} @ {exit_price:.5f}")
    
    def stop_exit_continuation(self, symbol: str, reason: str = "Alignment lost"):
        """Stop exit continuation monitoring for a symbol"""
        if symbol in self.exit_continuation_pending:
            del self.exit_continuation_pending[symbol]
            self.logger.info(f"STOPPED: Exit continuation stopped for {symbol}: {reason}")
    
    async def _check_profit_booking_chains(self):
        """
        Check profit booking chains for profit target achievement
        Runs every 30 seconds to monitor combined PnL
        """
        # Check if profit booking enabled
        profit_config = self.config.get("profit_booking_config", {})
        if not profit_config.get("enabled", True):
            return
        
        # Get profit booking manager from trading engine
        profit_manager = getattr(self.trading_engine, 'profit_booking_manager', None)
        if not profit_manager or not profit_manager.is_enabled():
            return
        
        # Get all active profit chains
        active_chains = profit_manager.get_all_chains()
        if not active_chains:
            return
        
        # Get open trades from trading engine
        open_trades = getattr(self.trading_engine, 'open_trades', [])
        
        # Check each chain
        for chain_id, chain in active_chains.items():
            try:
                # Validate chain state
                if not profit_manager.validate_chain_state(chain, open_trades):
                    continue
                
                # Check if profit target reached
                if profit_manager.check_profit_targets(chain, open_trades):
                    # Execute profit booking
                    success = await profit_manager.execute_profit_booking(
                        chain, open_trades, self.trading_engine
                    )
                    
                    if success:
                        self.logger.info(
                            f"✅ Profit booking executed for chain {chain_id} "
                            f"at level {chain.current_level}"
                        )
                    else:
                        self.logger.warning(
                            f"⚠️ Profit booking failed for chain {chain_id}"
                        )
                
            except Exception as e:
                self.logger.error(
                    f"Error checking profit booking chain {chain_id}: {str(e)}"
                )
                import traceback
                traceback.print_exc()
