# 🚀 Zepix Trading Bot - Production Deployment Guide

## ✅ **ZERO-INTERACTION DEPLOYMENT - Ready for Production**

Your trading bot now features **fully automated Windows deployment** with ZERO manual troubleshooting required.

---

## 📋 **Prerequisites**

1. **Windows 10/11** (64-bit)
2. **Python 3.8+** (64-bit) - [Download here](https://www.python.org/downloads/)
3. **MetaTrader 5** (Optional - bot runs in simulation mode if unavailable)
4. **Git** - [Download here](https://git-scm.com/downloads)

---

## 🎯 **One-Click Deployment**

### **Option 1: Standard Deployment (Port 5000 - No Admin Required)**

```bash
git clone <your-repo-url>
cd <repo-folder>
.\windows_setup.bat
```

✅ **That's it!** Bot will be running in 1-2 minutes.

### **Option 2: Admin Deployment (Port 80 - Admin Required)**

```bash
.\windows_setup_admin.bat
```

---

## 🔧 **What Happens Automatically**

1. ✅ **Python Verification**: Checks for 64-bit Python installation
2. ✅ **Clean Environment**: Creates fresh virtual environment
3. ✅ **Locked Dependencies**: Installs exact versions (numpy==1.26.4, pydantic==2.5.0, etc.)
4. ✅ **MT5 Auto-Setup**: Searches 7 common MT5 paths and creates symlink automatically
   - XM Global MT5
   - Standard MetaTrader 5 installations
   - Other broker paths
5. ✅ **.ENV Validation**: Checks for required credentials
6. ✅ **Graceful Fallback**: Enables simulation mode if MT5 unavailable

---

## 🛡️ **Built-in Safety Features**

### **Simulation Mode Fallback**
If MT5 connection fails (wrong credentials, server down, MT5 not installed):
- ✅ Bot **automatically enables simulation mode**
- ✅ **No crashes** - graceful handling with retry logic
- ✅ All trades simulated safely
- ✅ Full functionality maintained

### **Smart MT5 Detection**
The bot searches these paths automatically:
1. `C:\Program Files\XM Global MetaTrader 5\terminal64.exe`
2. `C:\Program Files\MetaTrader 5\terminal64.exe`
3. `C:\Program Files (x86)\MetaTrader 5\terminal64.exe`
4. `%APPDATA%\MetaQuotes\Terminal\*\terminal64.exe`
5. `%LOCALAPPDATA%\Programs\MetaTrader 5\terminal64.exe`
6. `D:\MetaTrader 5\terminal64.exe`
7. `E:\MetaTrader 5\terminal64.exe`

---

## 📝 **Required .env Configuration**

Create a `.env` file in the root directory:

```env
# MT5 Credentials (Required for Live Trading)
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server

# Telegram Bot (Required for Notifications)
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

**Note:** If .env is missing or incomplete, the bot will start in **simulation mode** automatically.

---

## 🔄 **Future Updates - Zero Hassle**

To update the bot to the latest version:

```bash
git pull
.\windows_setup.bat
```

✅ **That's it!** No manual dependency fixes, no troubleshooting needed.

---

## 📊 **Deployment Modes**

### **Live Trading Mode**
- ✅ MT5 connected successfully
- ✅ Real trades executed
- ✅ Full risk management active
- ✅ Telegram notifications enabled

### **Simulation Mode** (Auto-enabled when MT5 unavailable)
- ✅ All trades simulated
- ✅ Full bot functionality maintained
- ✅ Risk management active
- ✅ Perfect for testing strategies
- ✅ Switch to live mode via `windows_setup_admin.bat` when MT5 ready

---

## 🐛 **Troubleshooting** (Rarely Needed)

### **Issue: Python not found**
**Solution:** Install Python 64-bit from [python.org](https://www.python.org/downloads/)

### **Issue: .env file missing**
**Solution:** Bot automatically runs in simulation mode - create .env when ready for live trading

### **Issue: MT5 not detected**
**Solution:** Bot automatically runs in simulation mode - install MT5 when ready for live trading

### **Issue: Port 5000 already in use**
**Solution:** 
```bash
# Find and kill process using port 5000
netstat -ano | findstr :5000
taskkill /PID <process_id> /F

# Or use admin script for port 80
.\windows_setup_admin.bat
```

---

## 🎯 **Production Checklist**

Before going live with real trading:

- [ ] ✅ .env file configured with correct MT5 credentials
- [ ] ✅ MetaTrader 5 installed and tested
- [ ] ✅ Telegram bot token and chat ID configured
- [ ] ✅ Test deployment with `windows_setup.bat` first
- [ ] ✅ Verify bot connects to MT5 successfully
- [ ] ✅ Test with small trade sizes initially
- [ ] ✅ Monitor Telegram notifications
- [ ] ✅ Set up daily loss caps via Telegram `/set_daily_cap`

---

## 📞 **Support**

For issues or questions:
1. Check logs in the workflow console
2. Review Telegram bot messages for alerts
3. Verify .env configuration
4. Ensure MT5 credentials are correct

---

## 🔐 **Security Best Practices**

1. ✅ Never commit `.env` file to git (already in .gitignore)
2. ✅ Use strong passwords for MT5 account
3. ✅ Secure Telegram bot token
4. ✅ Run bot on secure, dedicated server
5. ✅ Monitor bot activity regularly via Telegram
6. ✅ Set appropriate daily/lifetime loss caps

---

## 🎉 **Success Indicators**

You'll know deployment succeeded when you see:

```
🤖 Trading Bot v2.0 Started Successfully!
🔧 Mode: LIVE TRADING (or SIMULATION)
📊 1:1.5 RR System Active
🔄 Re-entry System Enabled
```

In your Telegram chat!

---

**Deployment created:** October 08, 2025
**Status:** ✅ Production Ready - Zero-Interaction Deployment
**Architect Approved:** All 4 tasks verified
