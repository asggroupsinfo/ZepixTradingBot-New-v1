# BOT DEPLOYMENT INSTRUCTIONS

## Server Deployment on Port 5000

### Step 1: Start the Bot Server

**Option 1: Using main.py (Recommended)**
```bash
python main.py --port 5000
```

**Option 2: Using start_bot.py**
```bash
python start_bot.py
```

### Step 2: Verify Server is Running

Open browser or use curl:
```
http://localhost:5000/health
http://localhost:5000/status
```

### Step 3: Test with Signals

**Using send_test_signals.py:**
```bash
python send_test_signals.py
```

**Or manually send POST request:**
```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "EURUSD",
    "signal": "buy",
    "price": 1.10000,
    "type": "entry",
    "strategy": "LOGIC1"
  }'
```

## Webhook Endpoint

**URL**: `http://localhost:5000/webhook`
**Method**: POST
**Content-Type**: application/json

### Signal Format:
```json
{
  "symbol": "EURUSD",
  "signal": "buy",
  "price": 1.10000,
  "type": "entry",
  "strategy": "LOGIC1",
  "tf": "5m"
}
```

## Testing Checklist

1. ✅ Server starts on port 5000
2. ✅ Health endpoint responds
3. ✅ Status endpoint shows bot state
4. ✅ Webhook receives signals
5. ✅ Dual orders created (Order A + Order B)
6. ✅ Profit chains created for Order B
7. ✅ Orders tracked in database
8. ✅ Telegram notifications sent
9. ✅ Price monitoring active
10. ✅ Exit signals handled

## Important Notes

- **MT5 Connection**: For live trading, ensure MT5 is connected
- **Simulation Mode**: If MT5 not connected, bot runs in simulation mode
- **Port**: Default port is 5000 (can be changed with --port argument)
- **Logs**: Check console output for detailed logs

