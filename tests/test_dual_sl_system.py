#!/usr/bin/env python3
"""
Test script for Dual SL System validation
Tests SL-1 and SL-2 for all 10 symbols × 5 account tiers
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

import json

from src.config import Config
from src.utils.pip_calculator import PipCalculator

def test_sl_system(system_name, config):
    """Test a specific SL system for all symbols and tiers"""
    print(f"\n{'='*80}")
    print(f"TESTING {system_name}")
    print(f"{'='*80}\n")
    
    calculator = PipCalculator(config)
    
    symbols = ["EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "NZDUSD", 
               "USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "XAUUSD"]
    
    account_tiers = [
        (5000, "5000"),
        (10000, "10000"),
        (25000, "25000"),
        (50000, "50000"),
        (100000, "100000")
    ]
    
    errors = []
    passed = 0
    
    for symbol in symbols:
        print(f"\n{symbol}:")
        symbol_config = config["symbol_config"][symbol]
        pip_size = symbol_config["pip_size"]
        
        for balance, tier_key in account_tiers:
            # Get expected SL from config
            try:
                expected_data = config["sl_systems"][system_name]["symbols"][symbol][tier_key]
                expected_sl_pips = expected_data["sl_pips"]
                expected_risk = expected_data["risk_dollars"]
            except KeyError:
                errors.append(f"[FAIL] Missing config: {symbol} @ {tier_key} in {system_name}")
                continue
            
            # Calculate SL using pip calculator
            calculated_sl_pips = calculator._get_sl_from_dual_system(symbol, balance)
            
            # Validate
            tolerance = 1.0  # 1 pip tolerance
            if abs(calculated_sl_pips - expected_sl_pips) <= tolerance:
                print(f"  [PASS] ${balance:>6}: {calculated_sl_pips:>6.1f} pips (expected {expected_sl_pips})")
                passed += 1
            else:
                error_msg = f"  [FAIL] ${balance:>6}: {calculated_sl_pips:>6.1f} pips (expected {expected_sl_pips})"
                print(error_msg)
                errors.append(error_msg)
    
    return passed, errors

def test_sl_reduction():
    """Test SL reduction functionality"""
    print(f"\n{'='*80}")
    print(f"TESTING SL REDUCTION")
    print(f"{'='*80}\n")
    
    config = Config()
    
    # Set active system to sl-1
    config.update("active_sl_system", "sl-1")
    
    # Test: Reduce XAUUSD by 20%
    config.update("symbol_sl_reductions", {"XAUUSD": 20})
    
    calculator = PipCalculator(config)
    
    # Test $10k account
    balance = 10000
    expected_original = 1500  # SL-1 XAUUSD @ $10k
    expected_reduced = 1500 * 0.8  # 20% reduction = 1200 pips
    
    calculated = calculator._get_sl_from_dual_system("XAUUSD", balance)
    
    print(f"XAUUSD @ $10,000:")
    print(f"  Original: {expected_original} pips")
    print(f"  Reduction: 20%")
    print(f"  Expected: {expected_reduced} pips")
    print(f"  Calculated: {calculated} pips")
    
    if abs(calculated - expected_reduced) <= 1:
        print(f"  [PASS] PASS - Reduction working correctly")
        return True
    else:
        print(f"  [FAIL] FAIL - Reduction not applied correctly")
        return False

def test_system_switching():
    """Test switching between SL-1 and SL-2"""
    print(f"\n{'='*80}")
    print(f"TESTING SYSTEM SWITCHING")
    print(f"{'='*80}\n")
    
    config = Config()
    calculator = PipCalculator(config)
    balance = 10000
    
    # Test SL-1 for XAUUSD
    config.update("active_sl_system", "sl-1")
    sl1_value = calculator._get_sl_from_dual_system("XAUUSD", balance)
    print(f"SL-1 active: XAUUSD @ $10k = {sl1_value} pips (expected 1500)")
    
    # Switch to SL-2
    config.update("active_sl_system", "sl-2")
    sl2_value = calculator._get_sl_from_dual_system("XAUUSD", balance)
    print(f"SL-2 active: XAUUSD @ $10k = {sl2_value} pips (expected 800)")
    
    # Validate
    sl1_pass = abs(sl1_value - 1500) <= 1
    sl2_pass = abs(sl2_value - 800) <= 1
    
    if sl1_pass and sl2_pass:
        print(f"[PASS] PASS - System switching works correctly")
        return True
    else:
        print(f"[FAIL] FAIL - System switching issue")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print(" DUAL SL SYSTEM VALIDATION TEST")
    print("="*80)
    
    config = Config()
    
    # Test SL-1
    config.update("active_sl_system", "sl-1")
    config.update("symbol_sl_reductions", {})  # Clear reductions
    sl1_passed, sl1_errors = test_sl_system("sl-1", config)
    
    # Test SL-2
    config.update("active_sl_system", "sl-2")
    sl2_passed, sl2_errors = test_sl_system("sl-2", config)
    
    # Test reduction
    reduction_pass = test_sl_reduction()
    
    # Test switching
    switching_pass = test_system_switching()
    
    # Summary
    print(f"\n{'='*80}")
    print(f" TEST SUMMARY")
    print(f"{'='*80}")
    print(f"SL-1 Tests: {sl1_passed}/50 passed")
    print(f"SL-2 Tests: {sl2_passed}/50 passed")
    print(f"Reduction Test: {'[PASS] PASS' if reduction_pass else '[FAIL] FAIL'}")
    print(f"Switching Test: {'[PASS] PASS' if switching_pass else '[FAIL] FAIL'}")
    
    total_tests = 50 + 50 + 1 + 1  # 102 total
    total_passed = sl1_passed + sl2_passed + (1 if reduction_pass else 0) + (1 if switching_pass else 0)
    
    print(f"\nOVERALL: {total_passed}/{total_tests} tests passed")
    
    if sl1_errors or sl2_errors:
        print(f"\n[FAIL] ERRORS FOUND:")
        for error in sl1_errors + sl2_errors:
            print(f"  {error}")
    
    # Reset config to sl-1
    config.update("active_sl_system", "sl-1")
    config.update("symbol_sl_reductions", {})
    
    return total_passed == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
