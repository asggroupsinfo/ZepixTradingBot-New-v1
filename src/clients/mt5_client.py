try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("WARNING: MetaTrader5 not available (Windows only). Running in simulation mode.")

import time
from typing import Dict, Any, Optional
from src.config import Config
from src.models import Trade

class MT5Client:
    def __init__(self, config: Config):
        self.config = config
        self.initialized = False
        # Load symbol mapping from config for broker compatibility
        self.symbol_mapping = config.get("symbol_mapping", {})

    def _map_symbol(self, symbol: str) -> str:
        """
        Map TradingView symbol to broker's MT5 symbol
        Example: XAUUSD (TradingView) -> GOLD (XM Broker)
        """
        mapped = self.symbol_mapping.get(symbol, symbol)
        if mapped != symbol:
            print(f"Symbol mapping: {symbol} -> {mapped}")
        return mapped

    def initialize(self) -> bool:
        """Initialize MT5 connection with retry logic"""
        if not MT5_AVAILABLE:
            print("WARNING: Running in simulation mode (MT5 not available on this platform)")
            self.initialized = True
            return True
            
        for i in range(self.config["mt5_retries"]):
            try:
                if not mt5.initialize():
                    print(f"MT5 initialization failed, retry {i+1}/{self.config['mt5_retries']}")
                    time.sleep(self.config["mt5_wait"])
                    continue
                
                login = self.config.get("mt5_login", 0)
                password = self.config.get("mt5_password", "")
                server = self.config.get("mt5_server", "")
                
                if not login or not password or not server:
                    print(f"ERROR: MT5 credentials missing - Login: {login}, Server: {server}")
                    print("WARNING: Please check .env file for MT5_LOGIN, MT5_PASSWORD, MT5_SERVER")
                    time.sleep(self.config["mt5_wait"])
                    continue
                
                authorized = mt5.login(login, password, server)
                
                if authorized:
                    self.initialized = True
                    print("SUCCESS: MT5 connection established")
                    account_info = mt5.account_info()
                    if account_info:
                        print(f"Account Balance: ${account_info.balance:.2f}")
                        print(f"Account: {account_info.login} | Server: {account_info.server}")
                    return True
                else:
                    error = mt5.last_error()
                    print(f"MT5 login failed, retry {i+1}/{self.config['mt5_retries']}")
                    print(f"ERROR: MT5 login error: {error}")
                    time.sleep(self.config["mt5_wait"])
                    
            except Exception as e:
                print(f"MT5 connection error: {str(e)}")
                time.sleep(self.config["mt5_wait"])
        
        print("ERROR: Failed to connect to MT5 after retries")
        print("WARNING: Check the following:")
        print("  1. MT5 terminal is installed and running")
        print("  2. MT5 terminal is logged in with correct account")
        print("  3. .env file contains correct MT5_LOGIN, MT5_PASSWORD, MT5_SERVER")
        print("  4. MT5 server name matches exactly (case-sensitive)")
        
        # Check if simulation mode is enabled/should be enabled
        if self.config.get("simulate_orders", False):
            print("WARNING: MT5 connection failed but simulation mode enabled - continuing")
            self.initialized = True  # Safe to set for simulation
            return True
        
        return False

    def place_order(self, symbol: str, order_type: str, lot_size: float, 
                   price: float, sl: float, tp: float = None, 
                   comment: str = "") -> Optional[int]:
        """
        Place a new order with TP support and automatic symbol mapping
        This function translates TradingView symbols to broker-specific symbols
        """
        if not self.initialized:
            if not self.initialize():
                return None
        
        # Simulation mode
        if not MT5_AVAILABLE or self.config.get("simulate_orders", True):
            import random
            simulated_ticket = random.randint(100000, 999999)
            print(f"SIMULATED ORDER: {order_type.upper()} {lot_size} lots {symbol} @ {price}, SL={sl}, TP={tp} (Ticket #{simulated_ticket})")
            return simulated_ticket
        
        # Map symbol for broker compatibility - CRITICAL FOR XM BROKER
        mt5_symbol = self._map_symbol(symbol)
        
        try:
            # Get symbol info using the mapped broker symbol
            symbol_info = mt5.symbol_info(mt5_symbol)
            if symbol_info is None:
                print(f"ERROR: Symbol {mt5_symbol} not found in MT5")
                return None
                
            if not symbol_info.visible:
                print(f"Symbol {mt5_symbol} is not visible, attempting to enable")
                if not mt5.symbol_select(mt5_symbol, True):
                    print(f"ERROR: Failed to enable symbol {mt5_symbol}")
                    return None
            
            # Determine order type and get current price
            if order_type == "buy":
                order_type_mt5 = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(mt5_symbol).ask
            else:
                order_type_mt5 = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(mt5_symbol).bid
            
            # Round prices to symbol's digit precision
            digits = symbol_info.digits
            price = round(price, digits)
            sl = round(sl, digits)
            if tp:
                tp = round(tp, digits)
            
            # Prepare order request with mapped symbol
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": mt5_symbol,  # Use broker's symbol name
                "volume": lot_size,
                "type": order_type_mt5,
                "price": price,
                "sl": sl,
                "deviation": 20,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Add TP if provided
            if tp:
                request["tp"] = tp
            
            # Send order to MT5
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"ERROR: Order failed: {result.comment} (Error code: {result.retcode})")
                print(f"Request details: Symbol={mt5_symbol}, Lot={lot_size}, Price={price}, SL={sl}, TP={tp}")
                return None
            
            print(f"SUCCESS: Order placed successfully: Ticket #{result.order}")
            return result.order
            
        except Exception as e:
            print(f"ERROR: Order placement error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def close_position(self, position_id: int, percentage: float = 100):
        """Close a position completely"""
        if not self.initialized:
            if not self.initialize():
                return False
        
        # Simulation mode - always return success
        if not MT5_AVAILABLE or self.config.get("simulate_orders", True):
            print(f"SIMULATED CLOSE: Position #{position_id}")
            return True
        
        try:
            # Get position by ticket
            positions = mt5.positions_get(ticket=position_id)
            
            # Check if it's an API error vs position not found
            if positions is None:
                error = mt5.last_error()
                print(f"ERROR: MT5 API error when getting position {position_id}: {error}")
                return False  # API error - don't mark as closed
            
            if len(positions) == 0:
                print(f"SUCCESS: Position {position_id} already closed (not found in MT5)")
                return True  # Position genuinely doesn't exist - already closed
                
            position = positions[0]
            
            # Prepare close request
            symbol_info = mt5.symbol_info(position.symbol)
            
            if position.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(position.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(position.symbol).ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": position_id,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": order_type,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": f"Close_{percentage}%",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"SUCCESS: Position {position_id} closed successfully")
                return True
            else:
                print(f"Failed to close position: {result.comment}")
                return False
                
        except Exception as e:
            print(f"Position close error: {str(e)}")
            return False

    def get_current_price(self, symbol: str) -> float:
        """
        Get current price for a symbol with automatic mapping support
        Handles both TradingView symbols and broker symbols
        """
        if not self.initialized:
            if not self.initialize():
                return 0.0
        
        # Simulation mode - return dummy prices
        if not MT5_AVAILABLE or self.config.get("simulate_orders", True):
            dummy_prices = {
                "XAUUSD": 2650.0, "GOLD": 2650.0,
                "EURUSD": 1.0850, "GBPUSD": 1.2650,
                "USDJPY": 149.50, "USDCAD": 1.3550
            }
            return dummy_prices.get(symbol, 1.0)
        
        # Map symbol to broker's format
        mt5_symbol = self._map_symbol(symbol)
        
        try:
            tick = mt5.symbol_info_tick(mt5_symbol)
            if tick:
                return (tick.ask + tick.bid) / 2
            return 0.0
        except:
            return 0.0

    def get_account_balance(self) -> float:
        """Get current account balance"""
        if not self.initialized:
            if not self.initialize():
                return 0.0
        
        # Simulation mode - return dummy balance
        if not MT5_AVAILABLE or self.config.get("simulate_orders", True):
            return 10000.0
        
        try:
            account_info = mt5.account_info()
            if account_info:
                return account_info.balance
            return 0.0
        except:
            return 0.0

    def shutdown(self):
        """Shutdown MT5 connection gracefully"""
        if self.initialized:
            mt5.shutdown()
            self.initialized = False
            print("MT5 connection closed")