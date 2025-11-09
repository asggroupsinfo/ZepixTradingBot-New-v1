import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from src.models import Trade

class ExitStrategyManager:
    def __init__(self, mt5_client, trading_engine):
        self.mt5_client = mt5_client
        self.trading_engine = trading_engine
        self.active_strategies = {}
        self.running = False

    def start_monitoring(self):
        """Start the exit strategy monitoring loop"""
        self.running = True
        asyncio.create_task(self.monitor_strategies())

    def stop_monitoring(self):
        """Stop the exit strategy monitoring loop"""
        self.running = False

    async def monitor_strategies(self):
        """Monitor all active exit strategies"""
        while self.running:
            try:
                for trade_id, strategy in list(self.active_strategies.items()):
                    current_price = self.mt5_client.get_current_price(strategy['symbol'])
                    
                    if strategy['type'] == 'trailing_stop':
                        if await self.check_trailing_stop(trade_id, current_price, strategy):
                            # Trading engine ke through close karo
                            trade = strategy['trade']
                            await self.trading_engine.close_trade(trade, 100, "TRAILING_SL_EXIT")
                            
                    elif strategy['type'] == 'time_based':
                        if datetime.now() >= strategy['expiry_time']:
                            # Trading engine ke through close karo
                            trade = strategy['trade']
                            await self.trading_engine.close_trade(trade, 100, "TIME_BASED_EXIT")
                            
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"Exit strategy monitoring error: {str(e)}")
                await asyncio.sleep(30)

    async def check_trailing_stop(self, trade_id: str, current_price: float, strategy: Dict[str, Any]) -> bool:
        """Check if trailing stop condition is met"""
        try:
            trade = strategy['trade']
            
            if trade.direction == "buy":
                # Update best price if current price is higher
                if current_price > strategy['best_price']:
                    strategy['best_price'] = current_price
                    print(f"UP: Trailing SL updated: {strategy['best_price']}")
                
                # Check if price hit trailing SL
                sl_price = strategy['best_price'] - strategy['trailing_points']
                if current_price <= sl_price:
                    print(f"HIT: Trailing SL hit: {current_price} <= {sl_price}")
                    return True
                    
            else:  # sell
                # Update best price if current price is lower
                if current_price < strategy['best_price']:
                    strategy['best_price'] = current_price
                    print(f"DOWN: Trailing SL updated: {strategy['best_price']}")
                
                # Check if price hit trailing SL
                sl_price = strategy['best_price'] + strategy['trailing_points']
                if current_price >= sl_price:
                    print(f"HIT: Trailing SL hit: {current_price} >= {sl_price}")
                    return True
                    
            return False
            
        except Exception as e:
            print(f"Trailing stop check error: {str(e)}")
            return False

    # 🔥 NEW FUNCTION ADDED - Missing function fix
    def check_exit_conditions(self, trade: Trade) -> bool:
        """Check if exit conditions are met for a trade"""
        try:
            if trade.trade_id in self.active_strategies:
                strategy = self.active_strategies[trade.trade_id]
                current_price = self.mt5_client.get_current_price(trade.symbol)
                
                if strategy['type'] == 'trailing_stop':
                    if trade.direction == "buy":
                        sl_price = strategy['best_price'] - strategy['trailing_points']
                        return current_price <= sl_price
                    else:
                        sl_price = strategy['best_price'] + strategy['trailing_points']
                        return current_price >= sl_price
                        
                elif strategy['type'] == 'time_based':
                    return datetime.now() >= strategy['expiry_time']
                    
            return False
            
        except Exception as e:
            print(f"Exit condition check error: {str(e)}")
            return False

    def add_trailing_stop(self, trade: Trade, trailing_points: float = 50.0):
        """Add trailing stop loss to a trade"""
        self.active_strategies[trade.trade_id] = {
            'type': 'trailing_stop',
            'trade': trade,
            'symbol': trade.symbol,
            'trailing_points': trailing_points,
            'best_price': trade.entry,
            'added_time': datetime.now()
        }
        print(f"SUCCESS: Trailing SL added for {trade.symbol} - {trailing_points} points")

    def add_time_based_exit(self, trade: Trade, exit_after_hours: float = 4.0):
        """Add time-based exit to a trade"""
        self.active_strategies[trade.trade_id] = {
            'type': 'time_based',
            'trade': trade,
            'symbol': trade.symbol,
            'expiry_time': datetime.now() + timedelta(hours=exit_after_hours),
            'added_time': datetime.now()
        }
        print(f"SUCCESS: Time-based exit added for {trade.symbol} - {exit_after_hours} hours")

    def remove_strategy(self, trade_id: str):
        """Remove exit strategy for a trade"""
        if trade_id in self.active_strategies:
            del self.active_strategies[trade_id]
            print(f"REMOVED: Exit strategy removed for trade {trade_id}")

    def get_active_strategies(self) -> Dict[str, Any]:
        """Get all active exit strategies"""
        return self.active_strategies