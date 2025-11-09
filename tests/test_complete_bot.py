#!/usr/bin/env python3
"""
Complete Bot Feature Test Script
Tests all existing and new features
"""
import requests
import json
import time
import sqlite3
from typing import Dict, Any

BASE_URL = "http://localhost:5000"

def test_health():
    """Test 1: Bot Health Check"""
    print("=" * 60)
    print("TEST 1: BOT HEALTH CHECK")
    print("=" * 60)
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Status: {data.get('status')}")
            print(f"Version: {data.get('version')}")
            print(f"MT5 Connected: {data.get('mt5_connected')}")
            print("SUCCESS: PASS - Bot is healthy")
            return True
        else:
            print("FAIL: Health check failed")
            return False
    except Exception as e:
        print(f"FAIL: Error: {e}")
        return False

def test_status():
    """Test 2: Bot Status Check"""
    print("\n" + "=" * 60)
    print("TEST 2: BOT STATUS CHECK")
    print("=" * 60)
    try:
        r = requests.get(f"{BASE_URL}/status", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"Status: {data.get('status')}")
            print(f"MT5 Connected: {data.get('mt5_connected')}")
            print(f"Simulation Mode: {data.get('simulation_mode')}")
            print(f"Dual Orders Enabled: {data.get('dual_orders_enabled')}")
            print(f"Profit Booking Enabled: {data.get('profit_booking_enabled')}")
            print(f"Open Trades: {data.get('open_trades_count', 0)}")
            print("SUCCESS: PASS - Status check successful")
            return True, data
        else:
            print("FAIL: Status check failed")
            return False, None
    except Exception as e:
        print(f"FAIL: Error: {e}")
        return False, None

def test_signal(symbol: str, signal: str, price: float, signal_type: str = "entry", strategy: str = "LOGIC1", tf: str = "5m"):
    """Test 3: Send Signal"""
    print("\n" + "=" * 60)
    print(f"TEST 3: SIGNAL RECEIVING ({signal.upper()})")
    print("=" * 60)
    try:
        payload = {
            "symbol": symbol,
            "signal": signal,
            "price": price,
            "type": signal_type,
            "strategy": strategy,
            "tf": tf
        }
        r = requests.post(f"{BASE_URL}/webhook", json=payload, timeout=10)
        print(f"Status Code: {r.status_code}")
        response = r.json() if r.status_code == 200 else None
        print(f"Response: {response}")
        if response and response.get('status') == 'success':
            print("SUCCESS: PASS - Signal accepted and processed")
            return True
        else:
            print(f"WARNING: Signal response: {response}")
            return False
    except Exception as e:
        print(f"FAIL: Error: {e}")
        return False

def test_dual_orders():
    """Test 4: Dual Order Placement Check"""
    print("\n" + "=" * 60)
    print("TEST 4: DUAL ORDER PLACEMENT CHECK")
    print("=" * 60)
    try:
        r = requests.get(f"{BASE_URL}/status", timeout=5)
        if r.status_code == 200:
            data = r.json()
            trades = data.get('open_trades', [])
            print(f"Total Open Trades: {len(trades)}")
            
            tp_trail = [t for t in trades if t.get('order_type') == 'TP_TRAIL']
            profit_trail = [t for t in trades if t.get('order_type') == 'PROFIT_TRAIL']
            
            print(f"TP Trail Orders: {len(tp_trail)}")
            print(f"Profit Trail Orders: {len(profit_trail)}")
            
            if len(tp_trail) > 0 and len(profit_trail) > 0:
                print("SUCCESS: PASS - Dual orders placed correctly")
                return True
            else:
                print("WARNING: Dual orders not found (may need to send signal first)")
                return False
        else:
            print("FAIL: Status check failed")
            return False
    except Exception as e:
        print(f"FAIL: Error: {e}")
        return False

def test_profit_chains():
    """Test 5: Profit Booking Chain Check"""
    print("\n" + "=" * 60)
    print("TEST 5: PROFIT BOOKING CHAIN CHECK")
    print("=" * 60)
    try:
        conn = sqlite3.connect('data/trading_bot.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM profit_booking_chains WHERE status='ACTIVE'")
        chains_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT chain_id, symbol, current_level, status FROM profit_booking_chains WHERE status='ACTIVE' LIMIT 5")
        chain_data = cursor.fetchall()
        
        print(f"Active Profit Chains: {chains_count}")
        if chain_data:
            print("Chain Details:")
            for chain in chain_data:
                print(f"  Chain: {chain[0]} | Symbol: {chain[1]} | Level: {chain[2]} | Status: {chain[3]}")
            print("SUCCESS: PASS - Profit chains found")
            result = True
        else:
            print("WARNING: No active profit chains found (may need to send signal first)")
            result = False
        
        conn.close()
        return result
    except Exception as e:
        print(f"FAIL: Error: {e}")
        return False

def test_database():
    """Test 6: Database Verification"""
    print("\n" + "=" * 60)
    print("TEST 6: DATABASE VERIFICATION")
    print("=" * 60)
    try:
        conn = sqlite3.connect('data/trading_bot.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM trades WHERE status='open'")
        open_trades = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM trades WHERE order_type='TP_TRAIL' AND status='open'")
        tp_trail = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM trades WHERE order_type='PROFIT_TRAIL' AND status='open'")
        profit_trail = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM profit_booking_chains WHERE status='ACTIVE'")
        active_chains = cursor.fetchone()[0]
        
        print(f"Total Open Trades (DB): {open_trades}")
        print(f"TP Trail Orders (DB): {tp_trail}")
        print(f"Profit Trail Orders (DB): {profit_trail}")
        print(f"Active Profit Chains (DB): {active_chains}")
        
        conn.close()
        print("SUCCESS: PASS - Database verification successful")
        return True
    except Exception as e:
        print(f"FAIL: Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("COMPLETE BOT FEATURE TEST")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Health Check
    results['health'] = test_health()
    
    # Test 2: Status Check
    status_ok, status_data = test_status()
    results['status'] = status_ok
    
    if not status_ok:
        print("\nFAIL: Bot is not running. Please start the bot first.")
        print("Run: python main.py --host 0.0.0.0 --port 5000")
        return
    
    # Test 3: Send BUY Signal
    results['signal_buy'] = test_signal("EURUSD", "buy", 1.10000, "entry", "LOGIC1", "5m")
    time.sleep(3)
    
    # Test 4: Check Dual Orders
    results['dual_orders'] = test_dual_orders()
    
    # Test 5: Check Profit Chains
    results['profit_chains'] = test_profit_chains()
    
    # Test 6: Database Verification
    results['database'] = test_database()
    
    # Test 7: Send SELL Signal
    results['signal_sell'] = test_signal("GBPUSD", "sell", 1.27500, "entry", "LOGIC2", "15m")
    time.sleep(3)
    
    # Test 8: Check Multiple Trades
    results['multiple_trades'] = test_dual_orders()
    
    # Test 9: Send Exit Signal
    results['exit_signal'] = test_signal("EURUSD", "reversal_bear", 1.09900, "reversal", "LOGIC1", "5m")
    time.sleep(3)
    
    # Final Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nSUCCESS: ALL TESTS PASSED - Bot is fully functional!")
    else:
        print(f"\nWARNING: {total - passed} test(s) failed - Review results above")

if __name__ == "__main__":
    main()

