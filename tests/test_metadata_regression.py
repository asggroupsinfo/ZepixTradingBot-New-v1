#!/usr/bin/env python3
"""
Regression test for ReEntryChain metadata calculation
Verifies original_sl_pips and applied_sl_pips are correct for both unreduced and reduced scenarios
"""
import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import Config
from src.managers.reentry_manager import ReEntryManager
from src.models import Trade

def test_metadata_unreduced():
    """Test metadata when NO reduction is active"""
    print("\n" + "="*80)
    print("TEST 1: METADATA WITHOUT REDUCTION")
    print("="*80)
    
    config = Config()
    config.update("active_sl_system", "sl-1")
    config.update("symbol_sl_reductions", {})  # No reductions
    config.update("account_balance", 10000)
    
    manager = ReEntryManager(config)
    
    # Create test trade for XAUUSD
    # For XAUUSD @ $10k, SL-1 = 1500 pips
    # With pip_size = 0.01, 1500 pips = 15.00 price distance
    trade = Trade(
        symbol="XAUUSD",
        direction="BUY",
        entry=2500.00,
        sl=2485.00,  # 15.00 distance = 1500 pips
        tp=2522.50,
        lot_size=0.15,
        strategy="LOGIC1",
        open_time="2025-10-10 10:00:00",
        trade_id=12345
    )
    
    chain = manager.create_chain(trade)
    
    expected_original = 1500
    expected_applied = 1500
    actual_original = chain.metadata["original_sl_pips"]
    actual_applied = chain.metadata["applied_sl_pips"]
    
    print(f"\nXAUUSD SL-1 @ $10k (NO reduction):")
    print(f"  Expected original: {expected_original} pips")
    print(f"  Actual original:   {actual_original} pips")
    print(f"  Expected applied:  {expected_applied} pips")
    print(f"  Actual applied:    {actual_applied} pips")
    
    if actual_original == expected_original and actual_applied == expected_applied:
        print(f"  [PASS] PASS - Metadata correct without reduction")
        return True
    else:
        print(f"  [FAIL] FAIL - Metadata incorrect!")
        return False

def test_metadata_reduced():
    """Test metadata when 20% reduction is active"""
    print("\n" + "="*80)
    print("TEST 2: METADATA WITH 20% REDUCTION")
    print("="*80)
    
    config = Config()
    config.update("active_sl_system", "sl-1")
    config.update("symbol_sl_reductions", {"XAUUSD": 20})  # 20% reduction
    config.update("account_balance", 10000)
    
    manager = ReEntryManager(config)
    
    # Create test trade for XAUUSD with REDUCED SL
    # Original: 1500 pips, Reduced 20%: 1200 pips
    # With pip_size = 0.01, 1200 pips = 12.00 price distance
    trade = Trade(
        symbol="XAUUSD",
        direction="BUY",
        entry=2500.00,
        sl=2488.00,  # 12.00 distance = 1200 pips (reduced)
        tp=2518.00,
        lot_size=0.15,
        strategy="LOGIC1",
        open_time="2025-10-10 10:00:00",
        trade_id=12346
    )
    
    chain = manager.create_chain(trade)
    
    expected_original = 1500  # Should be unreduced value from config
    expected_applied = 1200   # Should be reduced value (1500 * 0.8)
    actual_original = chain.metadata["original_sl_pips"]
    actual_applied = chain.metadata["applied_sl_pips"]
    
    print(f"\nXAUUSD SL-1 @ $10k (20% reduction):")
    print(f"  Expected original: {expected_original} pips")
    print(f"  Actual original:   {actual_original} pips")
    print(f"  Expected applied:  {expected_applied} pips")
    print(f"  Actual applied:    {actual_applied} pips")
    print(f"  Reduction stored:  {chain.metadata['sl_reduction_percent']}%")
    
    if actual_original == expected_original and actual_applied == expected_applied:
        print(f"  [PASS] PASS - Metadata correct with reduction")
        return True
    else:
        print(f"  [FAIL] FAIL - Metadata incorrect!")
        return False

def test_metadata_sl2_reduced():
    """Test metadata with SL-2 system and reduction"""
    print("\n" + "="*80)
    print("TEST 3: METADATA WITH SL-2 + 30% REDUCTION")
    print("="*80)
    
    config = Config()
    config.update("active_sl_system", "sl-2")
    config.update("symbol_sl_reductions", {"EURUSD": 30})  # 30% reduction
    config.update("account_balance", 10000)
    
    manager = ReEntryManager(config)
    
    # Create test trade for EURUSD
    # SL-2 EURUSD @ $10k = 100 pips, Reduced 30%: 70 pips
    # With pip_size = 0.0001, 70 pips = 0.0070 price distance
    trade = Trade(
        symbol="EURUSD",
        direction="BUY",
        entry=1.1000,
        sl=1.0930,  # 0.0070 distance = 70 pips (reduced)
        tp=1.1105,
        lot_size=0.75,
        strategy="LOGIC2",
        open_time="2025-10-10 10:00:00",
        trade_id=12347
    )
    
    chain = manager.create_chain(trade)
    
    expected_original = 100  # SL-2 EURUSD @ $10k
    expected_applied = 70    # 100 * 0.7
    actual_original = chain.metadata["original_sl_pips"]
    actual_applied = chain.metadata["applied_sl_pips"]
    
    print(f"\nEURUSD SL-2 @ $10k (30% reduction):")
    print(f"  Expected original: {expected_original} pips")
    print(f"  Actual original:   {actual_original} pips")
    print(f"  Expected applied:  {expected_applied} pips")
    print(f"  Actual applied:    {actual_applied} pips")
    print(f"  System stored:     {chain.metadata['sl_system_used']}")
    
    if actual_original == expected_original and actual_applied == expected_applied:
        print(f"  [PASS] PASS - Metadata correct for SL-2 with reduction")
        return True
    else:
        print(f"  [FAIL] FAIL - Metadata incorrect!")
        return False

def main():
    """Run all metadata regression tests"""
    print("\n" + "="*80)
    print(" REENTRY CHAIN METADATA REGRESSION TEST")
    print("="*80)
    
    test1 = test_metadata_unreduced()
    test2 = test_metadata_reduced()
    test3 = test_metadata_sl2_reduced()
    
    print("\n" + "="*80)
    print(" TEST SUMMARY")
    print("="*80)
    print(f"Test 1 (No reduction):     {'[PASS] PASS' if test1 else '[FAIL] FAIL'}")
    print(f"Test 2 (SL-1 + 20% red):   {'[PASS] PASS' if test2 else '[FAIL] FAIL'}")
    print(f"Test 3 (SL-2 + 30% red):   {'[PASS] PASS' if test3 else '[FAIL] FAIL'}")
    
    all_pass = test1 and test2 and test3
    print(f"\nOVERALL: {'[PASS] ALL TESTS PASSED' if all_pass else '[FAIL] SOME TESTS FAILED'}")
    
    # Reset config
    config = Config()
    config.update("active_sl_system", "sl-1")
    config.update("symbol_sl_reductions", {})
    
    return all_pass

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
