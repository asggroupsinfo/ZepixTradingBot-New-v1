import json
import os
from datetime import datetime, date
from typing import Dict, Any, List
from src.config import Config

class RiskManager:
    def __init__(self, config: Config):
        self.config = config
        self.stats_file = "data/stats.json"
        self.daily_loss = 0.0
        self.lifetime_loss = 0.0
        self.daily_profit = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.open_trades = []
        self.mt5_client = None
        self.load_stats()
        
    def load_stats(self):
        """Load statistics from file with error handling"""
        try:
            if os.path.exists(self.stats_file) and os.path.getsize(self.stats_file) > 0:
                with open(self.stats_file, 'r') as f:
                    stats = json.load(f)
                    
                if stats.get("date") != str(date.today()):
                    self.daily_loss = 0.0
                    self.daily_profit = 0.0
                else:
                    self.daily_loss = stats.get("daily_loss", 0.0)
                    self.daily_profit = stats.get("daily_profit", 0.0)
                    
                self.lifetime_loss = stats.get("lifetime_loss", 0.0)
                self.total_trades = stats.get("total_trades", 0)
                self.winning_trades = stats.get("winning_trades", 0)
            else:
                # Initialize with default values if file doesn't exist or is empty
                self.reset_daily_stats()
                
        except (json.JSONDecodeError, Exception) as e:
            print(f"WARNING: Stats file corrupted, resetting: {str(e)}")
            self.reset_daily_stats()
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.daily_loss = 0.0
        self.daily_profit = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.save_stats()
    
    def reset_lifetime_loss(self):
        """Reset lifetime loss counter"""
        self.lifetime_loss = 0.0
        self.save_stats()
    
    def reset_daily_loss(self):
        """Reset daily loss and profit counters (keeps lifetime loss)"""
        self.daily_loss = 0.0
        self.daily_profit = 0.0
        self.save_stats()
    
    def save_stats(self):
        """Save statistics to file"""
        stats = {
            "date": str(date.today()),
            "daily_loss": self.daily_loss,
            "daily_profit": self.daily_profit,
            "lifetime_loss": self.lifetime_loss,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades
        }
        
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(stats, f, indent=4)
        except Exception as e:
            print(f"ERROR: Error saving stats: {str(e)}")
    
    def get_fixed_lot_size(self, balance: float) -> float:
        """Get fixed lot size based on account balance"""
        
        # Manual overrides first
        manual_overrides = self.config.get("manual_lot_overrides", {})
        if str(int(balance)) in manual_overrides:
            return manual_overrides[str(int(balance))]
        
        # Then tier-based sizing
        fixed_lots = self.config["fixed_lot_sizes"]
        
        for tier_balance in sorted(fixed_lots.keys(), key=int, reverse=True):
            if balance >= int(tier_balance):
                return fixed_lots[tier_balance]
        
        return 0.05  # Default minimum
    
    def set_manual_lot_size(self, balance_tier: int, lot_size: float):
        """Manually override lot size for a balance tier"""
        
        if "manual_lot_overrides" not in self.config.config:
            self.config.config["manual_lot_overrides"] = {}
        
        self.config.config["manual_lot_overrides"][str(balance_tier)] = lot_size
        self.config.save_config()
    
    def get_risk_tier(self, balance: float) -> str:
        """Get risk tier based on account balance"""
        for tier in ["100000", "50000", "25000", "10000", "5000"]:
            if balance >= int(tier):
                return tier
        return "5000"
    
    def can_trade(self) -> bool:
        """Check if trading is allowed based on risk limits"""
        if not self.mt5_client:
            return False
            
        account_balance = self.mt5_client.get_account_balance()
        risk_tier = self.get_risk_tier(account_balance)
        
        if risk_tier not in self.config["risk_tiers"]:
            return False
            
        risk_params = self.config["risk_tiers"][risk_tier]
        
        # Check closed loss limits
        if self.lifetime_loss >= risk_params["max_total_loss"]:
            print(f"BLOCKED: Lifetime loss limit reached: ${self.lifetime_loss}")
            return False
            
        if self.daily_loss >= risk_params["daily_loss_limit"]:
            print(f"BLOCKED: Daily loss limit reached: ${self.daily_loss}")
            return False
        
        # Note: Dual order validation is done separately in validate_dual_orders()
        # This method checks basic trading permission
        
        return True
    
    def update_pnl(self, pnl: float):
        """Update PnL and risk statistics"""
        self.total_trades += 1
        
        if pnl > 0:
            self.daily_profit += pnl
            self.winning_trades += 1
        else:
            self.daily_loss += abs(pnl)
            self.lifetime_loss += abs(pnl)
        
        self.save_stats()
    
    def add_open_trade(self, trade):
        """Add trade to open trades list"""
        self.open_trades.append(trade)
    
    def remove_open_trade(self, trade):
        """Remove trade from open trades list"""
        self.open_trades = [t for t in self.open_trades 
                          if getattr(t, 'trade_id', None) != getattr(trade, 'trade_id', None)]
    
    def set_mt5_client(self, mt5_client):
        """Set MT5 client for balance checking"""
        self.mt5_client = mt5_client
    
    def validate_dual_orders(self, symbol: str, lot_size: float, 
                            account_balance: float) -> Dict[str, Any]:
        """
        Validate if account can handle 2x lot size risk for dual orders
        Returns: {"valid": bool, "reason": str}
        """
        # Check if dual orders enabled
        dual_config = self.config.get("dual_order_config", {})
        if not dual_config.get("enabled", True):
            return {"valid": True, "reason": "Dual orders disabled"}
        
        # Get risk tier
        risk_tier = self.get_risk_tier(account_balance)
        
        if risk_tier not in self.config["risk_tiers"]:
            return {"valid": False, "reason": f"Invalid risk tier: {risk_tier}"}
        
        risk_params = self.config["risk_tiers"][risk_tier]
        
        # Calculate expected loss for 2x lot size
        # Get symbol config
        symbol_config = self.config["symbol_config"][symbol]
        volatility = symbol_config["volatility"]
        
        # Get SL pips (approximate - actual calculation done in pip_calculator)
        # For validation, we use a conservative estimate
        pip_value_std = symbol_config.get("pip_value_per_std_lot", 10.0)
        pip_value = pip_value_std * (lot_size * 2)  # 2x lot size
        
        # Estimate SL pips (conservative - actual will be calculated by pip_calculator)
        # Use a reasonable estimate: 50 pips for LOW, 75 for MEDIUM, 100 for HIGH
        sl_estimates = {"LOW": 50, "MEDIUM": 75, "HIGH": 100}
        estimated_sl_pips = sl_estimates.get(volatility, 75)
        
        # Calculate expected loss for 2 orders
        expected_loss = estimated_sl_pips * pip_value
        
        # Check daily loss cap
        if self.daily_loss + expected_loss > risk_params["daily_loss_limit"]:
            return {
                "valid": False,
                "reason": f"Daily loss cap would be exceeded: ${self.daily_loss + expected_loss:.2f} > ${risk_params['daily_loss_limit']}"
            }
        
        # Check lifetime loss cap
        if self.lifetime_loss + expected_loss > risk_params["max_total_loss"]:
            return {
                "valid": False,
                "reason": f"Lifetime loss cap would be exceeded: ${self.lifetime_loss + expected_loss:.2f} > ${risk_params['max_total_loss']}"
            }
        
        return {"valid": True, "reason": "Dual order risk validation passed"}
    
    def calculate_profit_booking_risk(self, chain_level: int, base_lot: float, 
                                     symbol: str, account_balance: float) -> Dict[str, Any]:
        """
        Calculate risk for profit booking chain at specific level
        Returns: {"total_risk": float, "order_count": int, "total_lot_size": float}
        """
        # Get profit booking config
        profit_config = self.config.get("profit_booking_config", {})
        multipliers = profit_config.get("multipliers", [1, 2, 4, 8, 16])
        sl_reductions = profit_config.get("sl_reductions", [0, 10, 25, 40, 50])
        
        if chain_level >= len(multipliers):
            return {"total_risk": 0.0, "order_count": 0, "total_lot_size": 0.0}
        
        # Get order count for this level
        order_count = multipliers[chain_level]
        total_lot_size = base_lot * order_count
        
        # Get SL reduction for this level
        sl_reduction = sl_reductions[chain_level] if chain_level < len(sl_reductions) else 0
        sl_adjustment = 1.0 - (sl_reduction / 100.0)
        
        # Get symbol config
        symbol_config = self.config["symbol_config"][symbol]
        pip_value_std = symbol_config.get("pip_value_per_std_lot", 10.0)
        
        # Estimate SL pips (conservative estimate)
        volatility = symbol_config["volatility"]
        sl_estimates = {"LOW": 50, "MEDIUM": 75, "HIGH": 100}
        estimated_sl_pips = sl_estimates.get(volatility, 75) * sl_adjustment
        
        # Calculate total risk
        pip_value = pip_value_std * total_lot_size
        total_risk = estimated_sl_pips * pip_value
        
        return {
            "total_risk": total_risk,
            "order_count": order_count,
            "total_lot_size": total_lot_size,
            "sl_reduction_percent": sl_reduction
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        if not self.mt5_client:
            return {}
            
        account_balance = self.mt5_client.get_account_balance()
        risk_tier = self.get_risk_tier(account_balance)
        lot_size = self.get_fixed_lot_size(account_balance)
        
        if risk_tier not in self.config["risk_tiers"]:
            return {}
            
        risk_params = self.config["risk_tiers"][risk_tier]
        
        return {
            "daily_loss": self.daily_loss,
            "daily_profit": self.daily_profit,
            "lifetime_loss": self.lifetime_loss,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0,
            "current_risk_tier": risk_tier,
            "risk_parameters": risk_params,
            "current_lot_size": lot_size,
            "account_balance": account_balance
        }