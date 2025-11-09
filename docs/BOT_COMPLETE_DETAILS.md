# 🤖 Zepix Trading Bot v2.0 - Complete Details

## 📋 Table of Contents
1. [Bot Overview](#bot-overview)
2. [Core Features](#core-features)
3. [Trading Systems](#trading-systems)
4. [Risk Management](#risk-management)
5. [Telegram Integration](#telegram-integration)
6. [TradingView Integration](#tradingview-integration)
7. [Technical Architecture](#technical-architecture)
8. [Configuration](#configuration)

---

## 🤖 Bot Overview

**Zepix Trading Bot v2.0** is a sophisticated automated trading system designed for MetaTrader 5 (MT5) that executes trades based on TradingView alerts with advanced risk management, profit booking, and re-entry systems.

### **Key Highlights:**
- ✅ **100% Automated**: No manual intervention required
- ✅ **Dual Order System**: Two orders per signal for maximum flexibility
- ✅ **Profit Booking Chains**: 5-level pyramid compounding system
- ✅ **Re-entry System**: Automatic re-entry after SL/TP/Exit
- ✅ **Risk Management**: Daily/lifetime loss caps, RR ratio validation
- ✅ **Telegram Control**: 50+ commands for full control
- ✅ **Simulation Mode**: Safe testing without real trades

---

## 🎯 Core Features

### **1. Dual Order System**

Each trading signal places **two independent orders**:

**Order A (TP Trail):**
- Takes profit at target price
- Then trails stop loss
- Conservative approach

**Order B (Profit Trail):**
- Trails stop loss from entry
- Books profit at multiple levels
- Aggressive approach

**Benefits:**
- Diversified risk
- Multiple profit opportunities
- Independent SL/TP management

**Configuration:**
- Split ratio: 50/50 (default, configurable)
- Independent risk management
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
- Real-time monitoring

**Example:**
- Order B: 0.10 lot
- Level 1: 0.025 lot closed at +10 pips
- Level 2: 0.019 lot closed at +20 pips
- Level 3: 0.014 lot closed at +30 pips
- And so on...

---

### **3. Re-entry System**

**Three Types of Re-entries:**

#### **A. SL Hunt Re-entry**
- **Trigger**: Stop loss hit
- **Action**: Monitor price recovery
- **Re-entry**: When price reaches SL + 1 pip
- **Validation**: Logic alignment check
- **Max Re-entries**: 3 per chain

#### **B. TP Continuation Re-entry**
- **Trigger**: Take profit hit
- **Action**: Wait for 2 pip gap
- **Re-entry**: Continue trend
- **SL Reduction**: 50% per level
- **Max Levels**: 2 re-entry levels

#### **C. Exit Continuation Re-entry**
- **Trigger**: Exit signal received
- **Action**: Profit book + monitor
- **Re-entry**: If price gap + alignment valid
- **Purpose**: Continue profitable trends

**Safety Features:**
- Maximum 3 re-entries per chain
- Cooldown period between re-entries
- Risk validation before each re-entry
- Alignment check required

---

### **4. Exit Strategies**

**Four Exit Methods:**

1. **Reversal Exit**: Exits on opposite signal
2. **Exit Early Warning**: Exits on early exit signal
3. **Trend Reversal**: Exits on trend change
4. **Opposite Signal**: Exits on opposite bias

**Priority:**
- Exit Appeared (highest priority)
- Trend Reversal
- Reversal Signal
- Opposite Signal

---

## 📊 Trading Systems

### **Trading Logics (3 Strategies)**

| Logic | Bias TF | Trend TF | Entry TF | Status |
|-------|---------|----------|----------|--------|
| **Logic 1** | 1H | 15M | 5M | ✅ ENABLED |
| **Logic 2** | 1H | 15M | 15M | ✅ ENABLED |
| **Logic 3** | 1D | 1H | 1H | ✅ ENABLED |

**Alignment Check:**
- Multi-timeframe trend validation
- Required before every entry
- Ensures high-probability trades

---

### **TradingView Alerts (18 Types)**

**Bias Alerts (4):**
- 5M Bull/Bear Bias
- 15M Bull/Bear Bias
- 1H Bull/Bear Bias
- 1D Bull/Bear Bias

**Trend Alerts (4):**
- 5M Bull/Bear Trend
- 15M Bull/Bear Trend
- 1H Bull/Bear Trend
- 1D Bull/Bear Trend

**Entry Alerts (6):**
- 5M Buy/Sell Entry
- 15M Buy/Sell Entry
- 1H Buy/Sell Entry

**Reversal Alerts (4):**
- 5M Reversal Bull/Bear
- 15M Reversal Bull/Bear

**Exit Appeared Alerts (6):**
- 5M Bull/Bear Exit Appeared
- 15M Bull/Bear Exit Appeared
- 1H Bull/Bear Exit Appeared

---

## 🛡️ Risk Management

### **1. RR Ratio Validation**

- **Minimum RR**: 1:1.5 (configurable)
- **Validation**: Before every order
- **Rejection**: If RR < 1:1.5

**Example:**
- Entry: 1.1000
- SL: 1.0990 (10 pips)
- TP: 1.1015 (15 pips)
- RR: 1:1.5 ✅ Valid

---

### **2. Risk Tiers**

**Account-Based Lot Sizing:**

| Account Size | Lot Size | Risk % |
|--------------|----------|--------|
| $5,000 | 0.05 | 1% |
| $10,000 | 0.10 | 1% |
| $25,000 | 0.20 | 0.8% |
| $50,000 | 0.50 | 1% |
| $100,000+ | 1.00 | 1% |

**Features:**
- Automatic lot sizing
- Volatility-based adjustment
- Configurable per symbol

---

### **3. Loss Caps**

**Daily Loss Cap:**
- Default: $400 (configurable)
- Resets daily
- Stops trading when exceeded
- Clear via `/clear_daily_loss`

**Lifetime Loss Cap:**
- Default: $2,000 (configurable)
- Cumulative across all days
- Stops trading when exceeded
- Clear via `/clear_loss_data`

**Features:**
- Real-time monitoring
- Automatic trading halt
- Telegram notifications
- Separate tracking

---

### **4. Lot Sizing**

**Automatic Calculation:**
- Based on account size
- Volatility adjustment
- Risk percentage
- Symbol-specific

**Manual Override:**
- Via Telegram: `/set_lot_size TIER LOT`
- Per-tier configuration
- Temporary override

---

## 📱 Telegram Integration

### **50+ Commands Available**

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
- `/close_symbol SYMBOL` - Close specific symbol

**Profit Booking:**
- `/profit_status` - View profit chains
- `/profit_stats` - Profit statistics
- `/toggle_profit_booking` - Enable/disable profit booking
- `/set_profit_targets SYMBOL LEVEL1 LEVEL2 ...` - Set profit targets

**Dual Orders:**
- `/dual_order_status` - View dual order settings
- `/toggle_dual_orders` - Enable/disable dual orders
- `/set_split_ratio [ratio]` - Set order split ratio

**MT5 Status:**
- `/mt5_status` - MT5 connection status
- `/account_info` - Account information
- `/balance` - Account balance

**Re-entry System:**
- `/reentry_status` - View re-entry chains
- `/toggle_reentry` - Enable/disable re-entry
- `/reentry_stats` - Re-entry statistics

**Full list:** Use `/start` in Telegram to see all commands

---

## 📡 TradingView Integration

### **Webhook Endpoint**

```
POST http://your-vm-ip:5000/webhook
```

### **Alert JSON Format**

**Entry Alert:**
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

**Exit Alert:**
```json
{
  "type": "exit",
  "symbol": "EURUSD",
  "signal": "sell",
  "tf": "5m",
  "price": 1.1015,
  "strategy": "ZepixPremium"
}
```

**Bias Alert:**
```json
{
  "type": "bias",
  "symbol": "EURUSD",
  "signal": "bullish",
  "tf": "1h",
  "strategy": "ZepixPremium"
}
```

**Reversal Alert:**
```json
{
  "type": "reversal",
  "symbol": "EURUSD",
  "signal": "bearish",
  "tf": "5m",
  "strategy": "ZepixPremium"
}
```

---

## 🏗️ Technical Architecture

### **Folder Structure**

```
ZepixTradingBot/
├── src/                    # Core bot source code
│   ├── main.py            # FastAPI entry point
│   ├── config.py          # Configuration management
│   ├── models.py          # Data models
│   ├── database.py        # Database operations
│   ├── core/              # Core trading logic
│   │   └── trading_engine.py
│   ├── managers/          # Business logic managers
│   │   ├── risk_manager.py
│   │   ├── dual_order_manager.py
│   │   ├── profit_booking_manager.py
│   │   ├── reentry_manager.py
│   │   └── timeframe_trend_manager.py
│   ├── services/          # Background services
│   │   ├── price_monitor_service.py
│   │   ├── analytics_engine.py
│   │   └── reversal_exit_handler.py
│   ├── clients/           # External integrations
│   │   ├── mt5_client.py
│   │   └── telegram_bot.py
│   ├── processors/        # Data processors
│   │   └── alert_processor.py
│   └── utils/             # Utility functions
│       ├── pip_calculator.py
│       └── exit_strategies.py
├── tests/                 # All test files
├── scripts/               # Utility and deployment scripts
│   ├── windows_setup.bat
│   ├── windows_setup_admin.bat
│   └── setup_mt5_connection.py
├── docs/                  # All documentation
├── config/                # Configuration files
│   ├── config.json
│   ├── base_trends.json
│   └── timeframe_trends.json
├── data/                  # Data files
│   ├── trading_bot.db
│   └── stats.json
├── assets/                 # Static assets
├── .env                   # Environment variables
├── requirements.txt     # Dependencies
└── README.md            # Project overview
```

---

### **Technology Stack**

- **Python 3.8+**: Core language
- **FastAPI**: Web framework for webhooks
- **MetaTrader5**: Trading platform integration
- **SQLite**: Database for trade history
- **python-telegram-bot**: Telegram integration
- **Uvicorn**: ASGI server

---

## ⚙️ Configuration

### **Main Config: `config/config.json`**

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
  },
  "reentry_config": {
    "enabled": true,
    "max_reentries": 3,
    "cooldown_seconds": 60
  }
}
```

### **Environment Variables: `.env`**

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

## 🎯 Deployment Modes

### **Live Trading Mode**
- ✅ MT5 connected successfully
- ✅ Real trades executed
- ✅ Full risk management active
- ✅ Telegram notifications enabled

### **Simulation Mode**
- ✅ All trades simulated
- ✅ Full bot functionality maintained
- ✅ Risk management active
- ✅ Perfect for testing strategies
- ✅ Auto-enabled if MT5 unavailable

---

## 📊 Performance Metrics

**Key Metrics Tracked:**
- Total trades executed
- Win rate
- Average RR ratio
- Daily/lifetime P&L
- Profit booking statistics
- Re-entry success rate

**Access via Telegram:**
- `/stats` - Overall statistics
- `/profit_stats` - Profit booking stats
- `/reentry_stats` - Re-entry statistics

---

## 🔒 Security Features

- ✅ `.env` file never committed to git
- ✅ Credentials encrypted in memory
- ✅ Risk caps prevent excessive losses
- ✅ Validation before every trade
- ✅ Simulation mode for safe testing

---

## 📝 Version History

**v2.0 (Current):**
- ✅ Dual Order System
- ✅ Profit Booking Chains
- ✅ Re-entry System
- ✅ Complete Risk Management
- ✅ 50+ Telegram Commands
- ✅ One-Click Deployment

---

**Last Updated:** January 2025
**Status:** ✅ Production Ready
**Version:** 2.0

