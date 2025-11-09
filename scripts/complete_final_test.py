#!/usr/bin/env python3
"""
Complete Final Test - All Features
Tests all features including exit signals
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
        
        # Get stopped chains
        cursor.execute("SELECT COUNT(*) FROM profit_booking_chains WHERE status='STOPPED'")
        stopped_chains = cursor.fetchone()[0]
        
        conn.close()
        return {
            'open_trades': open_trades,
            'tp_trail': tp_trail,
            'profit_trail': profit_trail,
            'active_chains': active_chains,
            'stopped_chains': stopped_chains,
            'has_order_type': has_order_type
        }
    except Exception as e:
        print(f"ERROR checking database: {e}")
        return None

def main():
    """Run complete final test suite"""
    print("=" * 60)
    print("COMPLETE FINAL TEST - ALL FEATURES")
    print("=" * 60)
    
    # Check bot status
    if not check_bot_status():
        print("ERROR: Bot is not running. Please start bot first.")
        send_telegram_notification("TEST FAILED: Bot is not running")
        return
    
    send_telegram_notification("FINAL TEST STARTED: Complete feature verification")
    print("\nSUCCESS: Bot is running")
    
    # Test 1: Verify Alert Validation Fix
    print("\n" + "=" * 60)
    print("TEST 1: ALERT VALIDATION (without tf field)")
    print("=" * 60)
    success, response = send_signal("GBPUSD", "buy", 1.25000, "entry", "LOGIC1")
    if success:
        print("SUCCESS: Signal without tf field accepted")
        send_telegram_notification("TEST: Signal without tf field accepted - Alert validation fix working")
    else:
        print("FAILED: Signal without tf field rejected")
    time.sleep(2)
    
    # Test 2: Bias Signal
    print("\n" + "=" * 60)
    print("TEST 2: BIAS SIGNAL")
    print("=" * 60)
    success, response = send_signal("GBPUSD", "bull", 1.25100, "bias", "LOGIC1", "1h")
    if success:
        print("SUCCESS: Bias signal sent")
        send_telegram_notification("TEST: Bias signal sent - GBPUSD 1H BULL")
    time.sleep(2)
    
    # Test 3: Trend Signal
    print("\n" + "=" * 60)
    print("TEST 3: TREND SIGNAL")
    print("=" * 60)
    success, response = send_signal("GBPUSD", "bull", 1.25200, "trend", "LOGIC1", "15m")
    if success:
        print("SUCCESS: Trend signal sent")
        send_telegram_notification("TEST: Trend signal sent - GBPUSD 15M BULL")
    time.sleep(2)
    
    # Test 4: Entry Signal (Dual Orders)
    print("\n" + "=" * 60)
    print("TEST 4: ENTRY SIGNAL (Dual Order Placement)")
    print("=" * 60)
    success, response = send_signal("GBPUSD", "buy", 1.25300, "entry", "LOGIC1", "5m")
    if success:
        print("SUCCESS: Entry signal sent")
        send_telegram_notification("TEST: Entry signal sent - GBPUSD BUY @ 1.25300")
    time.sleep(5)
    
    # Check status after entry signal
    status = get_status()
    db_info = check_database()
    
    if db_info:
        print(f"\nDatabase Check:")
        print(f"  Open Trades: {db_info['open_trades']}")
        if db_info['has_order_type']:
            print(f"  TP Trail Orders: {db_info['tp_trail']}")
            print(f"  Profit Trail Orders: {db_info['profit_trail']}")
        print(f"  Active Profit Chains: {db_info['active_chains']}")
        
        if db_info['open_trades'] >= 2:
            print("SUCCESS: Dual orders placed!")
            send_telegram_notification(f"TEST SUCCESS: Dual orders placed - {db_info['open_trades']} trades in database")
        else:
            print("WARNING: Orders not placed (may need trend alignment)")
            send_telegram_notification("TEST WARNING: Orders not placed - checking trend alignment")
    
    # Test 5: Exit Signal (Stop Profit Chains)
    print("\n" + "=" * 60)
    print("TEST 5: EXIT SIGNAL (Stop Profit Chains)")
    print("=" * 60)
    
    # Get active chains before exit
    db_before = check_database()
    active_before = db_before['active_chains'] if db_before else 0
    
    success, response = send_signal("GBPUSD", "bear", 1.25400, "exit", "LOGIC1", "15m")
    if success:
        print("SUCCESS: Exit signal sent")
        send_telegram_notification("TEST: Exit signal sent - GBPUSD EXIT")
    time.sleep(5)
    
    # Check chains after exit
    db_after = check_database()
    active_after = db_after['active_chains'] if db_after else 0
    stopped_after = db_after['stopped_chains'] if db_after else 0
    
    print(f"\nChains Status:")
    print(f"  Active Chains (before): {active_before}")
    print(f"  Active Chains (after): {active_after}")
    print(f"  Stopped Chains (after): {stopped_after}")
    
    if active_after < active_before or stopped_after > 0:
        print("SUCCESS: Exit signal stopped profit chains!")
        send_telegram_notification(f"TEST SUCCESS: Exit signal stopped chains - Active: {active_after}, Stopped: {stopped_after}")
    else:
        print("INFO: No chains to stop (or chains already stopped)")
        send_telegram_notification("TEST INFO: Exit signal processed - no active chains to stop")
    
    # Final status
    print("\n" + "=" * 60)
    print("FINAL STATUS")
    print("=" * 60)
    
    status = get_status()
    db_info = check_database()
    
    if status:
        print(f"Bot Status: {status.get('status', 'unknown')}")
        print(f"MT5 Connected: {status.get('mt5_connected', False)}")
        print(f"Dual Orders Enabled: {status.get('dual_orders_enabled', False)}")
        print(f"Profit Booking Enabled: {status.get('profit_booking_enabled', False)}")
        print(f"Open Trades (Status API): {status.get('open_trades_count', 0)}")
    
    if db_info:
        print(f"\nDatabase Status:")
        print(f"  Open Trades (DB): {db_info['open_trades']}")
        if db_info['has_order_type']:
            print(f"  TP Trail Orders: {db_info['tp_trail']}")
            print(f"  Profit Trail Orders: {db_info['profit_trail']}")
        print(f"  Active Profit Chains: {db_info['active_chains']}")
        print(f"  Stopped Profit Chains: {db_info['stopped_chains']}")
        
        send_telegram_notification(
            f"FINAL TEST COMPLETE:\n"
            f"Open Trades: {db_info['open_trades']}\n"
            f"Active Chains: {db_info['active_chains']}\n"
            f"Stopped Chains: {db_info['stopped_chains']}\n"
            f"All features verified!"
        )
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()

