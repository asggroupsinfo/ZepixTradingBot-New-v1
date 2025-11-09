from typing import Dict, Any, List, Optional
from datetime import datetime
from src.models import Trade, ProfitBookingChain
from src.config import Config
from src.database import TradeDatabase
from src.clients.mt5_client import MT5Client
from src.utils.pip_calculator import PipCalculator
from src.managers.risk_manager import RiskManager
import uuid
import logging

class ProfitBookingManager:
    """
    Manages profit booking chains for pyramid compounding system
    - Level 0: 1 order → $10 profit target → Level 1
    - Level 1: 2 orders → $20 profit target → Level 2
    - Level 2: 4 orders → $40 profit target → Level 3
    - Level 3: 8 orders → $80 profit target → Level 4
    - Level 4: 16 orders → $160 profit target → Max level
    """
    
    def __init__(self, config: Config, mt5_client: MT5Client, 
                 pip_calculator: PipCalculator, risk_manager: RiskManager,
                 db: TradeDatabase):
        self.config = config
        self.mt5_client = mt5_client
        self.pip_calculator = pip_calculator
        self.risk_manager = risk_manager
        self.db = db
        
        # Active profit booking chains
        self.active_chains: Dict[str, ProfitBookingChain] = {}
        
        # Get configuration
        self.profit_config = config.get("profit_booking_config", {})
        self.enabled = self.profit_config.get("enabled", True)
        self.profit_targets = self.profit_config.get("profit_targets", [10, 20, 40, 80, 160])
        self.multipliers = self.profit_config.get("multipliers", [1, 2, 4, 8, 16])
        self.sl_reductions = self.profit_config.get("sl_reductions", [0, 10, 25, 40, 50])
        self.max_level = self.profit_config.get("max_level", 4)
        
        self.logger = logging.getLogger(__name__)
    
    def is_enabled(self) -> bool:
        """Check if profit booking system is enabled"""
        return self.enabled
    
    def create_profit_chain(self, trade: Trade) -> Optional[ProfitBookingChain]:
        """
        Create a new profit booking chain from Order B (PROFIT_TRAIL)
        Returns chain if created successfully, None otherwise
        """
        if not self.is_enabled():
            return None
        
        if trade.order_type != "PROFIT_TRAIL":
            return None  # Only create chains for Profit Trail orders
        
        try:
            chain_id = f"PROFIT_{trade.symbol}_{uuid.uuid4().hex[:8]}"
            
            chain = ProfitBookingChain(
                chain_id=chain_id,
                symbol=trade.symbol,
                direction=trade.direction,
                base_lot=trade.lot_size,
                current_level=0,
                max_level=self.max_level,
                total_profit=0.0,
                active_orders=[trade.trade_id] if trade.trade_id else [],
                status="ACTIVE",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                profit_targets=self.profit_targets.copy(),
                multipliers=self.multipliers.copy(),
                sl_reductions=self.sl_reductions.copy(),
                metadata={
                    "strategy": trade.strategy,
                    "original_entry": trade.entry,
                    "original_sl": trade.sl,
                    "original_tp": trade.tp
                }
            )
            
            self.active_chains[chain_id] = chain
            trade.profit_chain_id = chain_id
            trade.profit_level = 0
            
            # Save to database
            self.db.save_profit_chain(chain)
            
            if trade.trade_id:
                self.db.save_profit_booking_order(
                    str(trade.trade_id),
                    chain_id,
                    0,
                    self.profit_targets[0],
                    int(self.sl_reductions[0]),
                    "OPEN"
                )
            
            self.logger.info(f"SUCCESS: Profit booking chain created: {chain_id} for {trade.symbol}")
            return chain
            
        except Exception as e:
            self.logger.error(f"Error creating profit chain: {str(e)}")
            return None
    
    def get_profit_target(self, level: int) -> float:
        """Get profit target for a specific level"""
        if 0 <= level < len(self.profit_targets):
            return self.profit_targets[level]
        return 0.0
    
    def get_order_multiplier(self, level: int) -> int:
        """Get order multiplier for a specific level"""
        if 0 <= level < len(self.multipliers):
            return self.multipliers[level]
        return 1
    
    def get_sl_reduction(self, level: int) -> float:
        """Get SL reduction percentage for a specific level"""
        if 0 <= level < len(self.sl_reductions):
            return self.sl_reductions[level]
        return 0.0
    
    def calculate_combined_pnl(self, chain: ProfitBookingChain, 
                               open_trades: List[Trade]) -> float:
        """
        Calculate combined unrealized PnL for all orders in current level
        Returns total PnL in dollars
        """
        try:
            # Get all trades for this chain at current level
            chain_trades = [
                t for t in open_trades
                if t.profit_chain_id == chain.chain_id 
                and t.profit_level == chain.current_level
                and t.status == "open"
            ]
            
            if not chain_trades:
                return 0.0
            
            # Get current price
            current_price = self.mt5_client.get_current_price(chain.symbol)
            if current_price == 0:
                return 0.0
            
            # Calculate PnL for each trade and sum
            total_pnl = 0.0
            
            for trade in chain_trades:
                symbol_config = self.config["symbol_config"][trade.symbol]
                pip_size = symbol_config["pip_size"]
                pip_value_per_std_lot = symbol_config["pip_value_per_std_lot"]
                
                # Calculate price difference in pips
                if trade.direction == "buy":
                    price_diff = current_price - trade.entry
                else:
                    price_diff = trade.entry - current_price
                
                pips_moved = price_diff / pip_size
                
                # Calculate PnL: pips × pip_value × lot_size
                pip_value = pip_value_per_std_lot * trade.lot_size
                trade_pnl = pips_moved * pip_value
                
                total_pnl += trade_pnl
            
            return total_pnl
            
        except Exception as e:
            self.logger.error(f"Error calculating combined PnL: {str(e)}")
            return 0.0
    
    def check_profit_targets(self, chain: ProfitBookingChain, 
                            open_trades: List[Trade]) -> bool:
        """
        Check if profit target is reached for current level
        Returns True if target reached, False otherwise
        """
        if chain.status != "ACTIVE":
            return False
        
        if chain.current_level >= chain.max_level:
            return False
        
        # Calculate combined PnL for current level
        combined_pnl = self.calculate_combined_pnl(chain, open_trades)
        
        # Get profit target for current level
        profit_target = self.get_profit_target(chain.current_level)
        
        if combined_pnl >= profit_target:
            self.logger.info(
                f"✅ Profit target reached: Chain {chain.chain_id} "
                f"Level {chain.current_level} - ${combined_pnl:.2f} >= ${profit_target}"
            )
            return True
        
        return False
    
    async def execute_profit_booking(self, chain: ProfitBookingChain, 
                                    open_trades: List[Trade],
                                    trading_engine) -> bool:
        """
        Execute profit booking: close current level orders and place next level orders
        Returns True if successful, False otherwise
        """
        try:
            if chain.status != "ACTIVE":
                return False
            
            if chain.current_level >= chain.max_level:
                # Max level reached - complete chain
                chain.status = "COMPLETED"
                chain.updated_at = datetime.now().isoformat()
                self.db.save_profit_chain(chain)
                self.logger.info(f"SUCCESS: Chain {chain.chain_id} completed - max level reached")
                return True
            
            # Get all trades for current level
            current_level_trades = [
                t for t in open_trades
                if t.profit_chain_id == chain.chain_id 
                and t.profit_level == chain.current_level
                and t.status == "open"
            ]
            
            if not current_level_trades:
                self.logger.warning(f"No open trades found for chain {chain.chain_id} level {chain.current_level}")
                return False
            
            # Calculate profit booked (combined PnL)
            profit_booked = self.calculate_combined_pnl(chain, open_trades)
            
            # Close all orders in current level
            orders_closed = 0
            for trade in current_level_trades:
                current_price = self.mt5_client.get_current_price(trade.symbol)
                if current_price > 0:
                    await trading_engine.close_trade(trade, "PROFIT_BOOKING", current_price)
                    orders_closed += 1
            
            # Update chain profit
            chain.total_profit += profit_booked
            
            # Progress to next level
            next_level = chain.current_level + 1
            next_order_count = self.get_order_multiplier(next_level)
            next_profit_target = self.get_profit_target(next_level)
            next_sl_reduction = self.get_sl_reduction(next_level)
            
            # Place new orders for next level
            orders_placed = 0
            account_balance = self.mt5_client.get_account_balance()
            lot_size = self.risk_manager.get_fixed_lot_size(account_balance)
            
            # Get current price
            current_price = self.mt5_client.get_current_price(chain.symbol)
            if current_price == 0:
                self.logger.error(f"Failed to get current price for {chain.symbol}")
                return False
            
            # Calculate SL with reduction for next level
            sl_adjustment = 1.0 - (next_sl_reduction / 100.0)
            sl_price, sl_distance = self.pip_calculator.calculate_sl_price(
                chain.symbol, current_price, chain.direction, 
                lot_size, account_balance, sl_adjustment
            )
            
            tp_price = self.pip_calculator.calculate_tp_price(
                current_price, sl_price, chain.direction, self.config.get("rr_ratio", 1.0)
            )
            
            # Place multiple orders for next level
            new_trade_ids = []
            for i in range(next_order_count):
                # Create trade object
                new_trade = Trade(
                    symbol=chain.symbol,
                    entry=current_price,
                    sl=sl_price,
                    tp=tp_price,
                    lot_size=lot_size,
                    direction=chain.direction,
                    strategy=chain.metadata.get("strategy", "LOGIC1"),
                    open_time=datetime.now().isoformat(),
                    original_entry=chain.metadata.get("original_entry", current_price),
                    original_sl_distance=sl_distance,
                    order_type="PROFIT_TRAIL",
                    profit_chain_id=chain.chain_id,
                    profit_level=next_level
                )
                
                # Place order
                if not self.config.get("simulate_orders", False):
                    trade_id = self.mt5_client.place_order(
                        symbol=chain.symbol,
                        order_type=chain.direction,
                        lot_size=lot_size,
                        price=current_price,
                        sl=sl_price,
                        tp=tp_price,
                        comment=f"{chain.metadata.get('strategy', 'LOGIC1')}_PROFIT_L{next_level}"
                    )
                    if trade_id:
                        new_trade.trade_id = trade_id
                        new_trade_ids.append(trade_id)
                else:
                    # Simulation mode
                    import random
                    trade_id = random.randint(100000, 999999)
                    new_trade.trade_id = trade_id
                    new_trade_ids.append(trade_id)
                
                # Add to open trades
                trading_engine.open_trades.append(new_trade)
                trading_engine.risk_manager.add_open_trade(new_trade)
                
                # Save to database
                if new_trade.trade_id:
                    self.db.save_profit_booking_order(
                        str(new_trade.trade_id),
                        chain.chain_id,
                        next_level,
                        next_profit_target,
                        int(next_sl_reduction),
                        "OPEN"
                    )
                
                orders_placed += 1
            
            # Update chain
            chain.current_level = next_level
            chain.active_orders = new_trade_ids
            chain.updated_at = datetime.now().isoformat()
            self.db.save_profit_chain(chain)
            
            # Save profit booking event
            self.db.save_profit_booking_event(
                chain.chain_id,
                chain.current_level - 1,  # Previous level
                profit_booked,
                orders_closed,
                orders_placed
            )
            
            # Send Telegram notification
            trading_engine.telegram_bot.send_message(
                f"🔁 PROFIT BOOKING LEVEL UP!\n"
                f"Chain: {chain.chain_id}\n"
                f"Level: {chain.current_level - 1} → {chain.current_level}\n"
                f"Profit Booked: ${profit_booked:.2f}\n"
                f"Orders Closed: {orders_closed}\n"
                f"Orders Placed: {orders_placed}\n"
                f"Next Target: ${next_profit_target}\n"
                f"SL Reduction: {next_sl_reduction}%"
            )
            
            self.logger.info(
                f"✅ Profit booking executed: Chain {chain.chain_id} "
                f"Level {chain.current_level - 1} → {chain.current_level}, "
                f"Profit: ${profit_booked:.2f}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing profit booking: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop_chain(self, chain_id: str, reason: str = "Manual stop"):
        """Stop a profit booking chain"""
        if chain_id in self.active_chains:
            chain = self.active_chains[chain_id]
            chain.status = "STOPPED"
            chain.updated_at = datetime.now().isoformat()
            self.db.save_profit_chain(chain)
            self.logger.info(f"STOPPED: Chain {chain_id} stopped: {reason}")
    
    def stop_all_chains(self, reason: str = "Manual stop all"):
        """Stop all active profit booking chains"""
        for chain_id in list(self.active_chains.keys()):
            self.stop_chain(chain_id, reason)
    
    def recover_chains_from_database(self, open_trades: List[Trade]):
        """
        Recover active profit booking chains from database on bot restart
        """
        try:
            active_chains_data = self.db.get_active_profit_chains()
            
            for chain_data in active_chains_data:
                try:
                    chain = ProfitBookingChain(
                        chain_id=chain_data["chain_id"],
                        symbol=chain_data["symbol"],
                        direction=chain_data["direction"],
                        base_lot=chain_data["base_lot"],
                        current_level=chain_data["current_level"],
                        max_level=self.max_level,
                        total_profit=chain_data.get("total_profit", 0.0),
                        active_orders=[],  # Will be populated from open_trades
                        status=chain_data.get("status", "ACTIVE"),
                        created_at=chain_data.get("created_at", datetime.now().isoformat()),
                        updated_at=chain_data.get("updated_at", datetime.now().isoformat()),
                        profit_targets=self.profit_targets.copy(),
                        multipliers=self.multipliers.copy(),
                        sl_reductions=self.sl_reductions.copy(),
                        metadata={}
                    )
                    
                    # Find active orders for this chain
                    chain_orders = [
                        t.trade_id for t in open_trades
                        if t.profit_chain_id == chain.chain_id
                        and t.status == "open"
                    ]
                    chain.active_orders = chain_orders
                    
                    self.active_chains[chain.chain_id] = chain
                    self.logger.info(f"SUCCESS: Recovered chain: {chain.chain_id} with {len(chain_orders)} orders")
                    
                except Exception as e:
                    self.logger.error(f"Error recovering chain {chain_data.get('chain_id', 'unknown')}: {str(e)}")
            
            self.logger.info(f"SUCCESS: Recovered {len(self.active_chains)} profit booking chains from database")
            
        except Exception as e:
            self.logger.error(f"Error recovering chains from database: {str(e)}")
    
    def get_chain(self, chain_id: str) -> Optional[ProfitBookingChain]:
        """Get profit booking chain by ID"""
        return self.active_chains.get(chain_id)
    
    def get_all_chains(self) -> Dict[str, ProfitBookingChain]:
        """Get all active profit booking chains"""
        return self.active_chains.copy()
    
    def validate_chain_state(self, chain: ProfitBookingChain, 
                            open_trades: List[Trade]) -> bool:
        """
        Validate chain state integrity
        Returns True if valid, False otherwise
        """
        try:
            # Check if chain exists
            if chain.chain_id not in self.active_chains:
                return False
            
            # Check if all active orders still exist
            for order_id in chain.active_orders:
                order_exists = any(
                    t.trade_id == order_id and t.status == "open"
                    for t in open_trades
                )
                if not order_exists:
                    self.logger.warning(
                        f"Chain {chain.chain_id} has missing order: {order_id}"
                    )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating chain state: {str(e)}")
            return False
    
    def handle_orphaned_orders(self, open_trades: List[Trade]):
        """
        Handle orders that have profit_chain_id but chain doesn't exist
        """
        try:
            for trade in open_trades:
                if trade.profit_chain_id and trade.profit_chain_id not in self.active_chains:
                    # Orphaned order - clear profit_chain_id
                    trade.profit_chain_id = None
                    trade.profit_level = 0
                    self.logger.warning(
                        f"Cleared orphaned order: {trade.trade_id} "
                        f"from missing chain: {trade.profit_chain_id}"
                    )
        except Exception as e:
            self.logger.error(f"Error handling orphaned orders: {str(e)}")

