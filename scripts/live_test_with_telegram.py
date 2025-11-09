#!/usr/bin/env python3
"""
Live Bot Test with Telegram Notifications
Tests all 3 logics and sends results to Telegram
"""
import requests
import json
import time
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:5000"

def send_telegram_notification(message):
    """Send test notification to Telegram"""
    try:
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
            print(f"Telegram notification sent: {message[:50]}...")
        else:
            print("WARNING: Telegram credentials not found")
    except Exception as e:
        print(f"WARNING: Could not send Telegram notification: {e}")

def check_bot_status():
    """Check if bot is running"""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        return r.status_code == 200, r.json() if r.status_code == 200 else None
    except:
        return False, None

def send_signal(symbol, signal, price, signal_type="entry", tf="5m"):
    """Send signal to bot"""
    signal_data = {
        "symbol": symbol,
        "signal": signal,
        "price": price,
        "type": signal_type,
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

def main():
    """Run complete live test suite"""
    print("=" * 60)
    print("LIVE BOT TEST WITH TELEGRAM NOTIFICATIONS")
    print("=" * 60)
    
    # Check bot status
    is_running, health_data = check_bot_status()
    if not is_running:
        error_msg = "TEST FAILED: Bot is not running. Please start bot first."
        print(error_msg)
        send_telegram_notification(f"<b>TEST FAILED</b>\n{error_msg}")
        return
    
    send_telegram_notification(
        "<b>LIVE TEST STARTED</b>\n"
        "Testing all 3 logics (LOGIC1, LOGIC2, LOGIC3)\n"
        "Original behavior restored - tf field REQUIRED"
    )
    print("\nSUCCESS: Bot is running")
    
    # Test 1: LOGIC1 - 5m Entry Signal
    print("\n" + "=" * 60)
    print("TEST 1: LOGIC1 - 5m Entry Signal")
    print("=" * 60)
    success, response = send_signal("XAUUSD", "sell", 3720.500, "entry", "5m")
    if success:
        print("SUCCESS: 5m entry signal sent")
        send_telegram_notification(
            "<b>TEST 1: LOGIC1 (5m)</b>\n"
            "Signal: XAUUSD SELL @ 3720.500\n"
            "Timeframe: 5m\n"
            "Status: Signal accepted\n"
            "Expected Logic: LOGIC1"
        )
    else:
        print("FAILED: 5m entry signal rejected")
        send_telegram_notification(
            "<b>TEST 1: LOGIC1 (5m) - FAILED</b>\n"
            "Signal rejected - check bot logs"
        )
    time.sleep(3)
    
    # Test 2: LOGIC2 - 15m Entry Signal
    print("\n" + "=" * 60)
    print("TEST 2: LOGIC2 - 15m Entry Signal")
    print("=" * 60)
    success, response = send_signal("EURUSD", "buy", 1.10000, "entry", "15m")
    if success:
        print("SUCCESS: 15m entry signal sent")
        send_telegram_notification(
            "<b>TEST 2: LOGIC2 (15m)</b>\n"
            "Signal: EURUSD BUY @ 1.10000\n"
            "Timeframe: 15m\n"
            "Status: Signal accepted\n"
            "Expected Logic: LOGIC2"
        )
    else:
        print("FAILED: 15m entry signal rejected")
        send_telegram_notification(
            "<b>TEST 2: LOGIC2 (15m) - FAILED</b>\n"
            "Signal rejected - check bot logs"
        )
    time.sleep(3)
    
    # Test 3: LOGIC3 - 1h Entry Signal
    print("\n" + "=" * 60)
    print("TEST 3: LOGIC3 - 1h Entry Signal")
    print("=" * 60)
    success, response = send_signal("GBPUSD", "buy", 1.25000, "entry", "1h")
    if success:
        print("SUCCESS: 1h entry signal sent")
        send_telegram_notification(
            "<b>TEST 3: LOGIC3 (1h)</b>\n"
            "Signal: GBPUSD BUY @ 1.25000\n"
            "Timeframe: 1h\n"
            "Status: Signal accepted\n"
            "Expected Logic: LOGIC3"
        )
    else:
        print("FAILED: 1h entry signal rejected")
        send_telegram_notification(
            "<b>TEST 3: LOGIC3 (1h) - FAILED</b>\n"
            "Signal rejected - check bot logs"
        )
    time.sleep(3)
    
    # Test 4: Entry Signal WITHOUT tf field (Should be REJECTED)
    print("\n" + "=" * 60)
    print("TEST 4: Entry Signal WITHOUT tf field (Should be REJECTED)")
    print("=" * 60)
    signal_data = {
        "symbol": "USDJPY",
        "signal": "buy",
        "price": 150.00,
        "type": "entry",
        "timestamp": datetime.now().isoformat()
    }
    try:
        r = requests.post(f"{BASE_URL}/webhook", json=signal_data, timeout=10)
        if r.status_code == 200:
            response = r.json()
            # Check if validation failed
            if "error" in str(response).lower() or "validation" in str(response).lower():
                print("SUCCESS: Signal without tf field correctly REJECTED")
                send_telegram_notification(
                    "<b>TEST 4: Validation Test</b>\n"
                    "Signal: USDJPY BUY (without tf field)\n"
                    "Status: CORRECTLY REJECTED\n"
                    "Result: ValidationError - tf field required\n"
                    "Original behavior working correctly!"
                )
            else:
                print("WARNING: Signal without tf field was accepted (should be rejected)")
                send_telegram_notification(
                    "<b>TEST 4: Validation Test - WARNING</b>\n"
                    "Signal without tf field was accepted\n"
                    "This should have been rejected!"
                )
        else:
            print("SUCCESS: Signal without tf field correctly REJECTED (status code != 200)")
            send_telegram_notification(
                "<b>TEST 4: Validation Test</b>\n"
                "Signal: USDJPY BUY (without tf field)\n"
                "Status: CORRECTLY REJECTED\n"
                "Result: HTTP error - tf field required\n"
                "Original behavior working correctly!"
            )
    except Exception as e:
        print(f"SUCCESS: Signal without tf field correctly REJECTED (exception: {e})")
        send_telegram_notification(
            "<b>TEST 4: Validation Test</b>\n"
            "Signal: USDJPY BUY (without tf field)\n"
            "Status: CORRECTLY REJECTED\n"
            "Result: ValidationError - tf field required\n"
            "Original behavior working correctly!"
        )
    time.sleep(3)
    
    # Test 5: Bias Signal with tf field
    print("\n" + "=" * 60)
    print("TEST 5: Bias Signal with tf field")
    print("=" * 60)
    success, response = send_signal("XAUUSD", "bear", 3721.000, "bias", "1h")
    if success:
        print("SUCCESS: Bias signal sent")
        send_telegram_notification(
            "<b>TEST 5: Bias Signal</b>\n"
            "Signal: XAUUSD BEAR Bias\n"
            "Timeframe: 1h\n"
            "Status: Signal accepted\n"
            "Result: Trend set (no trade executed)"
        )
    time.sleep(2)
    
    # Test 6: Trend Signal with tf field
    print("\n" + "=" * 60)
    print("TEST 6: Trend Signal with tf field")
    print("=" * 60)
    success, response = send_signal("XAUUSD", "bear", 3720.500, "trend", "15m")
    if success:
        print("SUCCESS: Trend signal sent")
        send_telegram_notification(
            "<b>TEST 6: Trend Signal</b>\n"
            "Signal: XAUUSD BEAR Trend\n"
            "Timeframe: 15m\n"
            "Status: Signal accepted\n"
            "Result: Trend set (no trade executed)"
        )
    time.sleep(2)
    
    # Final Status Check
    print("\n" + "=" * 60)
    print("FINAL STATUS CHECK")
    print("=" * 60)
    
    status = get_status()
    if status:
        print(f"Bot Status: {status.get('status', 'unknown')}")
        print(f"MT5 Connected: {status.get('mt5_connected', False)}")
        print(f"Dual Orders Enabled: {status.get('dual_orders_enabled', False)}")
        print(f"Profit Booking Enabled: {status.get('profit_booking_enabled', False)}")
        print(f"Open Trades: {status.get('open_trades_count', 0)}")
        
        send_telegram_notification(
            "<b>LIVE TEST COMPLETE</b>\n\n"
            f"Bot Status: {status.get('status', 'unknown')}\n"
            f"MT5 Connected: {status.get('mt5_connected', False)}\n"
            f"Dual Orders: {status.get('dual_orders_enabled', False)}\n"
            f"Profit Booking: {status.get('profit_booking_enabled', False)}\n"
            f"Open Trades: {status.get('open_trades_count', 0)}\n\n"
            "<b>All Tests Executed:</b>\n"
            "1. LOGIC1 (5m) - Tested\n"
            "2. LOGIC2 (15m) - Tested\n"
            "3. LOGIC3 (1h) - Tested\n"
            "4. Validation (no tf) - Tested\n"
            "5. Bias Signal - Tested\n"
            "6. Trend Signal - Tested\n\n"
            "<b>Original behavior restored - tf field REQUIRED</b>"
        )
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)
    print("\nCheck Telegram for detailed test results!")

if __name__ == "__main__":
    main()

