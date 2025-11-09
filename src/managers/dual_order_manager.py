from typing import Dict, Any, List, Tuple, Optional
from src.models import Trade, Alert
from src.config import Config
from src.managers.risk_manager import RiskManager
from src.clients.mt5_client import MT5Client
from src.utils.pip_calculator import PipCalculator
from datetime import datetime
import logging

class DualOrderManager:
    """
    Manages dual order placement system
    - Order A: TP Continuation Trail (existing system)
    - Order B: Profit Booking Trail (new pyramid system)
    - Both orders use SAME lot size (no split)
    - Orders work independently (no rollback if one fails)
    """
    
    def __init__(self, config: Config, risk_manager: RiskManager, 
                 mt5_client: MT5Client, pip_calculator: PipCalculator):
        self.config = config
        self.risk_manager = risk_manager
        self.mt5_client = mt5_client
        self.pip_calculator = pip_calculator
        self.logger = logging.getLogger(__name__)
    
    def is_enabled(self) -> bool:
        """Check if dual order system is enabled"""
        return self.config.get("dual_order_config", {}).get("enabled", True)
    
    def validate_dual_order_risk(self, symbol: str, lot_size: float, 
                                account_balance: float) -> Dict[str, Any]:
        """
        Validate if account can handle 2x lot size risk
        Returns: {"valid": bool, "reason": str}
        """
        if not self.is_enabled():
            return {"valid": True, "reason": "Dual orders disabled"}
        
        # Calculate risk for 2x lot size
        symbol_config = self.config["symbol_config"][symbol]
        account_tier = self.risk_manager.get_risk_tier(account_balance)
        
        # Get SL pips from dual SL system
        sl_pips = self.pip_calculator._get_sl_from_dual_system(symbol, account_balance)
        
        # Calculate pip value for 2x lot size
        pip_value_std = symbol_config["pip_value_per_std_lot"]
        pip_value = pip_value_std * (lot_size * 2)  # 2x lot size
        
        # Calculate expected loss for 2 orders
        expected_loss = sl_pips * pip_value
        
        # Get risk tier limits
        if account_tier not in self.config["risk_tiers"]:
            return {"valid": False, "reason": f"Invalid risk tier: {account_tier}"}
        
        risk_params = self.config["risk_tiers"][account_tier]
        
        # Check daily loss cap
        daily_loss = self.risk_manager.daily_loss
        if daily_loss + expected_loss > risk_params["daily_loss_limit"]:
            return {
                "valid": False,
                "reason": f"Daily loss cap exceeded: ${daily_loss + expected_loss:.2f} > ${risk_params['daily_loss_limit']}"
            }
        
        # Check lifetime loss cap
        lifetime_loss = self.risk_manager.lifetime_loss
        if lifetime_loss + expected_loss > risk_params["max_total_loss"]:
            return {
                "valid": False,
                "reason": f"Lifetime loss cap exceeded: ${lifetime_loss + expected_loss:.2f} > ${risk_params['max_total_loss']}"
            }
        
        # Check account balance (basic check - ensure we have enough margin)
        # This is a simple check - MT5 will enforce actual margin requirements
        min_balance_required = account_balance * 0.1  # 10% of balance as margin
        if expected_loss > min_balance_required:
            return {
                "valid": False,
                "reason": f"Expected loss ${expected_loss:.2f} exceeds safe margin threshold"
            }
        
        return {"valid": True, "reason": "Risk validation passed"}
    
    def create_dual_orders(self, alert: Alert, strategy: str, 
                          account_balance: float) -> Dict[str, Any]:
        """
        Create Order A (TP Trail) and Order B (Profit Trail) with same lot size
        Returns: {
            "order_a": Trade object or None,
            "order_b": Trade object or None,
            "order_a_placed": bool,
            "order_b_placed": bool,
            "errors": List[str]
        }
        """
        result = {
            "order_a": None,
            "order_b": None,
            "order_a_placed": False,
            "order_b_placed": False,
            "errors": []
        }
        
        if not self.is_enabled():
            # If dual orders disabled, return empty result
            return result
        
        try:
            # Get lot size (same for both orders)
            lot_size = self.risk_manager.get_fixed_lot_size(account_balance)
            
            if lot_size <= 0:
                result["errors"].append("Invalid lot size")
                return result
            
            # Validate risk for 2x lot size
            risk_validation = self.validate_dual_order_risk(
                alert.symbol, lot_size, account_balance
            )
            
            if not risk_validation["valid"]:
                result["errors"].append(f"Risk validation failed: {risk_validation['reason']}")
                return result
            
            # Calculate SL and TP for both orders (same calculation)
            sl_price, sl_distance = self.pip_calculator.calculate_sl_price(
                alert.symbol, alert.price, alert.signal, lot_size, account_balance
            )
            
            tp_price = self.pip_calculator.calculate_tp_price(
                alert.price, sl_price, alert.signal, self.config.get("rr_ratio", 1.0)
            )
            
            # Create Order A (TP Trail)
            order_a = Trade(
                symbol=alert.symbol,
                entry=alert.price,
                sl=sl_price,
                tp=tp_price,
                lot_size=lot_size,
                direction=alert.signal,
                strategy=strategy,
                open_time=datetime.now().isoformat(),
                original_entry=alert.price,
                original_sl_distance=sl_distance,
                order_type="TP_TRAIL"
            )
            
            # Create Order B (Profit Trail)
            order_b = Trade(
                symbol=alert.symbol,
                entry=alert.price,
                sl=sl_price,
                tp=tp_price,
                lot_size=lot_size,  # Same lot size
                direction=alert.signal,
                strategy=strategy,
                open_time=datetime.now().isoformat(),
                original_entry=alert.price,
                original_sl_distance=sl_distance,
                order_type="PROFIT_TRAIL"
            )
            
            result["order_a"] = order_a
            result["order_b"] = order_b
            
            # Place Order A independently
            order_a_result = self._place_single_order(order_a, strategy, "TP_TRAIL")
            if order_a_result["success"]:
                result["order_a_placed"] = True
                order_a.trade_id = order_a_result["trade_id"]
            else:
                result["errors"].append(f"Order A failed: {order_a_result.get('error', 'Unknown error')}")
                # Order A failed - but we continue to try Order B (independent)
            
            # Place Order B independently (regardless of Order A result)
            order_b_result = self._place_single_order(order_b, strategy, "PROFIT_TRAIL")
            if order_b_result["success"]:
                result["order_b_placed"] = True
                order_b.trade_id = order_b_result["trade_id"]
            else:
                result["errors"].append(f"Order B failed: {order_b_result.get('error', 'Unknown error')}")
                # Order B failed - but Order A continues independently (no rollback)
            
            # Log results
            if result["order_a_placed"] and result["order_b_placed"]:
                self.logger.info(f"SUCCESS: Both orders placed: {alert.symbol} {alert.signal.upper()}")
            elif result["order_a_placed"]:
                self.logger.warning(f"WARNING: Only Order A placed: {alert.symbol} {alert.signal.upper()} (Order B failed)")
            elif result["order_b_placed"]:
                self.logger.warning(f"WARNING: Only Order B placed: {alert.symbol} {alert.signal.upper()} (Order A failed)")
            else:
                self.logger.error(f"ERROR: Both orders failed: {alert.symbol} {alert.signal.upper()}")
            
            return result
            
        except Exception as e:
            error_msg = f"Dual order creation error: {str(e)}"
            self.logger.error(error_msg)
            result["errors"].append(error_msg)
            return result
    
    def _place_single_order(self, trade: Trade, strategy: str, 
                           order_type: str) -> Dict[str, Any]:
        """
        Place a single order in MT5
        Returns: {"success": bool, "trade_id": Optional[int], "error": Optional[str]}
        """
        try:
            if self.config.get("simulate_orders", False):
                # Simulation mode
                import random
                trade_id = random.randint(100000, 999999)
                self.logger.info(f"SIMULATED: {order_type}: {trade.symbol} {trade.direction.upper()} @ {trade.entry}")
                return {"success": True, "trade_id": trade_id, "error": None}
            
            # Live trading mode
            trade_id = self.mt5_client.place_order(
                symbol=trade.symbol,
                order_type=trade.direction,
                lot_size=trade.lot_size,
                price=trade.entry,
                sl=trade.sl,
                tp=trade.tp,
                comment=f"{strategy}_{order_type}"
            )
            
            if trade_id:
                return {"success": True, "trade_id": trade_id, "error": None}
            else:
                return {"success": False, "trade_id": None, "error": "MT5 order placement failed"}
                
        except Exception as e:
            error_msg = f"Order placement error: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "trade_id": None, "error": error_msg}

