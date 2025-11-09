"""
Auto Deploy and Test Bot
One-click deployment and testing script
"""
import subprocess
import sys
import os
import time
import requests
import json
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

def check_server_running(port=5000, max_retries=10):
    """Check if server is running"""
    for i in range(max_retries):
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            if response.status_code == 200:
                return True
        except:
            time.sleep(2)
    return False

def start_bot_server(port=5000):
    """Start bot server"""
    print("=" * 60)
    print("STARTING BOT SERVER")
    print("=" * 60)
    
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Start server in background
    try:
        process = subprocess.Popen(
            [sys.executable, "src/main.py", "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        print(f"Bot server starting on port {port}...")
        print(f"Process ID: {process.pid}")
        
        # Wait for server to start
        print("Waiting for server to start...")
        if check_server_running(port):
            print("SUCCESS: Server is running!")
            return process
        else:
            print("ERROR: Server failed to start")
            return None
    except Exception as e:
        print(f"ERROR: Error starting server: {str(e)}")
        return None

def send_test_signal(symbol, signal, price, signal_type="entry", strategy="LOGIC1"):
    """Send test signal"""
    signal_data = {
        "symbol": symbol,
        "signal": signal,
        "price": price,
        "type": signal_type,
        "strategy": strategy,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        print(f"\nSending {signal_type} signal: {symbol} {signal.upper()} @ {price}")
        response = requests.post(
            "http://localhost:5000/webhook",
            json=signal_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Signal accepted: {result.get('message', 'OK')}")
            return True
        else:
            print(f"FAILED: Signal rejected: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def check_bot_status():
    """Check bot status"""
    try:
        response = requests.get("http://localhost:5000/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("\n" + "=" * 60)
            print("BOT STATUS")
            print("=" * 60)
            print(f"Status: {data.get('status')}")
            print(f"Open Trades: {data.get('open_trades_count', 0)}")
            print(f"Dual Orders Enabled: {data.get('dual_orders_enabled', False)}")
            print(f"Profit Booking Enabled: {data.get('profit_booking_enabled', False)}")
            print(f"MT5 Connected: {data.get('mt5_connected', False)}")
            print(f"Simulation Mode: {data.get('simulation_mode', False)}")
            
            trades = data.get('open_trades', [])
            if trades:
                print("\nOpen Trades Details:")
                for trade in trades[:5]:
                    print(f"  - {trade.get('symbol')} {trade.get('direction', '').upper()}")
                    print(f"    Order Type: {trade.get('order_type', 'N/A')}")
                    print(f"    Profit Chain: {trade.get('profit_chain_id', 'N/A')}")
            
            return True
    except Exception as e:
        print(f"ERROR: Error checking status: {str(e)}")
        return False

def main():
    """Main deployment and testing function"""
    print("=" * 60)
    print("AUTO DEPLOYMENT AND TESTING")
    print("=" * 60)
    
    # Step 1: Start server
    process = start_bot_server(5000)
    if not process:
        print("\nERROR: Failed to start server")
        return
    
    time.sleep(3)
    
    # Step 2: Check server health
    print("\n" + "=" * 60)
    print("TEST 1: Server Health Check")
    print("=" * 60)
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is healthy")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Step 3: Check bot status
    print("\n" + "=" * 60)
    print("TEST 2: Bot Status Check")
    print("=" * 60)
    check_bot_status()
    
    # Step 4: Send test signals
    print("\n" + "=" * 60)
    print("TEST 3: Sending Test Signals")
    print("=" * 60)
    
    # Test 1: Fresh BUY signal
    send_test_signal("EURUSD", "buy", 1.10000, "entry", "LOGIC1")
    time.sleep(3)
    
    # Check status after signal
    check_bot_status()
    time.sleep(2)
    
    # Test 2: Fresh SELL signal
    send_test_signal("GBPUSD", "sell", 1.27500, "entry", "LOGIC2")
    time.sleep(3)
    
    # Test 3: Exit signal
    send_test_signal("EURUSD", "reversal_bear", 1.09900, "reversal", "LOGIC1")
    time.sleep(2)
    
    # Final status check
    print("\n" + "=" * 60)
    print("FINAL STATUS")
    print("=" * 60)
    check_bot_status()
    
    print("\n" + "=" * 60)
    print("DEPLOYMENT AND TESTING COMPLETE")
    print("=" * 60)
    print("\nBot is running. Press Ctrl+C in the server window to stop.")
    print("Or close this window to continue monitoring.")

if __name__ == "__main__":
    main()

