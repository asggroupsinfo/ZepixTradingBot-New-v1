#!/usr/bin/env python3
"""
Complete Bot Test Script with Telegram Notifications
Tests all features and sends Telegram notifications
"""
import requests
import json
import time
import sqlite3
from datetime import datetime

BASE_URL = "http://localhost:5000"

def send_telegram_notification(message):
    """Send test notification to Telegram"""
    try:
        from config import Config
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if token and chat_id:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"WARNING: Could not send Telegram notification: {e}")

def check_bot_status():
    """Check if bot is running"""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        return r.status_code == 200
    except:
        return False

def send_signal(symbol, signal, price, signal_type="entry", strategy="LOGIC1", tf="5m"):
    """Send signal to bot"""
    signal_data = {
        "symbol": symbol,
        "signal": signal,
        "price": price,
        "type": signal_type,
        "strategy": strategy,
        "tf": tf,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        r = requests.post(f"{BASE_URL}/webhook", json=signal_data, timeout=10)
        return r.status_code == 200, r.json() if r.status_code == 200 else None
    except Exception as e:
        print(f"ERROR: {e}")
        return False, None

def get_status():
    """Get bot status"""
    try:
        r = requests.get(f"{BASE_URL}/status", timeout=5)
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None

def check_database():
    """Check database for trades and chains"""
    try:
        conn = sqlite3.connect('trading_bot.db')
        cursor = conn.cursor()
        
        # Check if order_type column exists
        cursor.execute("PRAGMA table_info(trades)")
        columns = [col[1] for col in cursor.fetchall()]
        has_order_type = 'order_type' in columns
        
        # Get open trades
        cursor.execute("SELECT COUNT(*) FROM trades WHERE status='open'")
        open_trades = cursor.fetchone()[0]
        
        # Get TP trail orders (if column exists)
        tp_trail = 0
        profit_trail = 0
        if has_order_type:
            cursor.execute("SELECT COUNT(*) FROM trades WHERE order_type='TP_TRAIL' AND status='open'")
            tp_trail = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM trades WHERE order_type='PROFIT_TRAIL' AND status='open'")
            profit_trail = cursor.fetchone()[0]
        
        # Get active profit chains
        cursor.execute("SELECT COUNT(*) FROM profit_booking_chains WHERE status='ACTIVE'")
        active_chains = cursor.fetchone()[0]
        
        conn.close()
        return {
            'open_trades': open_trades,
            'tp_trail': tp_trail,
            'profit_trail': profit_trail,
            'active_chains': active_chains,
            'has_order_type': has_order_type
        }
    except Exception as e:
        print(f"ERROR checking database: {e}")
        return None

def main():
    """Run complete test suite"""
    print("=" * 60)
    print("COMPLETE BOT TEST WITH TELEGRAM NOTIFICATIONS")
    print("=" * 60)
    
    # Check bot status
    if not check_bot_status():
        print("ERROR: Bot is not running. Please start bot first.")
        send_telegram_notification("TEST FAILED: Bot is not running")
        return
    
    send_telegram_notification("TEST STARTED: Complete bot feature test")
    print("\nSUCCESS: Bot is running")
    
    # Test 1: Bias Signal (Trend Setup)
    print("\n" + "=" * 60)
    print("TEST 1: BIAS SIGNAL (Trend Setup)")
    print("=" * 60)
    success, response = send_signal("XAUUSD", "bear", 3721.405, "bias", "LOGIC1", "1h")
    if success:
        print("SUCCESS: Bias signal sent")
        send_telegram_notification("TEST: Bias signal sent - XAUUSD 1H BEAR")
    time.sleep(2)
    
    # Test 2: Trend Signal (Trend Setup)
    print("\n" + "=" * 60)
    print("TEST 2: TREND SIGNAL (Trend Setup)")
    print("=" * 60)
    success, response = send_signal("XAUUSD", "bear", 3720.500, "trend", "LOGIC1", "15m")
    if success:
        print("SUCCESS: Trend signal sent")
        send_telegram_notification("TEST: Trend signal sent - XAUUSD 15M BEAR")
    time.sleep(2)
    
    # Test 3: Entry Signal (Dual Order Placement)
    print("\n" + "=" * 60)
    print("TEST 3: ENTRY SIGNAL (Dual Order Placement)")
    print("=" * 60)
    success, response = send_signal("XAUUSD", "sell", 3719.800, "entry", "LOGIC1", "5m")
    if success:
        print("SUCCESS: Entry signal sent")
        send_telegram_notification("TEST: Entry signal sent - XAUUSD SELL @ 3719.800")
    time.sleep(5)
    
    # Check status after entry signal
    status = get_status()
    if status:
        open_trades = status.get('open_trades_count', 0)
        print(f"\nOpen Trades: {open_trades}")
        send_telegram_notification(f"TEST: After entry signal - Open Trades: {open_trades}")
        
        if open_trades >= 2:
            print("SUCCESS: Dual orders placed!")
            send_telegram_notification("TEST SUCCESS: Dual orders placed correctly!")
        else:
            print("WARNING: Orders not placed (may need trend alignment)")
            send_telegram_notification("TEST WARNING: Orders not placed - checking trend alignment")
    
    # Check database
    db_info = check_database()
    if db_info:
        print("\n" + "=" * 60)
        print("DATABASE CHECK")
        print("=" * 60)
        print(f"Open Trades (DB): {db_info['open_trades']}")
        if db_info['has_order_type']:
            print(f"TP Trail Orders (DB): {db_info['tp_trail']}")
            print(f"Profit Trail Orders (DB): {db_info['profit_trail']}")
        print(f"Active Profit Chains (DB): {db_info['active_chains']}")
        send_telegram_notification(f"TEST: Database - Open Trades: {db_info['open_trades']}, Active Chains: {db_info['active_chains']}")
    
    # Test 4: Another Entry Signal
    print("\n" + "=" * 60)
    print("TEST 4: ANOTHER ENTRY SIGNAL")
    print("=" * 60)
    success, response = send_signal("EURUSD", "buy", 1.10000, "entry", "LOGIC1", "5m")
    if success:
        print("SUCCESS: Entry signal sent")
        send_telegram_notification("TEST: Entry signal sent - EURUSD BUY @ 1.10000")
    time.sleep(5)
    
    # Final status
    status = get_status()
    if status:
        open_trades = status.get('open_trades_count', 0)
        print(f"\nFinal Open Trades: {open_trades}")
        send_telegram_notification(f"TEST: Final status - Open Trades: {open_trades}")
    
    # Final database check
    db_info = check_database()
    if db_info:
        print(f"\nFinal Database - Open Trades: {db_info['open_trades']}, Active Chains: {db_info['active_chains']}")
        send_telegram_notification(f"TEST COMPLETE: Final - Open Trades: {db_info['open_trades']}, Active Chains: {db_info['active_chains']}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    send_telegram_notification("TEST COMPLETE: All tests executed. Check results above.")

if __name__ == "__main__":
    main()

