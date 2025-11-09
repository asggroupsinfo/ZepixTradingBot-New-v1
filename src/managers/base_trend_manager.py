import json
import os
from typing import Dict, Any, Optional

class BaseTrendManager:
    def __init__(self, config_file="config/base_trends.json"):
        self.config_file = config_file
        self.base_trends = self.load_base_trends()
    
    def load_base_trends(self) -> Dict[str, Any]:
        """Load base trends from file with error handling"""
        try:
            if os.path.exists(self.config_file) and os.path.getsize(self.config_file) > 0:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Default structure
                return {
                    "symbols": {},
                    "modes": {"default": "AUTO"}
                }
        except (json.JSONDecodeError, Exception) as e:
            print(f"WARNING: Base trends file corrupted, using defaults: {str(e)}")
            return {
                "symbols": {},
                "modes": {"default": "AUTO"}
            }
    
    def save_base_trends(self):
        """Save base trends to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.base_trends, f, indent=4)
        except Exception as e:
            print(f"ERROR: Error saving base trends: {str(e)}")
    
    def set_base_trend(self, symbol: str, logic: str, trend: str, mode: str = "MANUAL"):
        """Set base trend for a symbol and logic"""
        if symbol not in self.base_trends["symbols"]:
            self.base_trends["symbols"][symbol] = {}
        
        self.base_trends["symbols"][symbol][logic] = {
            "base_trend": trend.upper(),
            "mode": mode.upper(),
            "last_updated": os.path.getmtime(__file__)  # current timestamp
        }
        self.save_base_trends()
    
    def get_base_trend(self, symbol: str, logic: str) -> Optional[Dict[str, Any]]:
        """Get base trend for a symbol and logic"""
        try:
            return self.base_trends["symbols"].get(symbol, {}).get(logic)
        except:
            return None
    
    def set_mode(self, symbol: str, logic: str, mode: str):
        """Set mode (MANUAL/AUTO) for a symbol and logic"""
        if symbol in self.base_trends["symbols"] and logic in self.base_trends["symbols"][symbol]:
            self.base_trends["symbols"][symbol][logic]["mode"] = mode.upper()
            self.save_base_trends()
    
    def get_all_trends(self) -> Dict[str, Any]:
        """Get all base trends"""
        return self.base_trends
    
    def delete_trend(self, symbol: str, logic: str):
        """Delete base trend for a symbol and logic"""
        if symbol in self.base_trends["symbols"] and logic in self.base_trends["symbols"][symbol]:
            del self.base_trends["symbols"][symbol][logic]
            self.save_base_trends()