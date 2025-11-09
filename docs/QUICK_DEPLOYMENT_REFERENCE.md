# 🚀 Quick Deployment Reference - Windows VM

## ⚡ One-Click Deployment Commands

### **Standard Deployment (Port 5000 - No Admin Required)**

```powershell
.\scripts\windows_setup.bat
```

**What it does:**
- ✅ Checks Python 64-bit
- ✅ Creates virtual environment
- ✅ Installs dependencies
- ✅ Sets up MT5 connection
- ✅ Validates .env file
- ✅ Starts bot on port 5000

**Time:** 1-2 minutes

---

### **Admin Deployment (Port 80 - Admin Required)**

```powershell
# Right-click PowerShell → "Run as Administrator"
.\scripts\windows_setup_admin.bat
```

**What it does:**
- Same as standard, but runs on port 80
- Requires administrator privileges

**Time:** 1-2 minutes

---

## 📋 Pre-Deployment Checklist

Before running deployment:

- [ ] ✅ Python 3.8+ (64-bit) installed
- [ ] ✅ `.env` file created with credentials
- [ ] ✅ MetaTrader 5 installed (optional)
- [ ] ✅ Git installed (if cloning from GitHub)

---

## 🔧 .env File Template

Create `.env` file in project root:

```env
# MT5 Credentials
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server

# Telegram Bot
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## ✅ Verification Commands

**Check Bot Status:**
```powershell
# Via browser
http://localhost:5000/health

# Via Telegram
/status
```

**Check MT5 Connection:**
```powershell
# Via Telegram
/mt5_status
```

**Test Webhook:**
```powershell
curl -X POST http://localhost:5000/webhook -H "Content-Type: application/json" -d '{\"type\":\"entry\",\"symbol\":\"EURUSD\",\"signal\":\"buy\",\"tf\":\"5m\",\"price\":1.1000,\"strategy\":\"ZepixPremium\"}'
```

---

## 🐛 Quick Troubleshooting

**Python Not Found:**
- Install from [python.org](https://www.python.org/downloads/)
- Check "Add Python to PATH" during installation

**32-bit Python Error:**
- Uninstall 32-bit Python
- Install 64-bit Python

**.env File Missing:**
- Create `.env` file in project root
- Add required credentials

**MT5 Connection Failed:**
- Bot will run in simulation mode
- Install MT5 when ready for live trading

**Port Already in Use:**
```powershell
# Find process
netstat -ano | findstr :5000

# Kill process
taskkill /PID <PID> /F
```

---

## 📞 Support

**Full Documentation:**
- `docs/WINDOWS_VM_DEPLOYMENT_COMPLETE.md` - Complete guide
- `docs/DEPLOYMENT_GUIDE.md` - General deployment
- `README.md` - Project overview

**Telegram Commands:**
- `/start` - Show all commands
- `/help` - Get help

---

**Version:** 2.0
**Last Updated:** January 2025

