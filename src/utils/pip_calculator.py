from typing import Dict, Tuple
from src.config import Config

class PipCalculator:
    """
    Accurate pip and SL calculation for all symbols
    Uses TradingView symbol names (XAUUSD) internally
    MT5Client handles the mapping to broker symbols (GOLD)
    """
    
    def __init__(self, config: Config):
        self.config = config
        
    def calculate_sl_price(self, symbol: str, entry_price: float, 
                          direction: str, lot_size: float, 
                          account_balance: float, sl_adjustment: float = 1.0) -> Tuple[float, float]:
        """
        Calculate SL price using dual SL system (sl-1 or sl-2)
        Symbol parameter uses TradingView naming (XAUUSD, not GOLD)
        Returns: (sl_price, sl_distance_in_price)
        
        sl_adjustment: Multiplier for SL (used in re-entry system, default 1.0)
        """
        
        # Get symbol configuration
        symbol_config = self.config["symbol_config"][symbol]
        pip_size = symbol_config["pip_size"]
        
        # Get SL in pips from dual SL system
        sl_pips = self._get_sl_from_dual_system(symbol, account_balance)
        
        # Apply SL adjustment (for re-entry progressive reduction)
        sl_pips = sl_pips * sl_adjustment
        
        # Convert pips to price distance
        sl_distance = sl_pips * pip_size
        
        # Calculate actual SL price based on direction
        if direction == "buy":
            sl_price = entry_price - sl_distance
        else:
            sl_price = entry_price + sl_distance
            
        return sl_price, sl_distance
    
    def _get_sl_from_dual_system(self, symbol: str, account_balance: float) -> float:
        """
        Get SL in pips from active dual SL system (sl-1 or sl-2)
        Applies symbol-specific reductions if configured
        """
        
        # Check if SL system is enabled
        if not self.config.get("sl_system_enabled", True):
            # Fallback to old risk-cap based calculation
            return self._fallback_sl_calculation(symbol, account_balance)
        
        # Get active system (sl-1 or sl-2)
        active_system = self.config.get("active_sl_system", "sl-1")
        
        # Get account tier
        account_tier = self._get_account_tier(account_balance)
        
        # Get SL pips from active system table
        try:
            sl_data = self.config["sl_systems"][active_system]["symbols"][symbol][account_tier]
            sl_pips = sl_data["sl_pips"]
        except KeyError:
            # Fallback if symbol/tier not found
            print(f"WARNING: SL not found for {symbol} @ {account_tier} in {active_system}, using fallback")
            return self._fallback_sl_calculation(symbol, account_balance)
        
        # Apply symbol-specific reduction if configured
        symbol_reductions = self.config.get("symbol_sl_reductions", {})
        if symbol in symbol_reductions:
            reduction_percent = symbol_reductions[symbol]
            sl_pips = sl_pips * (1 - reduction_percent / 100)
            print(f"DOWN: {symbol} SL reduced by {reduction_percent}%: {sl_pips:.1f} pips")
        
        return sl_pips
    
    def _fallback_sl_calculation(self, symbol: str, account_balance: float) -> float:
        """
        Fallback SL calculation when dual system is disabled
        Uses old risk-cap based logic
        """
        symbol_config = self.config["symbol_config"][symbol]
        volatility = symbol_config["volatility"]
        account_tier = self._get_account_tier(account_balance)
        
        # Get risk cap
        risk_cap = self.config["risk_by_account_tier"][account_tier][volatility]["risk_dollars"]
        
        # Get lot size from fixed_lot_sizes
        lot_size = self.config["fixed_lot_sizes"].get(account_tier, 0.05)
        
        # Calculate pip value
        pip_value_std = symbol_config["pip_value_per_std_lot"]
        pip_value = pip_value_std * lot_size
        
        # Calculate SL in pips
        sl_pips = risk_cap / pip_value
        
        return sl_pips
    def _get_pip_value(self, symbol: str, lot_size: float) -> float:
        """
        Get pip value for a specific lot size
        Pip value is the monetary value of one pip movement
        """
        
        symbol_config = self.config["symbol_config"][symbol]
        
        # Get pip value for 1 standard lot (base value)
        pip_value_std = symbol_config["pip_value_per_std_lot"]
        
        # Scale to actual lot size being traded
        pip_value = pip_value_std * lot_size
        
        return pip_value
    
    def calculate_tp_price(self, entry_price: float, sl_price: float, 
                          direction: str, rr_ratio: float = 1.0) -> float:
        """
        Calculate TP price based on Risk:Reward ratio
        Default is 1:1 RR for this bot
        """
        
        # Calculate SL distance from entry
        sl_distance = abs(entry_price - sl_price)
        
        # Calculate TP distance based on RR ratio
        tp_distance = sl_distance * rr_ratio
        
        # Calculate TP price based on direction
        if direction == "buy":
            tp_price = entry_price + tp_distance
        else:
            tp_price = entry_price - tp_distance
            
        return tp_price
    
    def adjust_sl_for_reentry(self, original_sl_distance: float, 
                             level: int, reduction_percent: float = 0.2) -> float:
        """
        Calculate reduced SL distance for re-entry levels
        Each level reduces SL by 20% to manage cumulative risk
        """
        
        # Progressive reduction: Level 1 = 100%, Level 2 = 80%, Level 3 = 64%, etc.
        reduction_factor = (1 - reduction_percent) ** (level - 1)
        new_sl_distance = original_sl_distance * reduction_factor
        
        return new_sl_distance
    
    def _get_account_tier(self, balance: float) -> str:
        """
        Determine account tier based on balance
        Returns tier key as string for config lookup
        """
        if balance < 7500:
            return "5000"
        elif balance < 17500:
            return "10000"
        elif balance < 37500:
            return "25000"
        elif balance < 75000:
            return "50000"
        else:
            return "100000"
    
    def validate_trade_risk(self, symbol: str, lot_size: float, sl_pips: float, 
                           account_balance: float) -> Dict:
        """
        Validate that expected loss matches risk cap from dual SL system
        Returns: {"valid": bool, "expected_loss": float, "risk_cap": float, "message": str}
        """
        # Get pip value
        symbol_config = self.config["symbol_config"][symbol]
        pip_value_std = symbol_config["pip_value_per_std_lot"]
        pip_value = pip_value_std * lot_size
        
        # Calculate expected loss
        expected_loss = sl_pips * pip_value
        
        # Get risk cap from active SL system
        account_tier = self._get_account_tier(account_balance)
        active_system = self.config.get("active_sl_system", "sl-1")
        
        try:
            sl_data = self.config["sl_systems"][active_system]["symbols"][symbol][account_tier]
            risk_cap = sl_data["risk_dollars"]
        except KeyError:
            # Fallback to old risk tier system
            volatility = symbol_config["volatility"]
            risk_cap = self.config["risk_by_account_tier"][account_tier][volatility]["risk_dollars"]
        
        # Validate with 10% tolerance
        tolerance = 0.1
        lower_bound = risk_cap * (1 - tolerance)
        upper_bound = risk_cap * (1 + tolerance)
        
        is_valid = lower_bound <= expected_loss <= upper_bound
        
        if is_valid:
            message = f"✅ Risk validated: ${expected_loss:.2f} within ${risk_cap:.2f} cap"
        else:
            message = f"⚠️ Risk mismatch: ${expected_loss:.2f} vs ${risk_cap:.2f} cap"
        
        return {
            "valid": is_valid,
            "expected_loss": expected_loss,
            "risk_cap": risk_cap,
            "message": message
        }