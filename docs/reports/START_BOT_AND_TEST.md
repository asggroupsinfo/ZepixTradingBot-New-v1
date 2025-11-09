# BOT START AND TEST INSTRUCTIONS

## Quick Start Guide

### Step 1: Start Bot Server

**Open Terminal 1:**
```bash
cd "C:\Users\Ansh Shivaay Gupta\Downloads\ZepixTradingBot-old-v2-main\ZepixTradingBot-old-v2-main"
python main.py --port 5000
```

**Wait for:**
```
ZEPIX TRADING BOT v2.0
==================================================
Starting server on 0.0.0.0:5000
```

### Step 2: Test Server

**Open Terminal 2:**
```bash
cd "C:\Users\Ansh Shivaay Gupta\Downloads\ZepixTradingBot-old-v2-main\ZepixTradingBot-old-v2-main"
python send_test_signals.py
```

### Step 3: Check Results

**Check Terminal 1 (Bot Logs):**
- Look for "DUAL ORDER PLACED" messages
- Check for Order A and Order B creation
- Verify profit chain creation

**Check Terminal 2 (Test Results):**
- Signal acceptance status
- Open trades count
- Order details

---

## Manual Signal Testing

### Test 1: Fresh BUY Signal
```bash
curl -X POST http://localhost:5000/webhook ^
  -H "Content-Type: application/json" ^
  -d "{\"symbol\":\"EURUSD\",\"signal\":\"buy\",\"price\":1.10000,\"type\":\"entry\",\"strategy\":\"LOGIC1\"}"
```

### Test 2: Fresh SELL Signal
```bash
curl -X POST http://localhost:5000/webhook ^
  -H "Content-Type: application/json" ^
  -d "{\"symbol\":\"GBPUSD\",\"signal\":\"sell\",\"price\":1.27500,\"type\":\"entry\",\"strategy\":\"LOGIC2\"}"
```

### Test 3: Exit Signal
```bash
curl -X POST http://localhost:5000/webhook ^
  -H "Content-Type: application/json" ^
  -d "{\"symbol\":\"EURUSD\",\"signal\":\"reversal_bear\",\"price\":1.09900,\"type\":\"reversal\",\"strategy\":\"LOGIC1\"}"
```

---

## Check Bot Status

```bash
curl http://localhost:5000/status
```

**Expected Response:**
```json
{
  "status": "running",
  "open_trades_count": 2,
  "dual_orders_enabled": true,
  "profit_booking_enabled": true,
  "mt5_connected": false,
  "simulation_mode": true
}
```

---

## What to Check

### ✅ Working Features
1. Server starts on port 5000
2. Signals received and processed
3. Dual orders created (Order A + Order B)
4. Profit chains created for Order B
5. Orders tracked in database
6. Telegram notifications sent
7. Price monitoring active

### ⚠️ Requires MT5
1. Actual order placement in MT5
2. Real-time price updates
3. Live PnL calculation
4. Profit target monitoring

---

## Test Report Template

After testing, note:
- ✅ What worked
- ❌ What didn't work
- ⚠️ What requires MT5 connection
- 📝 Any errors or issues

---

**Ready for Testing!**

