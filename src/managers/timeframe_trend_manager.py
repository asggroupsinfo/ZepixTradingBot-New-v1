from typing import Dict, Any, Optional
from datetime import datetime
import json
import os

class TimeframeTrendManager:
    """Manage trends per timeframe instead of per logic"""
    
    def __init__(self, config_file="config/timeframe_trends.json"):
        self.config_file = config_file
        self.trends = self.load_trends()
        
    def load_trends(self) -> Dict[str, Any]:
        """Load trends from file with error handling"""
        try:
            if os.path.exists(self.config_file) and os.path.getsize(self.config_file) > 0:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Return default structure if file doesn't exist or is empty
                return {
                    "symbols": {},
                    "default_mode": "AUTO"
                }
        except (json.JSONDecodeError, Exception) as e:
            print(f"WARNING: Trends file corrupted, using defaults: {str(e)}")
            return {
                "symbols": {},
                "default_mode": "AUTO"
            }
    
    def save_trends(self):
        """Save trends to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.trends, f, indent=4)
        except Exception as e:
            print(f"ERROR: Error saving trends: {str(e)}")
    
    def update_trend(self, symbol: str, timeframe: str, signal: str, mode: str = "AUTO"):
        """Update trend for a specific symbol and timeframe"""
        
        if symbol not in self.trends["symbols"]:
            self.trends["symbols"][symbol] = {}
        
        if timeframe not in self.trends["symbols"][symbol]:
            self.trends["symbols"][symbol][timeframe] = {}
        
        # Check if manually locked
        current = self.trends["symbols"][symbol][timeframe]
        if current.get("mode") == "MANUAL" and mode == "AUTO":
            print(f"WARNING: Manual trend locked for {symbol} {timeframe}, not updating")
            return  # Don't override manual settings
        
        # Convert signal to trend - FIXED BUG HERE
        signal_lower = signal.lower()
        if signal_lower in ["bull", "buy", "bullish"]:
            trend = "BULLISH"
        elif signal_lower in ["bear", "sell", "bearish"]:
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"
        
        self.trends["symbols"][symbol][timeframe] = {
            "trend": trend,
            "mode": mode,
            "last_update": datetime.now().isoformat()
        }
        self.save_trends()
        print(f"SUCCESS: Trend updated: {symbol} {timeframe} -> {trend} ({mode})")
    
    def get_trend(self, symbol: str, timeframe: str) -> Optional[str]:
        """Get trend for a specific symbol and timeframe"""
        try:
            return self.trends["symbols"].get(symbol, {}).get(timeframe, {}).get("trend", "NEUTRAL")
        except:
            return "NEUTRAL"
    
    def get_mode(self, symbol: str, timeframe: str) -> str:
        """Get mode for a specific symbol and timeframe"""
        try:
            return self.trends["symbols"].get(symbol, {}).get(timeframe, {}).get("mode", "AUTO")
        except:
            return "AUTO"
    
    def check_logic_alignment(self, symbol: str, logic: str) -> Dict[str, Any]:
        """Check if trends align for a specific trading logic"""
        
        result = {
            "aligned": False,
            "direction": "NEUTRAL",
            "details": {}
        }
        
        if symbol not in self.trends["symbols"]:
            return result
        
        symbol_trends = self.trends["symbols"][symbol]
        
        if logic == "LOGIC1":  # 1H bias + 15M trend for 5M entries
            h1_trend = symbol_trends.get("1h", {}).get("trend", "NEUTRAL")
            m15_trend = symbol_trends.get("15m", {}).get("trend", "NEUTRAL")
            
            result["details"] = {"1h": h1_trend, "15m": m15_trend}
            
            if h1_trend != "NEUTRAL" and h1_trend == m15_trend:
                result["aligned"] = True
                result["direction"] = h1_trend
                
        elif logic == "LOGIC2":  # 1H bias + 15M trend for 15M entries
            h1_trend = symbol_trends.get("1h", {}).get("trend", "NEUTRAL")
            m15_trend = symbol_trends.get("15m", {}).get("trend", "NEUTRAL")
            
            result["details"] = {"1h": h1_trend, "15m": m15_trend}
            
            if h1_trend != "NEUTRAL" and h1_trend == m15_trend:
                result["aligned"] = True
                result["direction"] = h1_trend
                
        elif logic == "LOGIC3":  # 1D bias + 1H trend for 1H entries
            d1_trend = symbol_trends.get("1d", {}).get("trend", "NEUTRAL")
            h1_trend = symbol_trends.get("1h", {}).get("trend", "NEUTRAL")
            
            result["details"] = {"1d": d1_trend, "1h": h1_trend}
            
            if d1_trend != "NEUTRAL" and d1_trend == h1_trend:
                result["aligned"] = True
                result["direction"] = d1_trend
        
        return result
    
    def set_manual_trend(self, symbol: str, timeframe: str, trend: str):
        """Manually set a trend that won't be overridden by signals"""
        # Convert BULLISH/BEARISH to bull/bear for signal
        if trend.upper() == "BULLISH":
            signal = "bull"
        elif trend.upper() == "BEARISH":
            signal = "bear"
        else:
            signal = "neutral"
            
        self.update_trend(symbol, timeframe, signal, "MANUAL")
    
    def set_auto_trend(self, symbol: str, timeframe: str):
        """Set trend back to AUTO mode (will be updated by TradingView signals)"""
        if symbol in self.trends["symbols"] and timeframe in self.trends["symbols"][symbol]:
            self.trends["symbols"][symbol][timeframe]["mode"] = "AUTO"
            self.save_trends()
            print(f"SUCCESS: Mode set to AUTO for {symbol} {timeframe}")
    
    def get_all_trends(self, symbol: str) -> Dict[str, str]:
        """Get all timeframe trends for a symbol"""
        if symbol not in self.trends["symbols"]:
            return {"5m": "NEUTRAL", "15m": "NEUTRAL", "1h": "NEUTRAL", "1d": "NEUTRAL"}
        
        result = {}
        for tf in ["5m", "15m", "1h", "1d"]:
            result[tf] = self.trends["symbols"][symbol].get(tf, {}).get("trend", "NEUTRAL")
        
        return result
    
    def get_all_trends_with_mode(self, symbol: str) -> Dict[str, Dict[str, str]]:
        """Get all timeframe trends with mode information"""
        if symbol not in self.trends["symbols"]:
            return {
                "5m": {"trend": "NEUTRAL", "mode": "AUTO"},
                "15m": {"trend": "NEUTRAL", "mode": "AUTO"},
                "1h": {"trend": "NEUTRAL", "mode": "AUTO"},
                "1d": {"trend": "NEUTRAL", "mode": "AUTO"}
            }
        
        result = {}
        for tf in ["5m", "15m", "1h", "1d"]:
            trend_data = self.trends["symbols"][symbol].get(tf, {})
            result[tf] = {
                "trend": trend_data.get("trend", "NEUTRAL"),
                "mode": trend_data.get("mode", "AUTO")
            }
        
        return result