import json
import os
from typing import Dict, Any

def safe_int_from_env(env_var: str, default: int = 0) -> int:
    """Safely parse integer from environment variable with normalization"""
    value = os.getenv(env_var)
    if value is None:
        return default
    
    # Strip and normalize
    value = value.strip().replace(",", "").replace("+", "")
    
    if not value:
        return default
        
    try:
        return int(value)
    except ValueError:
        print(f"WARNING: Invalid integer value for {env_var}: '{os.getenv(env_var)}', using default {default}")
        return default

class Config:
    def __init__(self):
        self.config_file = "config/config.json"
        self.default_config = {
            "telegram_token": os.getenv("TELEGRAM_TOKEN", ""),
            "telegram_chat_id": safe_int_from_env("TELEGRAM_CHAT_ID", 0),
            "allowed_telegram_user": safe_int_from_env("TELEGRAM_CHAT_ID", 0),
            "mt5_login": safe_int_from_env("MT5_LOGIN", 0),
            "mt5_password": os.getenv("MT5_PASSWORD", ""),
            "mt5_server": os.getenv("MT5_SERVER", ""),
            "risk_tiers": {
                "5000": {"per_trade_cap": 150, "daily_loss_limit": 200, "max_total_loss": 500, "base_multiplier": 1.0},
                "10000": {"per_trade_cap": 300, "daily_loss_limit": 400, "max_total_loss": 1000, "base_multiplier": 2.0},
                "25000": {"per_trade_cap": 750, "daily_loss_limit": 1000, "max_total_loss": 2500, "base_multiplier": 5.0},
                "50000": {"per_trade_cap": 1500, "daily_loss_limit": 2000, "max_total_loss": 5000, "base_multiplier": 10.0},
                "100000": {"per_trade_cap": 3000, "daily_loss_limit": 4000, "max_total_loss": 10000, "base_multiplier": 20.0}
            },
            "volatility_risk_levels": {
                "LOW": {"base_per_trade_cap": 30, "base_sl_points": 7},
                "MEDIUM": {"base_per_trade_cap": 50, "base_sl_points": 10},
                "HIGH": {"base_per_trade_cap": 80, "base_sl_points": 15}
            },
            "symbol_config": {
                "EURUSD": {"volatility": "LOW", "pip_value": 10.0, "max_lots": 10.0},
                "GBPUSD": {"volatility": "MEDIUM", "pip_value": 10.0, "max_lots": 8.0},
                "USDJPY": {"volatility": "MEDIUM", "pip_value": 9.0, "max_lots": 10.0},
                "AUDUSD": {"volatility": "MEDIUM", "pip_value": 10.0, "max_lots": 8.0},
                "USDCAD": {"volatility": "MEDIUM", "pip_value": 8.0, "max_lots": 10.0},
                "NZDUSD": {"volatility": "MEDIUM", "pip_value": 10.0, "max_lots": 8.0},
                "EURJPY": {"volatility": "HIGH", "pip_value": 9.5, "max_lots": 5.0},
                "GBPJPY": {"volatility": "HIGH", "pip_value": 9.0, "max_lots": 3.0},
                "AUDJPY": {"volatility": "HIGH", "pip_value": 9.2, "max_lots": 5.0},
                "XAUUSD": {"volatility": "HIGH", "pip_value": 1.0, "max_lots": 2.0}
            },
            "default_risk_tier": "5000",
            "mt5_retries": 3,
            "mt5_wait": 5,
            "simulate_orders": False,
            "debug": True,
            "strategies": ["LOGIC1", "LOGIC2", "LOGIC3"],
            "daily_reset_time": "03:35",
            "fibonacci_levels": {"tp1": 0.618, "tp2": 1.0, "tp3": 1.618},
            "exit_strategies": {
                "default_trailing_points": 50.0,
                "default_time_exit_hours": 4.0,
                "check_interval_seconds": 5
            },
            "dual_order_config": {
                "enabled": True
            },
            "profit_booking_config": {
                "enabled": True,
                "base_profit": 10,
                "max_level": 4,
                "multipliers": [1, 2, 4, 8, 16],
                "profit_targets": [10, 20, 40, 80, 160],
                "sl_reductions": [0, 10, 25, 40, 50]
            }
        }
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
            
            # Environment variables ALWAYS override config.json (highest priority)
            # If env var is SET (even if empty), it takes precedence
            # If env var is NOT SET (None), keep config.json value
            
            if os.getenv("TELEGRAM_TOKEN") is not None:
                self.config["telegram_token"] = os.getenv("TELEGRAM_TOKEN", "")
            
            if os.getenv("TELEGRAM_CHAT_ID") is not None:
                chat_id = safe_int_from_env("TELEGRAM_CHAT_ID", 0)
                self.config["telegram_chat_id"] = chat_id
                self.config["allowed_telegram_user"] = chat_id
            
            if os.getenv("MT5_LOGIN") is not None:
                self.config["mt5_login"] = safe_int_from_env("MT5_LOGIN", 0)
            
            if os.getenv("MT5_PASSWORD") is not None:
                self.config["mt5_password"] = os.getenv("MT5_PASSWORD", "")
            
            if os.getenv("MT5_SERVER") is not None:
                self.config["mt5_server"] = os.getenv("MT5_SERVER", "")
            
            # Ensure new config sections exist (backward compatibility)
            if "dual_order_config" not in self.config:
                self.config["dual_order_config"] = self.default_config["dual_order_config"]
            if "profit_booking_config" not in self.config:
                self.config["profit_booking_config"] = self.default_config["profit_booking_config"]
            
            # Debug: Show loaded credentials (mask password)
            if self.config.get("debug", False):
                try:
                    print(f"Config loaded - MT5 Login: {self.config['mt5_login']}, Server: {self.config['mt5_server']}")
                except UnicodeEncodeError:
                    print(f"Config loaded - MT5 Login: {self.config['mt5_login']}, Server: {self.config['mt5_server']}")
        else:
            self.config = self.default_config
            self.save_config()

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def __getitem__(self, key):
        return self.config.get(key)
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def update(self, key, value):
        self.config[key] = value
        self.save_config()