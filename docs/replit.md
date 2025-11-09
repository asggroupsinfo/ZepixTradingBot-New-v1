# Zepix Automated Trading Bot v2.0

## Recent Updates

### October 10, 2025 - DUAL SL SYSTEM + CRITICAL GOLD PIP FIX ✅
**PRODUCTION-READY: Dual Volatility-Based Dynamic SL System with Accurate Risk Management**
- ✅ **CRITICAL BUG FIX**: Fixed Gold pip calculation (line 66: `lot_size * 100` → `lot_size * 1`) - now calculates accurate P&L for XAUUSD
- ✅ **Dual SL System Implemented**: 
  - **SL-1 ORIGINAL**: Wide SLs for conservative risk (XAUUSD $10k = 1500 pips, EURUSD $10k = 150 pips)
  - **SL-2 RECOMMENDED**: Tight SLs for aggressive trading (XAUUSD $10k = 800 pips, EURUSD $10k = 100 pips)
  - 100 configurations total (10 symbols × 5 account tiers × 2 systems)
- ✅ **Dynamic SL Reduction**: Per-symbol reduction support (5-50%) - reduce SL for specific symbols without affecting others
- ✅ **Pre-Trade Validation**: Automatic verification that expected loss matches risk cap (10% tolerance) before trade execution
- ✅ **SL Hunting Integration**: Updated to use active SL system with reductions for accurate hunt detection
- ✅ **Chain Metadata Tracking**: ReEntryChain now stores `sl_system_used`, `sl_reduction_percent`, `original_sl_pips`, `applied_sl_pips`
- ✅ **Telegram Control - 8 NEW Commands** (55 total now):
  - **⚙️ SL SYSTEM CONTROL**: `/sl_status`, `/sl_system_change [sl-1/sl-2]`, `/sl_system_on [sl-1/sl-2]`, `/complete_sl_system_off`
  - **Updated**: `/view_sl_config` (shows active system + reductions), `/set_symbol_sl SYMBOL PERCENT` (reduce by %)
  - **New**: `/reset_symbol_sl SYMBOL`, `/reset_all_sl`
  - **Removed**: `/update_volatility` (deprecated, replaced by dual SL system)
- ✅ **Comprehensive Testing**: 
  - 100/100 SL calculations passed (50 SL-1 + 50 SL-2 across all symbols/tiers)
  - 3/3 metadata regression tests passed
  - Zero LSP errors confirmed
- ✅ **Architect Approved**: Production-ready for Windows MT5 deployment with accurate risk management

**Test Results**: All systems validated - SL-1, SL-2, reduction, switching, metadata, and Gold pip fix verified working correctly

### October 09, 2025 - EXIT CONTINUATION SYSTEM COMPLETE ✅
**NEW FEATURE: Exit Continuation Monitoring (All Requirements Met)**
- ✅ **Exit Continuation System**: After Exit Appeared/Reversal/Trend Reversal/Opposite Signal → Profit book → Continue monitoring (30s) → Price gap check (2 pips) → Alignment validation → Auto re-entry if conditions met → TP system continues
- ✅ **Telegram Control**: Added `/exit_continuation [on/off/status]` command (47 total commands now)
- ✅ **Price Monitor Enhanced**: Added exit_continuation_pending tracking, _check_exit_continuation_reentries() method
- ✅ **Reversal Handler Updated**: Registers continuation monitoring for EXIT_APPEARED, TREND_REVERSAL, REVERSAL_, OPPOSITE_SIGNAL
- ✅ **Config Updated**: Added exit_continuation_enabled flag (enabled by default)
- ✅ **Architect Approved**: Pass - correctly integrated, no regressions, production ready

**Total Features**: 18 alerts, 3 logics, 3 re-entry systems (SL Hunt, TP Continuation, Exit Continuation), 4 exit systems, 47 Telegram commands

### October 08, 2025 - PRODUCTION READY VERIFICATION COMPLETE ✅
**COMPREHENSIVE TESTING: 41/41 TESTS PASSED (100%)**
- ✅ **Complete feature verification**: All 18 alerts, 3 trading logics, re-entry systems, exit systems tested
- ✅ **Architect approved**: Zero blocking defects, ready for Windows VM live trading
- ✅ **Telegram control**: 46 commands verified (runtime config without restart)
- ✅ **Risk management**: 1:1.5 RR, 5 tiers, daily/lifetime caps working
- ✅ **Database & persistence**: SQLite, config.json, stats.json verified
- ✅ **Deployment ready**: windows_setup_admin.bat, requirements locked (MT5 5.0.5328, numpy 1.26.4, pydantic 2.5.0)

**Test Report**: See PRODUCTION_READY_SUMMARY.md for detailed verification

### October 08, 2025 - Exit Appeared Alert Support + TP Continuation Optimization ✅
**NEW EARLY WARNING SYSTEM FOR TRADE PROTECTION:**
- ✅ **Exit Appeared alerts**: Added support for 'exit' type alerts (6 new alerts: 5M/15M/1H Bull/Bear Exit Appeared)
  - Bullish Exit Appeared closes all SELL trades before SL hits
  - Bearish Exit Appeared closes all BUY trades before SL hits
  - Exit reason logged: "EXIT_APPEARED_BULLISH/BEARISH"
- ✅ **TP Continuation optimization**: Now automatically stops TP continuation monitoring when opposite signal/trend received
  - Prevents resource waste on stale trade monitoring
  - Clean shutdown with proper logging
- ✅ **Architect approved**: All changes verified, zero breaking changes to existing features

**Total TradingView Alerts:** 18 (4 bias + 4 trend + 6 entry + 4 reversal + 6 exit appeared)

### October 08, 2025 - Production Deployment System Complete ✅
**ZERO-INTERACTION WINDOWS DEPLOYMENT ACHIEVED:**
- ✅ **Automated deployment scripts**: `windows_setup.bat` (port 5000, no admin) and `windows_setup_admin.bat` (port 80, admin required) - fully unattended execution
- ✅ **Dependency issues permanently resolved**: All versions locked in requirements.txt (numpy==1.26.4, pydantic==2.5.0, MetaTrader5==5.0.5328)
- ✅ **MT5 auto-detection system**: `setup_mt5_connection.py` intelligently finds MT5 across 7 common paths (XM Global, standard installs) and creates symlink automatically
- ✅ **Robust simulation fallback**: Bot gracefully handles MT5 failures by auto-enabling simulation mode with proper retry logic (no crashes)
- ✅ **Architect approved**: All 4 production-readiness tasks verified for deployment

**Future Deployments:** Simply run `git pull` → `.\windows_setup_admin.bat` → Bot running on port 80 in 1-2 minutes with ZERO manual fixes

## Overview
Zepix is an automated Forex and Gold trading bot designed for integration with MetaTrader 5 (MT5) and TradingView. Its primary purpose is to execute trades based on webhook signals from TradingView, incorporating advanced risk management, sophisticated re-entry strategies, and real-time Telegram notifications. The project aims to provide a robust, automated trading solution with high customizability and control, enabling users to manage trading operations efficiently and respond to market dynamics.

## User Preferences
- **Development Mode**: Currently running in simulation mode on Replit
- **Production Deployment**: Requires Windows environment with MT5 installed
- **Webhook Integration**: Designed to receive signals from TradingView/Zepix

## System Architecture

### Core Components
The bot is built around a modular architecture comprising several key components:
- **FastAPI Server (`main.py`)**: Entry point for webhooks and API endpoints.
- **Trading Orchestration (`trading_engine.py`)**: Manages core trading logic.
- **Risk Management (`risk_manager.py`)**: Handles risk assessment and loss tracking.
- **MT5 Integration (`mt5_client.py`)**: Interface for MetaTrader 5, supporting simulation on Linux and live trading on Windows.
- **Telegram Bot (`telegram_bot.py`)**: Provides a control and notification interface.
- **Alert Processing (`alert_processor.py`)**: Validates incoming TradingView alerts.
- **Database (`database.py`)**: SQLite for persisting trade history and system state.
- **Re-entry System (`reentry_manager.py`, `price_monitor_service.py`, `reversal_exit_handler.py`)**: Implements advanced re-entry strategies including SL Hunt and TP Continuation, alongside reversal exits, with a background price monitor.
- **Trend Analysis (`timeframe_trend_manager.py`)**: Supports multi-timeframe trend validation.

### UI/UX Decisions
The primary user interface is a Telegram bot, offering extensive runtime configuration control via over 15 commands. This allows for dynamic adjustment of trading parameters, re-entry settings, risk caps, and more, without requiring a bot restart. The Telegram interface is designed for clarity with organized categories and emoji headers.

### Technical Implementations
- **Runtime Configuration Control**: Over 15 Telegram commands enable live modification of bot settings (e.g., `/simulation_mode`, `/set_monitor_interval`, `/set_daily_cap`). Changes are auto-saved to `config.json` and include input validation.
- **Advanced Re-entry System v2.0**:
    - **SL Hunt Re-entry**: Automated re-entry when price approaches SL, with alignment checks.
    - **TP Continuation Re-entry**: Chained re-entry system after Take Profit hits, featuring progressive 50% Stop Loss reduction. Auto-stops when opposite signal received.
    - **Reversal Exit Handler**: Immediate profit booking upon receiving reversal or opposite signals.
    - **Exit Appeared Early Warning**: Closes trades before SL hits when Exit Appeared alerts received (Bullish Exit = close SELL, Bearish Exit = close BUY).
    - **Background Price Monitoring**: An AsyncIO service (`PriceMonitorService`) independently monitors prices every 30 seconds.
- **Risk Management**: Features fixed lot sizes based on balance, daily and lifetime loss limits, and symbol-specific SL configurations with volatility updates.
- **Security & Compatibility**: Sensitive credentials are managed via environment variables. The bot supports a simulation mode for Linux environments (like Replit) and requires a Windows environment for live MT5 trading.
- **PnL Calculation**: Correctly uses symbol-specific pip values to prevent calculation errors.

### Feature Specifications
- **Trading Strategies**: Supports multiple distinct trading logics (Logic1, Logic2, Logic3) that can be individually toggled.
- **Symbol Mapping**: Configurable symbol mapping to support broker-specific symbol conventions (e.g., XAUUSD to GOLD).
- **Database**: Uses SQLite for comprehensive trade history, re-entry chain management, performance reporting, and system state persistence.

## External Dependencies

- **MetaTrader 5 (MT5)**: The primary trading platform integration. Used for executing trades and retrieving market data.
- **TradingView Webhooks**: Receives trading signals and alerts from TradingView.
- **Telegram Bot API**: Used for sending notifications, performance reports, and receiving control commands from users.
- **SQLite**: Utilized as the database for storing trade history, re-entry chains, system settings, and other operational data.