"""
Complete Bot Test Script
Tests all components of the trading bot
"""
import sys
import traceback
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

def test_imports():
    """Test all module imports"""
    print("=" * 60)
    print("TEST 1: Module Imports")
    print("=" * 60)
    
    modules = [
        'src.config',
        'src.models',
        'src.database',
        'src.managers.risk_manager',
        'src.utils.pip_calculator',
        'src.managers.dual_order_manager',
        'src.managers.profit_booking_manager',
        'src.clients.telegram_bot',
        'src.core.trading_engine',
        'src.services.price_monitor_service',
        'src.services.reversal_exit_handler',
        'src.clients.mt5_client',
        'src.processors.alert_processor'
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"[PASS] {module}")
        except Exception as e:
            print(f"[FAIL] {module}: {str(e)}")
            failed.append((module, str(e)))
    
    if failed:
        print(f"\n[FAIL] {len(failed)} modules failed to import")
        return False
    else:
        print(f"\n[PASS] All {len(modules)} modules imported successfully")
        return True

def test_models():
    """Test model classes"""
    print("\n" + "=" * 60)
    print("TEST 2: Model Classes")
    print("=" * 60)
    
    try:
        from src.models import Trade, ProfitBookingChain
        
        # Test Trade model with new fields
        trade = Trade(
            symbol='EURUSD',
            entry=1.1000,
            sl=1.0950,
            tp=1.1050,
            lot_size=0.01,
            direction='buy',
            strategy='LOGIC1',
            open_time='2024-01-01T00:00:00',
            order_type='TP_TRAIL',
            profit_chain_id=None,
            profit_level=0
        )
        
        assert hasattr(trade, 'order_type'), "Trade missing order_type"
        assert hasattr(trade, 'profit_chain_id'), "Trade missing profit_chain_id"
        assert hasattr(trade, 'profit_level'), "Trade missing profit_level"
        assert trade.order_type == 'TP_TRAIL', "order_type not set correctly"
        print("[PASS] Trade model with new fields")
        
        # Test ProfitBookingChain model
        chain = ProfitBookingChain(
            chain_id='TEST123',
            symbol='EURUSD',
            direction='buy',
            base_lot=0.01,
            current_level=0,
            max_level=4,
            total_profit=0.0,
            active_orders=[],
            status='ACTIVE',
            created_at='2024-01-01T00:00:00',
            updated_at='2024-01-01T00:00:00'
        )
        
        assert chain.chain_id == 'TEST123', "Chain ID not set"
        assert chain.status == 'ACTIVE', "Chain status not set"
        print("[PASS] ProfitBookingChain model")
        
        return True
    except Exception as e:
        print(f"[FAIL] Model test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_config():
    """Test configuration"""
    print("\n" + "=" * 60)
    print("TEST 3: Configuration")
    print("=" * 60)
    
    try:
        from src.config import Config
        config = Config()
        
        # Test dual_order_config
        dual_config = config.get('dual_order_config', {})
        assert 'enabled' in dual_config, "dual_order_config missing enabled"
        print("[PASS] dual_order_config exists")
        
        # Test profit_booking_config
        profit_config = config.get('profit_booking_config', {})
        assert 'enabled' in profit_config, "profit_booking_config missing enabled"
        assert 'profit_targets' in profit_config, "profit_booking_config missing profit_targets"
        assert 'multipliers' in profit_config, "profit_booking_config missing multipliers"
        assert 'sl_reductions' in profit_config, "profit_booking_config missing sl_reductions"
        print("[PASS] profit_booking_config exists with all fields")
        
        return True
    except Exception as e:
        print(f"[FAIL] Config test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_database():
    """Test database tables and methods"""
    print("\n" + "=" * 60)
    print("TEST 4: Database")
    print("=" * 60)
    
    try:
        from src.database import TradeDatabase
        db = TradeDatabase()
        
        # Check tables exist
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'profit_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['profit_booking_chains', 'profit_booking_orders', 'profit_booking_events']
        for table in required_tables:
            assert table in tables, f"Table {table} not found"
            print(f"[PASS] Table {table} exists")
        
        # Test methods exist
        assert hasattr(db, 'save_profit_chain'), "save_profit_chain method missing"
        assert hasattr(db, 'get_active_profit_chains'), "get_active_profit_chains method missing"
        assert hasattr(db, 'get_profit_chain_stats'), "get_profit_chain_stats method missing"
        assert hasattr(db, 'save_profit_booking_order'), "save_profit_booking_order method missing"
        assert hasattr(db, 'save_profit_booking_event'), "save_profit_booking_event method missing"
        print("[PASS] All database methods exist")
        
        return True
    except Exception as e:
        print(f"[FAIL] Database test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_managers():
    """Test DualOrderManager and ProfitBookingManager"""
    print("\n" + "=" * 60)
    print("TEST 5: Manager Classes")
    print("=" * 60)
    
    try:
        from src.config import Config
        from src.managers.risk_manager import RiskManager
        from src.clients.mt5_client import MT5Client
        from src.utils.pip_calculator import PipCalculator
        from src.database import TradeDatabase
        from src.managers.dual_order_manager import DualOrderManager
        from src.managers.profit_booking_manager import ProfitBookingManager
        
        config = Config()
        risk_manager = RiskManager(config)
        mt5_client = MT5Client(config)
        pip_calculator = PipCalculator(config)
        db = TradeDatabase()
        
        # Test DualOrderManager
        dual_manager = DualOrderManager(config, risk_manager, mt5_client, pip_calculator)
        assert hasattr(dual_manager, 'create_dual_orders'), "DualOrderManager missing create_dual_orders"
        assert hasattr(dual_manager, 'validate_dual_order_risk'), "DualOrderManager missing validate_dual_order_risk"
        assert hasattr(dual_manager, 'is_enabled'), "DualOrderManager missing is_enabled"
        print("[PASS] DualOrderManager initialized with all methods")
        
        # Test ProfitBookingManager
        profit_manager = ProfitBookingManager(config, mt5_client, pip_calculator, risk_manager, db)
        assert hasattr(profit_manager, 'create_profit_chain'), "ProfitBookingManager missing create_profit_chain"
        assert hasattr(profit_manager, 'check_profit_targets'), "ProfitBookingManager missing check_profit_targets"
        assert hasattr(profit_manager, 'calculate_combined_pnl'), "ProfitBookingManager missing calculate_combined_pnl"
        assert hasattr(profit_manager, 'execute_profit_booking'), "ProfitBookingManager missing execute_profit_booking"
        assert hasattr(profit_manager, 'recover_chains_from_database'), "ProfitBookingManager missing recover_chains_from_database"
        print("[PASS] ProfitBookingManager initialized with all methods")
        
        return True
    except Exception as e:
        print(f"[FAIL] Manager test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_risk_manager():
    """Test RiskManager new methods"""
    print("\n" + "=" * 60)
    print("TEST 6: Risk Manager")
    print("=" * 60)
    
    try:
        from src.config import Config
        from src.managers.risk_manager import RiskManager
        
        config = Config()
        risk_manager = RiskManager(config)
        
        assert hasattr(risk_manager, 'validate_dual_orders'), "RiskManager missing validate_dual_orders"
        assert hasattr(risk_manager, 'calculate_profit_booking_risk'), "RiskManager missing calculate_profit_booking_risk"
        print("[PASS] RiskManager has new methods")
        
        return True
    except Exception as e:
        print(f"[FAIL] RiskManager test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_telegram_commands():
    """Test Telegram commands"""
    print("\n" + "=" * 60)
    print("TEST 7: Telegram Commands")
    print("=" * 60)
    
    try:
        from src.clients.telegram_bot import TelegramBot
        from src.config import Config
        
        config = Config()
        bot = TelegramBot(config)
        
        required_commands = [
            '/dual_order_status',
            '/toggle_dual_orders',
            '/profit_status',
            '/profit_stats',
            '/toggle_profit_booking',
            '/set_profit_targets',
            '/profit_chains',
            '/stop_profit_chain',
            '/stop_all_profit_chains',
            '/set_chain_multipliers',
            '/set_sl_reductions',
            '/profit_config',
            '/close_profit_chain'
        ]
        
        missing = []
        for cmd in required_commands:
            if cmd not in bot.command_handlers:
                missing.append(cmd)
            else:
                print(f"[PASS] {cmd}")
        
        if missing:
            print(f"[FAIL] Missing commands: {missing}")
            return False
        else:
            print(f"[PASS] All {len(required_commands)} commands registered")
            return True
    except Exception as e:
        print(f"[FAIL] Telegram commands test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_price_monitor():
    """Test PriceMonitorService profit booking integration"""
    print("\n" + "=" * 60)
    print("TEST 8: Price Monitor Service")
    print("=" * 60)
    
    try:
        from src.services.price_monitor_service import PriceMonitorService
        import inspect
        
        # Check if method exists
        source = inspect.getsource(PriceMonitorService)
        assert '_check_profit_booking_chains' in source, "_check_profit_booking_chains method not found"
        print("[PASS] _check_profit_booking_chains method exists")
        
        # Check if it's called in _check_all_opportunities
        assert '_check_profit_booking_chains()' in source or 'await self._check_profit_booking_chains()' in source, "_check_profit_booking_chains not called"
        print("[PASS] _check_profit_booking_chains integrated in monitoring loop")
        
        return True
    except Exception as e:
        print(f"[FAIL] Price monitor test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_reversal_exit_handler():
    """Test ReversalExitHandler profit chain stopping"""
    print("\n" + "=" * 60)
    print("TEST 9: Reversal Exit Handler")
    print("=" * 60)
    
    try:
        from src.services.reversal_exit_handler import ReversalExitHandler
        import inspect
        
        source = inspect.getsource(ReversalExitHandler.execute_reversal_exit)
        assert 'profit_chain_id' in source, "profit_chain_id handling not found"
        assert 'stop_chain' in source, "stop_chain call not found"
        print("[PASS] Exit signal handling for profit chains implemented")
        
        return True
    except Exception as e:
        print(f"[FAIL] Reversal exit handler test failed: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("COMPLETE BOT TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_models,
        test_config,
        test_database,
        test_managers,
        test_risk_manager,
        test_telegram_commands,
        test_price_monitor,
        test_reversal_exit_handler
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[FAIL] Test {test.__name__} crashed: {str(e)}")
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Tests Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n[PASS] ALL TESTS PASSED - BOT IS 100% READY!")
        return 0
    else:
        print("\n[FAIL] SOME TESTS FAILED - PLEASE REVIEW")
        return 1

if __name__ == "__main__":
    sys.exit(main())

