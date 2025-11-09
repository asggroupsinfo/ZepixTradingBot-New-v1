"""
Bot Deployment Test Script
Tests bot deployment and signal processing
"""
import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

import requests
import json
import time
from datetime import datetime

# Server configuration
BASE_URL = "http://localhost:5000"

def test_server_status():
    """Test if server is running"""
    print("=" * 60)
    print("TEST 1: Server Status")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=5)
        if response.status_code == 200:
            print("[PASS] Server is running")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"[FAIL] Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[FAIL] Server is not running. Please start the bot first.")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")
        return False

def send_test_signal(symbol, signal, price, strategy="LOGIC1"):
    """Send test signal to bot"""
    signal_data = {
        "symbol": symbol,
        "signal": signal,
        "price": price,
        "type": "entry",
        "strategy": strategy,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        print(f"\n[SEND] Sending signal: {symbol} {signal.upper()} @ {price}")
        response = requests.post(
            f"{BASE_URL}/webhook",
            json=signal_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"[PASS] Signal sent successfully")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"[FAIL] Signal failed: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Error sending signal: {str(e)}")
        return False

def test_dual_order_signal():
    """Test dual order placement with fresh signal"""
    print("\n" + "=" * 60)
    print("TEST 2: Dual Order Placement (Fresh Signal)")
    print("=" * 60)
    
    # Test BUY signal
    result = send_test_signal("EURUSD", "buy", 1.10000, "LOGIC1")
    time.sleep(2)  # Wait for processing
    
    return result

def test_reentry_signal():
    """Test re-entry signal"""
    print("\n" + "=" * 60)
    print("TEST 3: Re-entry Signal")
    print("=" * 60)
    
    # Test SELL signal for re-entry
    result = send_test_signal("EURUSD", "sell", 1.09900, "LOGIC1")
    time.sleep(2)
    
    return result

def test_exit_signal():
    """Test exit signal"""
    print("\n" + "=" * 60)
    print("TEST 4: Exit Signal")
    print("=" * 60)
    
    signal_data = {
        "symbol": "EURUSD",
        "signal": "reversal_bull",
        "price": 1.10100,
        "type": "reversal",
        "strategy": "LOGIC1",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        print(f"\n[SEND] Sending exit signal: reversal_bull @ 1.10100")
        response = requests.post(
            f"{BASE_URL}/webhook",
            json=signal_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"[PASS] Exit signal sent successfully")
            return True
        else:
            print(f"[FAIL] Exit signal failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")
        return False

def check_open_trades():
    """Check open trades status"""
    print("\n" + "=" * 60)
    print("TEST 5: Check Open Trades")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            open_trades = data.get("open_trades", [])
            print(f"[PASS] Open trades count: {len(open_trades)}")
            
            for trade in open_trades:
                print(f"  - {trade.get('symbol')} {trade.get('direction').upper()} @ {trade.get('entry')}")
                print(f"    Order Type: {trade.get('order_type', 'N/A')}")
                print(f"    Profit Chain ID: {trade.get('profit_chain_id', 'N/A')}")
                print(f"    Profit Level: {trade.get('profit_level', 0)}")
            
            return True
        else:
            print(f"[FAIL] Failed to get status: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")
        return False

def main():
    """Run all deployment tests"""
    print("\n" + "=" * 60)
    print("BOT DEPLOYMENT TEST SUITE")
    print("=" * 60)
    
    # Test 1: Server status
    if not test_server_status():
        print("\n[FAIL] Server is not running. Please start the bot first:")
        print("   python main.py")
        return
    
    # Wait a bit for server to be ready
    time.sleep(1)
    
    # Test 2: Dual order placement
    test_dual_order_signal()
    time.sleep(3)
    
    # Test 3: Check open trades
    check_open_trades()
    time.sleep(2)
    
    # Test 4: Re-entry signal
    test_reentry_signal()
    time.sleep(3)
    
    # Test 5: Exit signal
    test_exit_signal()
    time.sleep(2)
    
    # Final check
    check_open_trades()
    
    print("\n" + "=" * 60)
    print("DEPLOYMENT TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()

