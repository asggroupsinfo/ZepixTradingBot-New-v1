# FINAL BOT TEST INSTRUCTIONS

## Bot Status: ✅ READY FOR TESTING

All fixes have been applied:
- ✅ Port conflict handling added
- ✅ .env file created with credentials
- ✅ Unicode errors fixed
- ✅ MT5 connection improved
- ✅ Telegram error handling added
- ✅ All features implemented

---

## STEP 1: Start Bot Server

**Open Terminal 1:**
```powershell
cd "C:\Users\Ansh Shivaay Gupta\Downloads\ZepixTradingBot-old-v2-main\ZepixTradingBot-old-v2-main"
python main.py --host 0.0.0.0 --port 5000
```

**Wait for:**
```
INFO:     Uvicorn running on http://0.0.0.0:5000
SUCCESS: MT5 connection established
SUCCESS: Telegram bot polling started
```

---

## STEP 2: Run Complete Tests

**Open Terminal 2:**
```powershell
cd "C:\Users\Ansh Shivaay Gupta\Downloads\ZepixTradingBot-old-v2-main\ZepixTradingBot-old-v2-main"
python send_test_signals.py
```

**OR use comprehensive test:**
```powershell
python test_complete_bot.py
```

---

## TEST CHECKLIST

### ✅ Existing Features to Test

1. **Signal Receiving**
   - [ ] BUY signal accepted
   - [ ] SELL signal accepted
   - [ ] Exit signal accepted
   - [ ] Reversal signal accepted

2. **Order Placement**
   - [ ] Orders placed in MT5 (if connected)
   - [ ] Orders tracked in database
   - [ ] Order details stored correctly

3. **Re-entry Systems**
   - [ ] SL hunt re-entry works
   - [ ] TP continuation re-entry works
   - [ ] Exit continuation re-entry works

4. **Risk Management**
   - [ ] Risk validation works
   - [ ] Lot size calculation correct
   - [ ] Daily/lifetime loss limits enforced

5. **Telegram Notifications**
   - [ ] Startup message received
   - [ ] Trade notifications received
   - [ ] Error notifications received

### ✅ New Features to Test

1. **Dual Order System**
   - [ ] Order A (TP Trail) placed
   - [ ] Order B (Profit Trail) placed
   - [ ] Both orders use same lot size
   - [ ] Orders tracked independently

2. **Profit Booking Chain**
   - [ ] Profit chain created for Order B
   - [ ] Chain tracked in database
   - [ ] Chain status: ACTIVE
   - [ ] Profit target monitoring active

3. **Combined PnL Calculation**
   - [ ] PnL calculated for profit chains
   - [ ] Profit target monitoring works
   - [ ] Chain progression ready

4. **Exit Signal Handling**
   - [ ] Profit chains stopped on exit signal
   - [ ] All orders in chain closed
   - [ ] Chain status updated to STOPPED

---

## EXPECTED TEST RESULTS

### Test 1: BUY Signal
- **Signal**: `{"symbol": "EURUSD", "signal": "buy", "price": 1.10000, "type": "entry", "strategy": "LOGIC1", "tf": "5m"}`
- **Expected**: 
  - Status: `success`
  - 2 orders created (Order A + Order B)
  - 1 profit chain created

### Test 2: SELL Signal
- **Signal**: `{"symbol": "GBPUSD", "signal": "sell", "price": 1.27500, "type": "entry", "strategy": "LOGIC2", "tf": "15m"}`
- **Expected**:
  - Status: `success`
  - 2 orders created (Order A + Order B)
  - 1 profit chain created

### Test 3: Exit Signal
- **Signal**: `{"symbol": "EURUSD", "signal": "reversal_bear", "price": 1.09900, "type": "reversal", "strategy": "LOGIC1", "tf": "5m"}`
- **Expected**:
  - Status: `success`
  - EURUSD trades closed
  - Profit chains stopped

---

## VERIFICATION COMMANDS

### Check Bot Status
```powershell
python -c "import requests; r = requests.get('http://localhost:5000/status'); print(r.json())"
```

### Check Open Trades
```powershell
python -c "import requests; r = requests.get('http://localhost:5000/status'); data = r.json(); print(f'Open Trades: {data.get(\"open_trades_count\", 0)}'); [print(f'  - {t.get(\"symbol\")} {t.get(\"direction\")} Type: {t.get(\"order_type\")}') for t in data.get('open_trades', [])]"
```

### Check Profit Chains (Database)
```powershell
python -c "import sqlite3; conn = sqlite3.connect('trading_bot.db'); cursor = conn.cursor(); cursor.execute('SELECT chain_id, symbol, current_level, status FROM profit_booking_chains WHERE status=\"ACTIVE\"'); print('Active Profit Chains:'); [print(f'  {row}') for row in cursor.fetchall()]; conn.close()"
```

---

## TROUBLESHOOTING

### Bot Not Starting
1. Check port 5000 is free: `netstat -ano | findstr :5000`
2. Kill process if needed: `taskkill /F /PID <process_id>`
3. Check .env file exists and has credentials
4. Check MT5 terminal is running (if live trading)

### Signals Rejected
1. Check signal format matches requirements
2. Check `tf` field is included: `"5m"`, `"15m"`, `"1h"`, or `"1d"`
3. Check signal type matches: `"entry"` → `"buy"`/`"sell"`, `"reversal"` → `"reversal_bull"`/`"reversal_bear"`

### Orders Not Placed
1. Check MT5 connection status
2. Check risk validation passed
3. Check bot logs for errors
4. Check database for order records

---

## SUCCESS CRITERIA

✅ **Bot is 100% working if:**
1. Bot starts without errors
2. Signals are accepted and processed
3. Dual orders are placed correctly
4. Profit chains are created
5. Re-entry systems work
6. Exit signals work correctly
7. Telegram notifications sent
8. Database tracking correct

---

**Report Generated**: 2024-01-XX
**Status**: ✅ READY FOR TESTING
**Next Step**: Start bot and run tests

