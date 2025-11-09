"""
Send Test Signals to Bot
Tests complete bot functionality with real signals
"""
import requests
import json
import time
import sys
import os
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

BASE_URL = "http://localhost:5000"

def send_signal(symbol, signal, price, signal_type="entry", strategy="LOGIC1"):
    """Send signal to bot"""
    signal_data = {
        "symbol": symbol,
        "signal": signal,
        "price": price,
        "type": signal_type,
        "strategy": strategy,
        "tf": "5m" if signal_type == "entry" else "15m",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        print(f"\nSending {signal_type} signal: {symbol} {signal.upper()} @ {price}")
        response = requests.post(
            f"{BASE_URL}/webhook",
            json=signal_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Signal accepted: {result.get('message', 'OK')}")
            return True, result
        else:
            print(f"FAILED: Signal rejected: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server. Is bot running?")
        return False, None
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False, None

def get_status():
    """Get bot status"""
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def main():
    """Send test signals"""
    print("=" * 60)
    print("TEST SIGNAL SENDER")
    print("=" * 60)
    
    # Check server
    print("\n1. Checking server status...")
    status = get_status()
    if not status:
        print("ERROR: Server is not running. Please start bot first:")
        print("   python src/main.py --port 5000")
        print("   OR")
        print("   python start_bot.py")
        return
    print("SUCCESS: Server is running")
    
    # Test 1: Fresh BUY signal (should create dual orders)
    print("\n" + "=" * 60)
    print("TEST 1: Fresh BUY Signal (Dual Order Placement)")
    print("=" * 60)
    success, result = send_signal("EURUSD", "buy", 1.10000, "entry", "LOGIC1")
    time.sleep(3)
    
    # Check status after signal
    status = get_status()
    if status:
        open_trades = status.get("open_trades", [])
        print(f"\nOpen trades after signal: {len(open_trades)}")
        for trade in open_trades:
            print(f"  - {trade.get('symbol')} {trade.get('direction', '').upper()}")
            print(f"    Order Type: {trade.get('order_type', 'N/A')}")
            print(f"    Profit Chain: {trade.get('profit_chain_id', 'N/A')}")
    
    # Test 2: Fresh SELL signal
    print("\n" + "=" * 60)
    print("TEST 2: Fresh SELL Signal (Dual Order Placement)")
    print("=" * 60)
    success, result = send_signal("GBPUSD", "sell", 1.27500, "entry", "LOGIC2")
    time.sleep(3)
    
    # Test 3: Exit signal
    print("\n" + "=" * 60)
    print("TEST 3: Exit Signal (Reversal)")
    print("=" * 60)
    success, result = send_signal("EURUSD", "reversal_bear", 1.09900, "reversal", "LOGIC1")
    time.sleep(2)
    
    # Final status
    print("\n" + "=" * 60)
    print("FINAL STATUS")
    print("=" * 60)
    status = get_status()
    if status:
        print(f"Open Trades: {len(status.get('open_trades', []))}")
        print(f"Paused: {status.get('trading_paused', False)}")
        print(f"Daily Loss: ${status.get('daily_loss', 0):.2f}")
        print(f"Lifetime Loss: ${status.get('lifetime_loss', 0):.2f}")
    
    print("\nSUCCESS: Test signals sent. Check bot logs and MT5 for order placement.")

if __name__ == "__main__":
    main()

