from datetime import datetime
from typing import Dict, Any, Optional
from src.models import Trade, Alert
from src.config import Config
import logging

class ReversalExitHandler:
    """
    Handle reversal exit signals for immediate profit booking
    Accepts:
    1. Reversal alerts (type: 'reversal', signal: 'reversal_bull/bear')
    2. Opposite entry signals (if BUY trade open, SELL entry = exit)
    3. Trend reversal alerts (type: 'trend', opposite direction)
    4. Exit Appeared alerts (type: 'exit', early warning)
    """
    
    def __init__(self, config: Config, mt5_client, telegram_bot, db, price_monitor=None):
        self.config = config
        self.mt5_client = mt5_client
        self.telegram_bot = telegram_bot
        self.db = db
        self.price_monitor = price_monitor
        self.logger = logging.getLogger(__name__)
    
    async def check_reversal_exit(self, alert: Alert, open_trades: list) -> list:
        """
        Check if alert triggers reversal exit for any open trade
        Returns list of trades to close
        """
        if not self.config["re_entry_config"]["reversal_exit_enabled"]:
            return []
        
        trades_to_close = []
        
        for trade in open_trades:
            if trade.symbol != alert.symbol:
                continue
            
            should_exit = False
            exit_reason = ""
            
            # Case 1: Explicit reversal alert
            if alert.type == 'reversal':
                # Reversal bull = close sell trades
                # Reversal bear = close buy trades
                if alert.signal == 'reversal_bull' and trade.direction == 'sell':
                    should_exit = True
                    exit_reason = "REVERSAL_BULLISH"
                elif alert.signal == 'reversal_bear' and trade.direction == 'buy':
                    should_exit = True
                    exit_reason = "REVERSAL_BEARISH"
            
            # Case 2: Opposite entry signal
            elif alert.type == 'entry':
                if alert.signal == 'buy' and trade.direction == 'sell':
                    should_exit = True
                    exit_reason = "OPPOSITE_SIGNAL_BUY"
                elif alert.signal == 'sell' and trade.direction == 'buy':
                    should_exit = True
                    exit_reason = "OPPOSITE_SIGNAL_SELL"
            
            # Case 3: Trend reversal alert (type: 'trend', opposite direction)
            elif alert.type == 'trend':
                trend_direction = "BULLISH" if alert.signal == 'bull' else "BEARISH"
                trade_direction = "BULLISH" if trade.direction == 'buy' else "BEARISH"
                
                if trend_direction != trade_direction:
                    should_exit = True
                    exit_reason = f"TREND_REVERSAL_{trend_direction}"
            
            # Case 4: Exit Appeared alert (Early warning before reversal)
            elif alert.type == 'exit':
                if alert.signal == 'bull' and trade.direction == 'sell':
                    should_exit = True
                    exit_reason = "EXIT_APPEARED_BULLISH"
                elif alert.signal == 'bear' and trade.direction == 'buy':
                    should_exit = True
                    exit_reason = "EXIT_APPEARED_BEARISH"
            
            if should_exit:
                trades_to_close.append({
                    'trade': trade,
                    'exit_price': alert.price,
                    'exit_reason': exit_reason
                })
                
                # If trade is part of profit booking chain, stop the entire chain
                if hasattr(trade, 'profit_chain_id') and trade.profit_chain_id:
                    # Mark chain for stopping - will be handled in execute_reversal_exit
                    pass
        
        return trades_to_close
    
    async def execute_reversal_exit(self, trade: Trade, exit_price: float, exit_reason: str):
        """Execute immediate profit booking on reversal signal"""
        
        # If trade is part of profit booking chain, stop the entire chain
        if hasattr(trade, 'profit_chain_id') and trade.profit_chain_id:
            # Get trading engine from price_monitor if available
            trading_engine = None
            if self.price_monitor:
                trading_engine = getattr(self.price_monitor, 'trading_engine', None)
            
            if trading_engine:
                profit_manager = getattr(trading_engine, 'profit_booking_manager', None)
                if profit_manager:
                    # Stop the entire profit booking chain
                    profit_manager.stop_chain(trade.profit_chain_id, f"Exit signal: {exit_reason}")
                    
                    # Close all orders in the chain
                    open_trades = getattr(trading_engine, 'open_trades', [])
                    chain_orders = [
                        t for t in open_trades
                        if hasattr(t, 'profit_chain_id') and t.profit_chain_id == trade.profit_chain_id
                        and t.status == "open"
                    ]
                    
                    for chain_trade in chain_orders:
                        if chain_trade.trade_id != trade.trade_id:  # Don't close twice
                            await trading_engine.close_trade(chain_trade, f"CHAIN_STOPPED_{exit_reason}", exit_price)
                    
                    self.logger.info(f"STOPPED: Stopped profit booking chain {trade.profit_chain_id} due to exit signal: {exit_reason}")
        
        # Close position in MT5
        if not self.config.get("simulate_orders", True):
            success = self.mt5_client.close_position(trade.trade_id)
            if not success:
                self.logger.error(f"Failed to close position {trade.trade_id}")
                return False
        
        # Calculate PnL
        if trade.direction == 'buy':
            pnl = (exit_price - trade.entry) * trade.lot_size * 10000
        else:
            pnl = (trade.entry - exit_price) * trade.lot_size * 10000
        
        # Apply symbol-specific pip value
        symbol_config = self.config["symbol_config"][trade.symbol]
        if symbol_config.get("is_gold", False):
            pnl = pnl * 100  # Gold multiplier
        
        # Update trade
        trade.close_time = datetime.now().isoformat()
        trade.pnl = pnl
        trade.status = "closed"
        
        # Save to database
        self.db.save_trade(trade)
        
        # Save reversal exit event
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO reversal_exit_events VALUES (?,?,?,?,?,?,?)
        ''', (None, trade.trade_id, trade.symbol, exit_price, 
              exit_reason, pnl, datetime.now().isoformat()))
        self.db.conn.commit()
        
        # Send Telegram notification
        profit_emoji = "✅" if pnl >= 0 else "❌"
        self.telegram_bot.send_message(
            f"{profit_emoji} REVERSAL EXIT\n"
            f"Reason: {exit_reason}\n"
            f"Symbol: {trade.symbol}\n"
            f"Entry: {trade.entry:.5f}\n"
            f"Exit: {exit_price:.5f}\n"
            f"Direction: {trade.direction.upper()}\n"
            f"PnL: ${pnl:.2f}\n"
            f"Strategy: {trade.strategy}"
        )
        
        # Register continuation monitoring (NEW FEATURE)
        # After Exit Appeared/Reversal exit, continue monitoring for re-entry with price gap
        if self.price_monitor and self.config["re_entry_config"].get("exit_continuation_enabled", True):
            # Only register for specific exit reasons
            if any(reason in exit_reason for reason in ['EXIT_APPEARED', 'TREND_REVERSAL', 'REVERSAL_', 'OPPOSITE_SIGNAL']):
                self.price_monitor.register_exit_continuation(
                    trade=trade,
                    exit_price=exit_price,
                    exit_reason=exit_reason,
                    logic=trade.strategy,
                    timeframe='15M'  # Default timeframe
                )
        
        self.logger.info(f"SUCCESS: Reversal exit executed: {trade.symbol} PnL ${pnl:.2f}")
        return True
    
    def get_reversal_exit_stats(self) -> Dict[str, Any]:
        """Get statistics for reversal exits"""
        cursor = self.db.conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_reversal_exits,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as profitable_exits,
                SUM(pnl) as total_reversal_pnl,
                AVG(pnl) as avg_reversal_pnl
            FROM reversal_exit_events
            WHERE timestamp >= datetime('now', '-30 days')
        ''')
        
        result = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        
        return dict(zip(columns, result)) if result else {}
