# 🚀 Zepix Trading Bot - Complete Windows VM Deployment Guide

## 📋 Table of Contents
1. [Bot Overview](#bot-overview)
2. [Prerequisites](#prerequisites)
3. [One-Click Deployment](#one-click-deployment)
4. [Step-by-Step Manual Deployment](#step-by-step-manual-deployment)
5. [Bot Features & Details](#bot-features--details)
6. [Configuration](#configuration)
7. [Verification & Testing](#verification--testing)
8. [Troubleshooting](#troubleshooting)

---

## 🤖 Bot Overview

**Zepix Trading Bot v2.0** is an advanced automated trading system for MetaTrader 5 (MT5) with:

- ✅ **Dual Order System**: TP Trail and Profit Trail orders
- ✅ **Profit Booking Chains**: 5-level pyramid compounding system
- ✅ **Re-entry System**: SL Hunt, TP Continuation, Exit Continuation
- ✅ **Exit Strategies**: Reversal, Exit Early Warning, Trend Reversal, Opposite Signal
- ✅ **Risk Management**: RR Ratio, Risk Tiers, Lot Sizing, Daily/Lifetime Loss Caps
- ✅ **Telegram Bot**: 50+ commands for full control
- ✅ **FastAPI Webhook**: TradingView alert integration
- ✅ **MT5 Integration**: Live trading with automatic fallback to simulation mode

---

## 📋 Prerequisites

### Required Software

1. **Windows 10/11 (64-bit)**
2. **Python 3.8+ (64-bit)** - [Download](https://www.python.org/downloads/)
   - ⚠️ **IMPORTANT**: Must be 64-bit (MetaTrader5 requires 64-bit Python)
   - During installation, check "Add Python to PATH"
3. **MetaTrader 5** (Optional - bot runs in simulation mode if unavailable)
   - Download from your broker or [MetaQuotes](https://www.metatrader5.com/)
4. **Git** (Optional - for cloning from GitHub) - [Download](https://git-scm.com/downloads)

### Required Credentials

Before deployment, prepare:

1. **MT5 Account Credentials**:
   - Account Number (Login)
   - Password
   - Server Name (e.g., "XMGlobal-MT5 6")

2. **Telegram Bot**:
   - Bot Token (from [@BotFather](https://t.me/botfather))
   - Chat ID (your Telegram user ID)

---

## 🎯 One-Click Deployment

### **Method 1: Standard Deployment (Port 5000 - No Admin Required)**

**Single Command:**
```powershell
.\scripts\windows_setup.bat
```

**What it does:**
1. ✅ Checks Python 64-bit installation
2. ✅ Creates fresh virtual environment
3. ✅ Installs all dependencies
4. ✅ Sets up MT5 connection
5. ✅ Validates .env file
6. ✅ Starts bot on port 5000

**Time:** 1-2 minutes

---

### **Method 2: Admin Deployment (Port 80 - Admin Required)**

**Single Command:**
```powershell
# Right-click PowerShell → "Run as Administrator"
.\scripts\windows_setup_admin.bat
```

**What it does:**
- Same as Method 1, but runs on port 80 (requires admin rights)
- Better for production servers

**Time:** 1-2 minutes

---

## 📝 Step-by-Step Manual Deployment

If you prefer manual setup or need to troubleshoot:

### **Step 1: Download/Clone Project**

**Option A: From GitHub**
```powershell
git clone https://github.com/asggroupsinfo/ZepixTradingBot-New-v1.git
cd ZepixTradingBot-New-v1
```

**Option B: Extract ZIP**
- Download ZIP from GitHub
- Extract to `C:\ZepixTradingBot` (or your preferred location)

---

### **Step 2: Verify Python Installation**

```powershell
# Check Python version
python --version
# Should show: Python 3.8.x or higher

# Verify 64-bit
python -c "import struct; print('64-bit' if struct.calcsize('P') * 8 == 64 else '32-bit')"
# Should show: 64-bit
```

**If Python not found:**
- Install from [python.org](https://www.python.org/downloads/)
- During installation, check "Add Python to PATH"

---

### **Step 3: Create Virtual Environment**

```powershell
# Navigate to project folder
cd C:\ZepixTradingBot-New-v1

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# You should see (venv) in your prompt
```

---

### **Step 4: Install Dependencies**

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install all dependencies
python -m pip install -r requirements.txt
```

**Time:** 1-2 minutes

---

### **Step 5: Configure .env File**

Create `.env` file in project root:

```env
# MT5 Credentials (Required for Live Trading)
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server

# Telegram Bot (Required for Notifications)
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

**Example:**
```env
MT5_LOGIN=308646228
MT5_PASSWORD=Fast@@2801@@!!!
MT5_SERVER=XMGlobal-MT5 6
TELEGRAM_TOKEN=8289959450:AAHKZ_SJWjVzbRZXLAxaJ6SLfcW1kBnA
TELEGRAM_CHAT_ID=2139792302
```

**⚠️ Important:**
- `.env` file should be in project root (same folder as `main.py`)
- Never commit `.env` to git (already in .gitignore)

---

### **Step 6: Setup MT5 Connection (Optional)**

If MT5 is installed, the bot will auto-detect it. To manually verify:

```powershell
python scripts\setup_mt5_connection.py
```

**Expected Output:**
```
✅ MT5 Connection Established
Account: 308646228
Balance: $10,226.50
```

**If MT5 not found:**
- Bot will run in **simulation mode** (safe for testing)
- Install MT5 when ready for live trading

---

### **Step 7: Start the Bot**

**Option A: Standard Port (5000)**
```powershell
python src\main.py --host 0.0.0.0 --port 5000
```

**Option B: Production Port (80 - Requires Admin)**
```powershell
# Right-click PowerShell → "Run as Administrator"
python src\main.py --host 0.0.0.0 --port 80
```

**Success Message:**
```
🤖 Trading Bot v2.0 Started Successfully!
🔧 Mode: LIVE TRADING (or SIMULATION)
📊 1:1.5 RR System Active
🔄 Re-entry System Enabled
Uvicorn running on http://0.0.0.0:5000
```

---

## 🎯 Bot Features & Details

### **1. Dual Order System**

The bot places **two orders** for each signal:

- **Order A (TP Trail)**: Takes profit at target, then trails stop loss
- **Order B (Profit Trail)**: Trails stop loss from entry, books profit at levels

**Configuration:**
- Split ratio: 50/50 (configurable)
- Independent SL/TP for each order
- Separate profit booking chains

---

### **2. Profit Booking Chains**

**5-Level Pyramid System:**

1. **Level 1**: 25% of Order B at +10 pips
2. **Level 2**: 25% of remaining at +20 pips
3. **Level 3**: 25% of remaining at +30 pips
4. **Level 4**: 25% of remaining at +40 pips
5. **Level 5**: Remaining at +50 pips

**Features:**
- Automatic profit booking
- Compounding effect
- Configurable targets per symbol

---

### **3. Re-entry System**

**Three Types of Re-entries:**

1. **SL Hunt Re-entry**: Re-enters after stop loss hit
2. **TP Continuation Re-entry**: Re-enters after take profit hit
3. **Exit Continuation Re-entry**: Re-enters after exit signal

**Safety Features:**
- Maximum 3 re-entries per chain
- Cooldown period between re-entries
- Risk validation before each re-entry

---

### **4. Exit Strategies**

**Four Exit Methods:**

1. **Reversal Exit**: Exits on opposite signal
2. **Exit Early Warning**: Exits on early exit signal
3. **Trend Reversal**: Exits on trend change
4. **Opposite Signal**: Exits on opposite bias

---

### **5. Risk Management**

**Features:**
- **RR Ratio**: 1:1.5 minimum (configurable)
- **Risk Tiers**: Account-based lot sizing
- **Daily Loss Cap**: Configurable daily loss limit
- **Lifetime Loss Cap**: Configurable lifetime loss limit
- **Lot Sizing**: Automatic based on account size and volatility

**Risk Tiers:**
- $5,000: 0.05 lot
- $10,000: 0.10 lot
- $25,000: 0.20 lot
- $50,000: 0.50 lot
- $100,000+: 1.00 lot

---

### **6. Telegram Bot Commands**

**50+ Commands Available:**

**Basic Commands:**
- `/start` - Show all commands
- `/status` - Bot status
- `/health` - Health check

**Risk Management:**
- `/view_risk_caps` - View daily/lifetime caps
- `/set_daily_cap [amount]` - Set daily loss cap
- `/set_lifetime_cap [amount]` - Set lifetime loss cap
- `/clear_daily_loss` - Reset daily loss
- `/clear_loss_data` - Reset lifetime loss

**Lot Management:**
- `/lot_size_status` - View lot settings
- `/set_lot_size TIER LOT` - Override lot size

**Trading Control:**
- `/toggle_trading` - Enable/disable trading
- `/view_positions` - View open positions
- `/close_all` - Close all positions

**Profit Booking:**
- `/profit_status` - View profit chains
- `/profit_stats` - Profit statistics
- `/toggle_profit_booking` - Enable/disable profit booking

**Dual Orders:**
- `/dual_order_status` - View dual order settings
- `/toggle_dual_orders` - Enable/disable dual orders
- `/set_split_ratio [ratio]` - Set order split ratio

**Full list:** Use `/start` in Telegram to see all commands

---

### **7. TradingView Integration**

**Webhook Endpoint:**
```
POST http://your-vm-ip:5000/webhook
```

**Alert JSON Format:**
```json
{
  "type": "entry",
  "symbol": "EURUSD",
  "signal": "buy",
  "tf": "5m",
  "price": 1.1000,
  "strategy": "ZepixPremium"
}
```

**Supported Signals:**
- `entry` - New trade entry
- `exit` - Exit existing position
- `reversal` - Reversal signal
- `bias` - Trend bias update

---

## ⚙️ Configuration

### **Main Config File: `config/config.json`**

**Key Settings:**
```json
{
  "dual_order_config": {
    "enabled": true,
    "split_ratio": 0.5
  },
  "profit_booking_config": {
    "enabled": true,
    "levels": 5
  },
  "risk_management": {
    "min_rr_ratio": 1.5,
    "daily_loss_cap": 400,
    "lifetime_loss_cap": 2000
  }
}
```

---

## ✅ Verification & Testing

### **1. Check Bot Status**

**Via Telegram:**
```
/status
```

**Via Browser:**
```
http://localhost:5000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "mt5_connected": true,
  "mode": "live_trading"
}
```

---

### **2. Test MT5 Connection**

**Via Telegram:**
```
/mt5_status
```

**Expected Response:**
```
✅ MT5 Connected
Account: 308646228
Balance: $10,226.50
Server: XMGlobal-MT5 6
```

---

### **3. Test TradingView Webhook**

**Send Test Alert:**
```powershell
curl -X POST http://localhost:5000/webhook -H "Content-Type: application/json" -d '{\"type\":\"entry\",\"symbol\":\"EURUSD\",\"signal\":\"buy\",\"tf\":\"5m\",\"price\":1.1000,\"strategy\":\"ZepixPremium\"}'
```

**Expected:**
- Telegram notification received
- Order placed (if in live mode)
- Position visible in MT5

---

### **4. Run Test Suite**

```powershell
python scripts\run_all_tests.py
```

**Expected:**
- All tests pass
- No errors

---

## 🐛 Troubleshooting

### **Issue 1: Python Not Found**

**Error:**
```
'python' is not recognized as an internal or external command
```

**Solution:**
1. Install Python from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Restart PowerShell

---

### **Issue 2: 32-bit Python Detected**

**Error:**
```
❌ ERROR: 32-bit Python detected! MetaTrader5 requires 64-bit Python
```

**Solution:**
1. Uninstall 32-bit Python
2. Download 64-bit Python from [python.org](https://www.python.org/downloads/)
3. Install 64-bit version
4. Restart PowerShell

---

### **Issue 3: .env File Not Found**

**Error:**
```
❌ ERROR: .env file not found!
```

**Solution:**
1. Create `.env` file in project root
2. Add required credentials (see Step 5)
3. Save file

---

### **Issue 4: MT5 Connection Failed**

**Error:**
```
❌ MT5 Connection Failed
```

**Solution:**
1. Verify MT5 is installed
2. Open MT5 and login manually
3. Verify credentials in `.env` file
4. Check server name (case-sensitive)
5. Bot will run in simulation mode if MT5 unavailable

---

### **Issue 5: Port Already in Use**

**Error:**
```
Address already in use
```

**Solution:**
```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill process (replace <PID> with actual process ID)
taskkill /PID <PID> /F

# Or use different port
python src\main.py --port 5001
```

---

### **Issue 6: Dependencies Installation Failed**

**Error:**
```
ERROR: Failed to install dependencies
```

**Solution:**
```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Clear pip cache
python -m pip cache purge

# Try again
python -m pip install -r requirements.txt
```

---

## 📊 Deployment Checklist

Before going live:

- [ ] ✅ Python 64-bit installed
- [ ] ✅ Virtual environment created
- [ ] ✅ Dependencies installed
- [ ] ✅ `.env` file configured
- [ ] ✅ MT5 installed and tested
- [ ] ✅ Bot starts successfully
- [ ] ✅ Telegram bot responds
- [ ] ✅ MT5 connection verified
- [ ] ✅ Test webhook received
- [ ] ✅ Risk caps configured
- [ ] ✅ Lot sizes verified

---

## 🎉 Success Indicators

You'll know deployment succeeded when:

1. ✅ Bot starts without errors
2. ✅ Telegram notification received: "🤖 Trading Bot v2.0 Started Successfully!"
3. ✅ Health check returns: `{"status": "healthy"}`
4. ✅ MT5 status shows connected
5. ✅ Test webhook processes successfully

---

## 📞 Support

**For Issues:**
1. Check logs in PowerShell console
2. Review Telegram bot messages
3. Verify `.env` configuration
4. Check MT5 connection status
5. Review `docs/` folder for detailed guides

---

## 📝 Quick Reference

**Start Bot (Port 5000):**
```powershell
.\scripts\windows_setup.bat
```

**Start Bot (Port 80 - Admin):**
```powershell
.\scripts\windows_setup_admin.bat
```

**Manual Start:**
```powershell
python src\main.py --host 0.0.0.0 --port 5000
```

**Check Status:**
```
http://localhost:5000/health
```

**Telegram Commands:**
```
/start - Show all commands
/status - Bot status
```

---

**Last Updated:** January 2025
**Version:** 2.0
**Status:** ✅ Production Ready

