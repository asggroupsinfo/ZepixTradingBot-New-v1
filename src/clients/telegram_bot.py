import requests
import json
import threading
import time
from typing import Dict, Any, TYPE_CHECKING
from src.config import Config
from src.managers.risk_manager import RiskManager
from src.services.analytics_engine import AnalyticsEngine
from src.managers.timeframe_trend_manager import TimeframeTrendManager

if TYPE_CHECKING:
    from src.core.trading_engine import TradingEngine

class TelegramBot:
    def __init__(self, config: Config):
        self.config = config
        self.token = config["telegram_token"]
        self.chat_id = config["telegram_chat_id"]
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        
        self.trend_manager = None
        
        self.command_handlers = {
            "/start": self.handle_start,
            "/status": self.handle_status,
            "/pause": self.handle_pause,
            "/resume": self.handle_resume,
            "/performance": self.handle_performance,
            "/stats": self.handle_stats,
            "/trades": self.handle_trades,
            "/logic1_on": self.handle_logic1_on,
            "/logic1_off": self.handle_logic1_off,
            "/logic2_on": self.handle_logic2_on,
            "/logic2_off": self.handle_logic2_off,
            "/logic3_on": self.handle_logic3_on,
            "/logic3_off": self.handle_logic3_off,
            "/logic_status": self.handle_logic_status,
            "/performance_report": self.handle_performance_report,
            "/pair_report": self.handle_pair_report,
            "/strategy_report": self.handle_strategy_report,
            # Trend commands
            "/set_trend": self.handle_set_trend,
            "/set_auto": self.handle_set_auto,
            "/show_trends": self.handle_show_trends,
            "/trend_matrix": self.handle_trend_matrix,
            "/trend_mode": self.handle_trend_mode,
            "/lot_size_status": self.handle_lot_size_status,
            "/set_lot_size": self.handle_set_lot_size,
            "/chains": self.handle_chains_status,
            "/signal_status": self.handle_signal_status,
            "/clear_loss_data": self.handle_clear_loss_data,
            "/clear_daily_loss": self.handle_clear_daily_loss,
            "/tp_system": self.handle_tp_system,
            "/sl_hunt": self.handle_sl_hunt,
            "/exit_continuation": self.handle_exit_continuation,
            "/tp_report": self.handle_tp_report,
            # New configuration commands
            "/simulation_mode": self.handle_simulation_mode,
            "/reentry_config": self.handle_reentry_config,
            "/set_monitor_interval": self.handle_set_monitor_interval,
            "/set_sl_offset": self.handle_set_sl_offset,
            "/set_cooldown": self.handle_set_cooldown,
            "/set_recovery_time": self.handle_set_recovery_time,
            "/set_max_levels": self.handle_set_max_levels,
            "/set_sl_reduction": self.handle_set_sl_reduction,
            "/reset_reentry_config": self.handle_reset_reentry_config,
            "/view_sl_config": self.handle_view_sl_config,
            "/set_symbol_sl": self.handle_set_symbol_sl,
            "/view_risk_caps": self.handle_view_risk_caps,
            "/sl_status": self.handle_sl_status,
            "/sl_system_change": self.handle_sl_system_change,
            "/sl_system_on": self.handle_sl_system_on,
            "/complete_sl_system_off": self.handle_complete_sl_system_off,
            "/reset_symbol_sl": self.handle_reset_symbol_sl,
            "/reset_all_sl": self.handle_reset_all_sl,
            "/set_daily_cap": self.handle_set_daily_cap,
            "/set_lifetime_cap": self.handle_set_lifetime_cap,
            "/set_risk_tier": self.handle_set_risk_tier,
            # Dual order commands
            "/dual_order_status": self.handle_dual_order_status,
            "/toggle_dual_orders": self.handle_toggle_dual_orders,
            # Profit booking commands
            "/profit_status": self.handle_profit_status,
            "/profit_stats": self.handle_profit_stats,
            "/toggle_profit_booking": self.handle_toggle_profit_booking,
            "/set_profit_targets": self.handle_set_profit_targets,
            "/profit_chains": self.handle_profit_chains,
            "/stop_profit_chain": self.handle_stop_profit_chain,
            "/stop_all_profit_chains": self.handle_stop_all_profit_chains,
            "/set_chain_multipliers": self.handle_set_chain_multipliers,
            "/set_sl_reductions": self.handle_set_sl_reductions,
            "/close_profit_chain": self.handle_stop_profit_chain,  # Alias for stop_profit_chain
            "/profit_config": self.handle_profit_config
        }
        self.risk_manager = None
        self.trading_engine = None
        self.analytics_engine = AnalyticsEngine()

    def set_dependencies(self, risk_manager: RiskManager, trading_engine: 'TradingEngine'):
        """Set dependent modules"""
        self.risk_manager = risk_manager
        self.trading_engine = trading_engine

    def set_trend_manager(self, trend_manager: TimeframeTrendManager):
        """Set trend manager"""
        self.trend_manager = trend_manager
        print("SUCCESS: Trend manager set in Telegram bot")

    def send_message(self, message: str):
        """Send message to Telegram"""
        if not self.token or not self.chat_id:
            print("WARNING: Telegram credentials not configured - message not sent")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return True
            else:
                print(f"WARNING: Telegram API error: Status {response.status_code}, Response: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"WARNING: Telegram API request failed: {str(e)}")
            return False
        except Exception as e:
            print(f"WARNING: Telegram send_message error: {str(e)}")
            return False

    def handle_start(self, message):
        """Handle /start command"""
        rr_ratio = self.config.get("rr_ratio", 1.0)
        re_entry = self.config.get("re_entry_config", {})
        welcome_msg = (
            "🤖 <b>Zepix Trading Bot v2.0</b>\n"
            "✅ Bot is active with enhanced features\n"
            f"📊 1:{rr_ratio} Risk-Reward System Active\n"
            "🔄 Re-entry System Enabled\n"
            "🔄 SL Hunt Re-entry System Enabled\n"
            "⚡ Live Price Advanced System Working\n\n"
            
            "<b>📊 TRADING CONTROL</b>\n"
            "/status - Bot &amp; trade status\n"
            "/pause - Pause trading\n"
            "/resume - Resume trading\n"
            "/signal_status - Live signals\n"
            "/simulation_mode [on/off] - Toggle simulation mode\n\n"
            
            "<b>📈 PERFORMANCE &amp; ANALYTICS</b>\n"
            "/performance - Trading metrics\n"
            "/stats - Risk statistics\n"
            "/trades - Open positions\n"
            "/chains - Re-entry chains\n\n"
            
            "<b>⚙️ STRATEGY CONTROL</b>\n"
            "/logic_status - View all logic status\n"
            "/logic1_on, /logic1_off - 1H+15M→5M\n"
            "/logic2_on, /logic2_off - 1H+15M→15M\n"
            "/logic3_on, /logic3_off - D+1H→1H\n\n"
            
            "<b>🔄 ADVANCED RE-ENTRY SYSTEM</b>\n"
            "/tp_system [on/off/status] - TP continuation\n"
            "/sl_hunt [on/off/status] - SL hunt re-entry\n"
            "/tp_report - 30-day re-entry stats\n"
            "/reentry_config - View all re-entry settings\n"
            "/set_monitor_interval [30-300] - Price monitor interval\n"
            "/set_sl_offset [1-5] - SL hunt offset pips\n"
            "/set_cooldown [30-300] - SL hunt cooldown\n"
            "/set_recovery_time [1-10] - Price recovery window\n"
            "/set_max_levels [1-5] - Max chain levels\n"
            "/set_sl_reduction [0.3-0.7] - SL reduction %\n"
            "/reset_reentry_config - Reset to defaults\n\n"
            
            "<b>📍 TREND MANAGEMENT</b>\n"
            "/show_trends - All trends\n"
            "/trend_matrix - Complete matrix\n"
            "/set_trend SYMBOL TF TREND - Manual trend\n"
            "/set_auto SYMBOL TF - Auto mode\n"
            "/trend_mode SYMBOL TF - Check mode\n\n"
            
            "<b>💰 RISK &amp; LOT MANAGEMENT</b>\n"
            "/view_risk_caps - Daily/Lifetime caps &amp; loss\n"
            "/set_daily_cap [amount] - Set daily limit\n"
            "/set_lifetime_cap [amount] - Set lifetime limit\n"
            "/set_risk_tier BALANCE DAILY LIFETIME - Complete tier\n"
            "/clear_loss_data - Reset lifetime loss\n"
            "/clear_daily_loss - Reset daily loss\n"
            "/lot_size_status - Lot settings\n"
            "/set_lot_size TIER LOT - Override lot size\n\n"
            
            "<b>⚙️ SL SYSTEM CONTROL</b>\n"
            "/sl_status - Active SL system &amp; reductions\n"
            "/sl_system_change [sl-1/sl-2] - Switch SL system\n"
            "/sl_system_on [sl-1/sl-2] - Enable SL system\n"
            "/complete_sl_system_off - Disable all SL\n"
            "/view_sl_config - View SL configuration\n"
            "/set_symbol_sl SYMBOL PERCENT - Reduce SL %\n"
            "/reset_symbol_sl SYMBOL - Reset symbol SL\n"
            "/reset_all_sl - Reset all SL reductions\n\n"
            
            "<b>💎 DUAL ORDER SYSTEM</b>\n"
            "/dual_order_status - Dual order system status\n"
            "/toggle_dual_orders - Enable/disable dual orders\n\n"
            
            "<b>💰 PROFIT BOOKING SYSTEM</b>\n"
            "/profit_status - Profit booking system status\n"
            "/profit_stats - Profit booking statistics\n"
            "/toggle_profit_booking - Enable/disable profit booking\n"
            "/set_profit_targets TARGETS - Set profit targets\n"
            "/profit_chains - Show active profit chains\n"
            "/stop_profit_chain CHAIN_ID - Stop specific chain\n"
            "/stop_all_profit_chains - Stop all chains\n"
            "/set_chain_multipliers MULTIPLIERS - Set order multipliers\n"
            "/set_sl_reductions REDUCTIONS - Set SL reductions\n"
            "/close_profit_chain CHAIN_ID - Close specific chain\n"
            "/profit_config - Show profit booking configuration"
        )
        self.send_message(welcome_msg)

    def handle_status(self, message):
        """Handle /status command with enhanced display"""
        if not self.trading_engine or not self.risk_manager:
            self.send_message("❌ Bot not initialized")
            return
        
        stats = self.risk_manager.get_stats()
        
        # Get current trends for major symbol
        xau_trends = self.trend_manager.get_all_trends("XAUUSD") if self.trend_manager else {}
        
        # Check logic alignments
        logic_alignments = {}
        if self.trend_manager:
            for logic in ["LOGIC1", "LOGIC2", "LOGIC3"]:
                alignment = self.trend_manager.check_logic_alignment("XAUUSD", logic)
                logic_alignments[logic] = alignment["direction"]
        
        status_msg = (
            "📊 <b>Bot Status</b>\n\n"
            f"🔸 Trading: {'⏸️ PAUSED' if self.trading_engine.is_paused else '✅ ACTIVE'}\n"
            f"🔸 Simulation: {'✅ ON' if self.config['simulate_orders'] else '❌ OFF'}\n"
            f"🔸 MT5: {'✅ Connected' if self.trading_engine.mt5_client.initialized else '❌ Disconnected'}\n"
            f"🔸 Balance: ${stats.get('account_balance', 0):.2f}\n"
            f"🔸 Lot Size: {stats.get('current_lot_size', 0.05)}\n\n"
            "<b>Current Modes (XAUUSD):</b>\n"
            f"LOGIC1: {logic_alignments.get('LOGIC1', 'NEUTRAL')}\n"
            f"LOGIC2: {logic_alignments.get('LOGIC2', 'NEUTRAL')}\n"
            f"LOGIC3: {logic_alignments.get('LOGIC3', 'NEUTRAL')}\n\n"
            "<b>Live Signals (XAUUSD):</b>\n"
            f"5min: {xau_trends.get('5m', 'NA')}\n"
            f"15min: {xau_trends.get('15m', 'NA')}\n"
            f"1H: {xau_trends.get('1h', 'NA')}\n"
            f"1D: {xau_trends.get('1d', 'NA')}"
        )
        self.send_message(status_msg)

    # NEW COMMAND: Set Auto Mode
    def handle_set_auto(self, message):
        """Set trend back to AUTO mode"""
        if not self.trend_manager:
            self.send_message("❌ Trend manager not initialized")
            return
            
        try:
            parts = message['text'].split()
            
            if len(parts) < 3:
                self.send_message(
                    "📝 <b>Usage:</b> /set_auto SYMBOL TIMEFRAME\n\n"
                    "<b>Symbols:</b> XAUUSD, EURUSD, GBPUSD, etc.\n"
                    "<b>Timeframes:</b> 5m, 15m, 1h, 1d\n\n"
                    "<b>Example:</b> /set_auto XAUUSD 1h\n"
                    "This allows TradingView signals to auto-update this trend"
                )
                return
            
            symbol = parts[1].upper()
            timeframe = parts[2].lower()
            
            valid_timeframes = ['5m', '15m', '1h', '1d']
            if timeframe not in valid_timeframes:
                self.send_message(f"❌ Invalid timeframe. Use: {', '.join(valid_timeframes)}")
                return
            
            self.trend_manager.set_auto_trend(symbol, timeframe)
            current_trend = self.trend_manager.get_trend(symbol, timeframe)
            current_mode = self.trend_manager.get_mode(symbol, timeframe)
            
            self.send_message(f"🔄 <b>Auto Mode Enabled</b>\n"
                            f"{symbol} {timeframe} → {current_trend} ({current_mode})\n"
                            f"📡 Now accepting TradingView signals")
            
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    # NEW COMMAND: Check Trend Mode
    def handle_trend_mode(self, message):
        """Check current trend mode"""
        if not self.trend_manager:
            self.send_message("❌ Trend manager not initialized")
            return
            
        try:
            parts = message['text'].split()
            
            if len(parts) < 3:
                self.send_message(
                    "📝 <b>Usage:</b> /trend_mode SYMBOL TIMEFRAME\n\n"
                    "<b>Example:</b> /trend_mode XAUUSD 1h"
                )
                return
            
            symbol = parts[1].upper()
            timeframe = parts[2].lower()
            
            current_trend = self.trend_manager.get_trend(symbol, timeframe)
            current_mode = self.trend_manager.get_mode(symbol, timeframe)
            
            mode_info = "🔄 AUTO (TradingView updates)" if current_mode == "AUTO" else "🔒 MANUAL (Locked)"
            
            self.send_message(f"📊 <b>Trend Mode</b>\n"
                            f"Symbol: {symbol}\n"
                            f"Timeframe: {timeframe}\n"
                            f"Trend: {current_trend}\n"
                            f"Mode: {mode_info}")
            
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_set_trend(self, message):
        """Handle /set_trend command - SETS MANUAL MODE"""
        if not self.trend_manager:
            self.send_message("❌ Trend manager not initialized")
            return
            
        try:
            parts = message['text'].split()
            
            if len(parts) < 4:
                self.send_message(
                    "📝 <b>Usage:</b> /set_trend SYMBOL TIMEFRAME TREND\n\n"
                    "<b>Symbols:</b> XAUUSD, EURUSD, GBPUSD, etc.\n"
                    "<b>Timeframes:</b> 5m, 15m, 1h, 1d\n"
                    "<b>Trends:</b> BULLISH, BEARISH, NEUTRAL\n\n"
                    "⚠️ <b>This sets MANUAL mode</b> - TradingView signals won't auto-update\n"
                    "Use /set_auto to allow auto updates\n\n"
                    "<b>Example:</b> /set_trend XAUUSD 1h BULLISH"
                )
                return
            
            symbol = parts[1].upper()
            timeframe = parts[2].lower()
            trend = parts[3].upper()
            
            valid_timeframes = ['5m', '15m', '1h', '1d']
            if timeframe not in valid_timeframes:
                self.send_message(f"❌ Invalid timeframe. Use: {', '.join(valid_timeframes)}")
                return
            
            if trend not in ["BULLISH", "BEARISH", "NEUTRAL"]:
                self.send_message("❌ Trend must be BULLISH, BEARISH, or NEUTRAL")
                return
            
            self.trend_manager.set_manual_trend(symbol, timeframe, trend)
            
            # Verify the trend was set
            current_trend = self.trend_manager.get_trend(symbol, timeframe)
            current_mode = self.trend_manager.get_mode(symbol, timeframe)
            
            self.send_message(f"🔒 <b>Manual Trend Set</b>\n"
                            f"{symbol} {timeframe} → {current_trend} ({current_mode})\n"
                            f"⚠️ TradingView signals won't auto-update this\n"
                            f"Use /set_auto {symbol} {timeframe} to allow auto updates")
            
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_show_trends(self, message):
        """Handle /show_trends command"""
        if not self.trend_manager:
            self.send_message("❌ Trend manager not initialized")
            return
        
        symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD"]
        
        msg = "📊 <b>Current Trends</b>\n\n"
        for symbol in symbols:
            trends = self.trend_manager.get_all_trends_with_mode(symbol)
            has_non_neutral = any(trend_data["trend"] != "NEUTRAL" for trend_data in trends.values())
            
            if has_non_neutral:
                msg += f"<b>{symbol}:</b>\n"
                for tf, trend_data in trends.items():
                    if trend_data["trend"] != "NEUTRAL":
                        mode_icon = "🔒" if trend_data["mode"] == "MANUAL" else "🔄"
                        msg += f"  {tf}: {trend_data['trend']} {mode_icon}\n"
                msg += "─────────────\n"
        
        self.send_message(msg)

    def handle_trend_matrix(self, message):
        """Show complete trend matrix for all symbols"""
        if not self.trend_manager:
            self.send_message("❌ Trend manager not initialized")
            return
        
        symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD"]
        
        msg = "🎯 <b>Complete Trend Matrix</b>\n\n"
        
        for symbol in symbols:
            msg += f"<b>{symbol}</b>\n"
            trends = self.trend_manager.get_all_trends_with_mode(symbol)
            
            # Show individual timeframes with mode
            for tf in ["5m", "15m", "1h", "1d"]:
                trend_data = trends.get(tf, {"trend": "NEUTRAL", "mode": "AUTO"})
                trend = trend_data["trend"]
                mode = trend_data["mode"]
                
                emoji = "🟢" if trend == "BULLISH" else "🔴" if trend == "BEARISH" else "⚪"
                mode_icon = "🔒" if mode == "MANUAL" else "🔄"
                
                msg += f"  {tf}: {emoji} {trend} {mode_icon}\n"
            
            # Show logic alignments
            for logic in ["LOGIC1", "LOGIC2", "LOGIC3"]:
                alignment = self.trend_manager.check_logic_alignment(symbol, logic)
                if alignment["aligned"]:
                    msg += f"  ✅ {logic}: {alignment['direction']}\n"
            
            msg += "─────────────\n"
        
        msg += "\n<b>Legend:</b> 🟢BULLISH 🔴BEARISH ⚪NEUTRAL 🔒MANUAL 🔄AUTO"
        self.send_message(msg)

    # ... (rest of the existing functions remain the same - handle_pause, handle_resume, etc.)
    def handle_pause(self, message):
        """Handle /pause command"""
        if self.trading_engine:
            self.trading_engine.is_paused = True
            self.send_message("⏸️ <b>Trading PAUSED</b>\nNo new trades will be executed")
        else:
            self.send_message("❌ Trading engine not initialized")

    def handle_resume(self, message):
        """Handle /resume command"""
        if self.trading_engine:
            self.trading_engine.is_paused = False
            self.send_message("✅ <b>Trading RESUMED</b>\nReady to execute new trades")
        else:
            self.send_message("❌ Trading engine not initialized")

    def handle_performance(self, message):
        """Handle /performance command"""
        if not self.risk_manager:
            self.send_message("❌ Risk manager not initialized")
            return
            
        stats = self.risk_manager.get_stats()
        performance_msg = (
            "📈 <b>Trading Performance</b>\n\n"
            f"🔸 Total Trades: {stats['total_trades']}\n"
            f"🔸 Winning Trades: {stats['winning_trades']}\n"
            f"🔸 Win Rate: {stats['win_rate']:.1f}%\n\n"
            f"💰 Today's PnL: ${stats['daily_profit'] - stats['daily_loss']:.2f}\n"
            f"📊 Daily Profit: ${stats['daily_profit']:.2f}\n"
            f"📉 Daily Loss: ${stats['daily_loss']:.2f}\n"
            f"🔻 Lifetime Loss: ${stats['lifetime_loss']:.2f}"
        )
        self.send_message(performance_msg)

    def handle_stats(self, message):
        """Handle /stats command"""
        if not self.risk_manager:
            self.send_message("❌ Risk manager not initialized")
            return
            
        stats = self.risk_manager.get_stats()
        risk_msg = (
            "⚠️ <b>Risk Management</b>\n\n"
            f"🔸 Risk Tier: ${stats['current_risk_tier']}\n"
            f"🔸 Daily Loss Limit: ${stats['risk_parameters']['daily_loss_limit']}\n"
            f"🔸 Max Total Loss: ${stats['risk_parameters']['max_total_loss']}\n\n"
            f"📊 Daily Loss: ${stats['daily_loss']:.2f}/{stats['risk_parameters']['daily_loss_limit']}\n"
            f"🔻 Lifetime Loss: ${stats['lifetime_loss']:.2f}/{stats['risk_parameters']['max_total_loss']}\n\n"
            f"📦 Current Lot Size: {stats['current_lot_size']}"
        )
        self.send_message(risk_msg)

    def handle_trades(self, message):
        """Handle /trades command"""
        if not self.trading_engine:
            self.send_message("❌ Trading engine not initialized")
            return
            
        if not self.trading_engine.open_trades:
            self.send_message("📭 <b>No Open Trades</b>")
            return
        
        rr_ratio = self.config.get("rr_ratio", 1.0)
        trades_msg = "📊 <b>Open Trades</b>\n\n"
        for i, trade in enumerate(self.trading_engine.open_trades, 1):
            if trade.status != "closed":
                chain_info = f" [RE-{trade.chain_level}]" if trade.is_re_entry else ""
                trades_msg += (
                    f"<b>Trade #{i}{chain_info}</b>\n"
                    f"Symbol: {trade.symbol} | {trade.direction.upper()}\n"
                    f"Strategy: {trade.strategy}\n"
                    f"Entry: {trade.entry:.5f} | SL: {trade.sl:.5f}\n"
                    f"TP: {trade.tp:.5f} | RR: 1:{rr_ratio}\n"
                    f"Lot: {trade.lot_size:.2f}\n"
                    "────────────────────\n"
                )
        
        self.send_message(trades_msg)

    def handle_chains_status(self, message):
        """Show active re-entry chains"""
        if not self.trading_engine:
            self.send_message("❌ Trading engine not initialized")
            return
        
        chains = self.trading_engine.reentry_manager.active_chains
        
        if not chains:
            self.send_message("🔗 <b>No Active Re-entry Chains</b>")
            return
        
        msg = "🔗 <b>Active Re-entry Chains</b>\n\n"
        for chain_id, chain in chains.items():
            msg += (
                f"<b>{chain.symbol} - {chain.direction.upper()}</b>\n"
                f"Level: {chain.current_level}/{chain.max_level}\n"
                f"Total Profit: ${chain.total_profit:.2f}\n"
                f"Status: {chain.status}\n"
                "────────────────────\n"
            )
        
        self.send_message(msg)

    # Logic control handlers
    def handle_logic1_on(self, message):
        if self.trading_engine:
            self.trading_engine.enable_logic(1)
            self.send_message("✅ LOGIC 1 TRADING ENABLED")

    def handle_logic1_off(self, message):
        if self.trading_engine:
            self.trading_engine.disable_logic(1)
            self.send_message("⛔ LOGIC 1 TRADING DISABLED")

    def handle_logic2_on(self, message):
        if self.trading_engine:
            self.trading_engine.enable_logic(2)
            self.send_message("✅ LOGIC 2 TRADING ENABLED")

    def handle_logic2_off(self, message):
        if self.trading_engine:
            self.trading_engine.disable_logic(2)
            self.send_message("⛔ LOGIC 2 TRADING DISABLED")

    def handle_logic3_on(self, message):
        if self.trading_engine:
            self.trading_engine.enable_logic(3)
            self.send_message("✅ LOGIC 3 TRADING ENABLED")

    def handle_logic3_off(self, message):
        if self.trading_engine:
            self.trading_engine.disable_logic(3)
            self.send_message("⛔ LOGIC 3 TRADING DISABLED")

    def handle_logic_status(self, message):
        if not self.trading_engine:
            self.send_message("❌ Trading engine not initialized")
            return
            
        status = self.trading_engine.get_logic_status()
        status_msg = (
            "🤖 <b>LOGIC STATUS:</b>\n\n"
            f"LOGIC 1 (1H+15M→5M): {'✅ ENABLED' if status['logic1'] else '❌ DISABLED'}\n"
            f"LOGIC 2 (1H+15M→15M): {'✅ ENABLED' if status['logic2'] else '❌ DISABLED'}\n"
            f"LOGIC 3 (1D+1H→1H): {'✅ ENABLED' if status['logic3'] else '❌ DISABLED'}\n\n"
            "Use /logic1_on, /logic1_off, etc. to control"
        )
        self.send_message(status_msg)

    def handle_lot_size_status(self, message):
        """Show current lot size settings"""
        if not self.risk_manager or not self.risk_manager.mt5_client:
            self.send_message("❌ Risk manager not initialized")
            return
        
        balance = self.risk_manager.mt5_client.get_account_balance()
        current_lot = self.risk_manager.get_fixed_lot_size(balance)
        tier = self.risk_manager.get_risk_tier(balance)
        
        msg = (
            "📦 <b>Lot Size Configuration</b>\n\n"
            f"Account Balance: ${balance:.2f}\n"
            f"Current Tier: ${tier}\n"
            f"Current Lot Size: {current_lot:.2f}\n\n"
            "<b>Tier Settings:</b>\n"
            "$5,000 → 0.05 lots\n"
            "$10,000 → 0.10 lots\n"
            "$25,000 → 1.00 lots\n"
            "$100,000 → 5.00 lots\n\n"
            "Use /set_lot_size TIER LOT to override"
        )
        self.send_message(msg)

    def handle_set_lot_size(self, message):
        """Handle manual lot size override"""
        if not self.risk_manager:
            self.send_message("❌ Risk manager not initialized")
            return
        
        try:
            parts = message['text'].split()
            
            if len(parts) < 3:
                self.send_message(
                    "📝 <b>Usage:</b> /set_lot_size TIER LOT\n\n"
                    "<b>Example:</b> /set_lot_size 10000 0.15\n"
                    "This sets 0.15 lots for $10,000 tier"
                )
                return
            
            tier = int(parts[1])
            lot_size = float(parts[2])
            
            valid_tiers = [5000, 10000, 25000, 100000]
            if tier not in valid_tiers:
                self.send_message(f"❌ Invalid tier. Use: {', '.join(map(str, valid_tiers))}")
                return
            
            if lot_size <= 0 or lot_size > 10:
                self.send_message("❌ Lot size must be between 0.01 and 10.00")
                return
            
            self.risk_manager.set_manual_lot_size(tier, lot_size)
            self.send_message(f"✅ Lot size override: ${tier} → {lot_size:.2f} lots")
            
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    # Analytics handlers
    def handle_performance_report(self, message):
        report = self.analytics_engine.get_performance_report()
        msg = f"📊 Performance Report (30 Days)\n\n"
        msg += f"Total Trades: {report['total_trades']}\n"
        msg += f"Win Rate: {report['win_rate']:.1f}%\n"
        msg += f"Total PnL: ${report['total_pnl']:.2f}\n"
        msg += f"Avg Win: ${report['average_win']:.2f}\n"
        msg += f"Avg Loss: ${report['average_loss']:.2f}"
        self.send_message(msg)

    def handle_pair_report(self, message):
        pair_stats = self.analytics_engine.get_pair_performance()
        msg = "📈 Pair Performance\n\n"
        for symbol, stats in pair_stats.items():
            win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            msg += f"{symbol}: {stats['trades']} trades, ${stats['pnl']:.2f}, {win_rate:.1f}% WR\n"
        self.send_message(msg)

    def handle_strategy_report(self, message):
        strategy_stats = self.analytics_engine.get_strategy_performance()
        msg = "🤖 Strategy Performance\n\n"
        for strategy, stats in strategy_stats.items():
            win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            msg += f"{strategy}: {stats['trades']} trades, ${stats['pnl']:.2f}, {win_rate:.1f}% WR\n"
        self.send_message(msg)

    def handle_signal_status(self, message):
        """Show current signal status for all symbols"""
        if not self.trading_engine:
            self.send_message("❌ Trading engine not initialized")
            return
        
        msg = "📡 <b>Current Signal Status</b>\n\n"
        
        symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD"]
        
        for symbol in symbols:
            if symbol in self.trading_engine.current_signals:
                signals = self.trading_engine.current_signals[symbol]
                msg += f"<b>{symbol}:</b>\n"
                msg += f"  5m: {signals.get('5m', 'NA')}\n"
                msg += f"  15m: {signals.get('15m', 'NA')}\n"
                msg += f"  1h: {signals.get('1h', 'NA')}\n"
                msg += f"  1d: {signals.get('1d', 'NA')}\n"
            else:
                msg += f"<b>{symbol}:</b> No signals yet\n"
            msg += "─────────────\n"
        
        self.send_message(msg)
    
    def handle_clear_loss_data(self, message):
        """Clear lifetime loss data"""
        if not self.risk_manager or not self.trading_engine:
            self.send_message("❌ Bot not initialized")
            return
        
        try:
            self.risk_manager.reset_lifetime_loss()
            self.trading_engine.db.clear_lifetime_losses()
            self.send_message("✅ Lifetime loss data cleared successfully")
        except Exception as e:
            self.send_message(f"❌ Error clearing loss data: {str(e)}")
    
    def handle_clear_daily_loss(self, message):
        """Clear daily loss data (keeps lifetime loss)"""
        if not self.risk_manager:
            self.send_message("❌ Bot not initialized")
            return
        
        try:
            self.risk_manager.reset_daily_loss()
            self.send_message("✅ Daily loss data cleared successfully")
        except Exception as e:
            self.send_message(f"❌ Error clearing daily loss data: {str(e)}")
    
    def handle_tp_system(self, message):
        """Control TP re-entry system: /tp_system [on/off/status]"""
        try:
            parts = message["text"].strip().split()
            
            re_entry_config = self.config.get("re_entry_config", {})
            
            if len(parts) < 2:
                enabled = re_entry_config.get("tp_reentry_enabled", False)
                status_emoji = "✅" if enabled else "❌"
                msg = (
                    f"{status_emoji} <b>TP Re-entry System</b>\n\n"
                    f"Status: {'ENABLED' if enabled else 'DISABLED'}\n"
                    f"Chain Levels: {re_entry_config.get('max_reentry_levels', 3)}\n"
                    f"SL Reduction: {re_entry_config.get('sl_reduction_per_level', 0.5)*100:.0f}% per level\n\n"
                    "<b>Usage:</b>\n"
                    "/tp_system on - Enable TP re-entry\n"
                    "/tp_system off - Disable TP re-entry\n"
                    "/tp_system status - Show this status"
                )
                self.send_message(msg)
                return
            
            action = parts[1].lower()
            
            if action == "on":
                if "re_entry_config" in self.config.config:
                    self.config.config["re_entry_config"]["tp_reentry_enabled"] = True
                self.send_message("✅ TP re-entry system ENABLED")
            elif action == "off":
                if "re_entry_config" in self.config.config:
                    self.config.config["re_entry_config"]["tp_reentry_enabled"] = False
                self.send_message("❌ TP re-entry system DISABLED")
            elif action == "status":
                self.handle_tp_system({"text": "/tp_system"})
            else:
                self.send_message("❌ Invalid action. Use: on, off, or status")
                
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_sl_hunt(self, message):
        """Control SL hunt re-entry system: /sl_hunt [on/off/status]"""
        try:
            parts = message["text"].strip().split()
            
            re_entry_config = self.config.get("re_entry_config", {})
            
            if len(parts) < 2:
                enabled = re_entry_config.get("sl_hunt_reentry_enabled", False)
                status_emoji = "✅" if enabled else "❌"
                msg = (
                    f"{status_emoji} <b>SL Hunt Re-entry System</b>\n\n"
                    f"Status: {'ENABLED' if enabled else 'DISABLED'}\n"
                    f"Offset Pips: {re_entry_config.get('sl_hunt_offset_pips', 1)}\n"
                    f"Cooldown: {re_entry_config.get('sl_hunt_cooldown_seconds', 60)}s\n"
                    f"Price Check: {re_entry_config.get('price_recovery_check_minutes', 2)} min\n\n"
                    "<b>Usage:</b>\n"
                    "/sl_hunt on - Enable SL hunt re-entry\n"
                    "/sl_hunt off - Disable SL hunt re-entry\n"
                    "/sl_hunt status - Show this status"
                )
                self.send_message(msg)
                return
            
            action = parts[1].lower()
            
            if action == "on":
                if "re_entry_config" in self.config.config:
                    self.config.config["re_entry_config"]["sl_hunt_reentry_enabled"] = True
                self.send_message("✅ SL hunt re-entry system ENABLED")
            elif action == "off":
                if "re_entry_config" in self.config.config:
                    self.config.config["re_entry_config"]["sl_hunt_reentry_enabled"] = False
                self.send_message("❌ SL hunt re-entry system DISABLED")
            elif action == "status":
                self.handle_sl_hunt({"text": "/sl_hunt"})
            else:
                self.send_message("❌ Invalid action. Use: on, off, or status")
                
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_exit_continuation(self, message):
        """Control Exit Continuation system: /exit_continuation [on/off/status]"""
        try:
            parts = message["text"].strip().split()
            
            re_entry_config = self.config.get("re_entry_config", {})
            
            if len(parts) < 2:
                enabled = re_entry_config.get("exit_continuation_enabled", True)
                status_emoji = "✅" if enabled else "❌"
                msg = (
                    f"{status_emoji} <b>Exit Continuation System</b>\n\n"
                    f"Status: {'ENABLED' if enabled else 'DISABLED'}\n"
                    f"Price Gap: {re_entry_config.get('tp_continuation_price_gap_pips', 2)} pips\n"
                    f"Monitor Interval: {re_entry_config.get('price_monitor_interval_seconds', 30)}s\n\n"
                    f"<b>What it does:</b>\n"
                    f"• After Exit Appeared signal → Profit book\n"
                    f"• Continue monitoring with price gap\n"
                    f"• Auto re-entry if price & alignment match\n"
                    f"• Works for: EXIT_APPEARED, REVERSAL, TREND_REVERSAL, OPPOSITE_SIGNAL\n\n"
                    "<b>Usage:</b>\n"
                    "/exit_continuation on - Enable continuation\n"
                    "/exit_continuation off - Disable continuation\n"
                    "/exit_continuation status - Show this status"
                )
                self.send_message(msg)
                return
            
            action = parts[1].lower()
            
            if action == "on":
                if "re_entry_config" in self.config.config:
                    self.config.config["re_entry_config"]["exit_continuation_enabled"] = True
                self.send_message("✅ Exit continuation system ENABLED\n\n"
                                "Bot will monitor for re-entry after exit signals with price gap")
            elif action == "off":
                if "re_entry_config" in self.config.config:
                    self.config.config["re_entry_config"]["exit_continuation_enabled"] = False
                self.send_message("❌ Exit continuation system DISABLED\n\n"
                                "Bot will stop monitoring after exit signals")
            elif action == "status":
                self.handle_exit_continuation({"text": "/exit_continuation"})
            else:
                self.send_message("❌ Invalid action. Use: on, off, or status")
                
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_tp_report(self, message):
        """Show TP re-entry statistics and performance"""
        if not self.trading_engine:
            self.send_message("❌ Trading engine not initialized")
            return
        
        try:
            tp_stats = self.trading_engine.db.get_tp_reentry_stats()
            sl_stats = self.trading_engine.db.get_sl_hunt_reentry_stats()
            reversal_stats = self.trading_engine.reversal_handler.get_reversal_exit_stats()
            
            msg = "📊 <b>Advanced Re-entry Report (30 Days)</b>\n\n"
            
            msg += "<b>TP Re-entry System:</b>\n"
            msg += f"Total TP Re-entries: {tp_stats.get('total_tp_reentries', 0)}\n"
            msg += f"Profitable: {tp_stats.get('profitable_tp_reentries', 0)}\n"
            msg += f"Total PnL: ${tp_stats.get('total_tp_reentry_pnl', 0):.2f}\n"
            msg += f"Avg PnL: ${tp_stats.get('avg_tp_reentry_pnl', 0):.2f}\n\n"
            
            msg += "<b>SL Hunt Re-entry System:</b>\n"
            msg += f"SL Hunt Attempts: {sl_stats.get('sl_hunt_attempts', 0)}\n"
            msg += f"Successful Re-entries: {sl_stats.get('total_sl_hunt_reentries', 0)}\n\n"
            
            msg += "<b>Reversal Exit System:</b>\n"
            msg += f"Total Reversal Exits: {reversal_stats.get('total_reversal_exits', 0)}\n"
            msg += f"Profitable Exits: {reversal_stats.get('profitable_exits', 0)}\n"
            msg += f"Total PnL: ${reversal_stats.get('total_reversal_pnl', 0):.2f}\n"
            msg += f"Avg PnL: ${reversal_stats.get('avg_reversal_pnl', 0):.2f}"
            
            self.send_message(msg)
            
        except Exception as e:
            self.send_message(f"❌ Error generating report: {str(e)}")

    def handle_simulation_mode(self, message):
        """Toggle simulation mode on/off"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /simulation_mode [on/off]")
                return
            
            mode = parts[1].lower()
            if mode not in ['on', 'off']:
                self.send_message("❌ Invalid mode. Use 'on' or 'off'")
                return
            
            simulate = (mode == 'on')
            self.config.update('simulate_orders', simulate)
            
            status = "ENABLED ✅" if simulate else "DISABLED ❌"
            self.send_message(f"🔄 Simulation Mode: {status}\n\n{'⚠️ Orders will be simulated (not live)' if simulate else '✅ Live trading mode active'}")
        
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_reentry_config(self, message):
        """Display all re-entry configuration settings"""
        re_cfg = self.config.get('re_entry_config', {})
        
        msg = "⚙️ <b>Re-entry System Configuration</b>\n\n"
        msg += f"<b>System Status:</b>\n"
        msg += f"TP Re-entry: {'✅ ON' if re_cfg.get('tp_reentry_enabled', True) else '❌ OFF'}\n"
        msg += f"SL Hunt Re-entry: {'✅ ON' if re_cfg.get('sl_hunt_reentry_enabled', True) else '❌ OFF'}\n"
        msg += f"Reversal Exit: {'✅ ON' if re_cfg.get('reversal_exit_enabled', True) else '❌ OFF'}\n"
        msg += f"Exit Continuation: {'✅ ON' if re_cfg.get('exit_continuation_enabled', True) else '❌ OFF'}\n\n"
        
        msg += f"<b>Timing Settings:</b>\n"
        msg += f"Monitor Interval: {re_cfg.get('price_monitor_interval_seconds', 30)}s\n"
        msg += f"SL Hunt Cooldown: {re_cfg.get('sl_hunt_cooldown_seconds', 60)}s\n"
        msg += f"Recovery Window: {re_cfg.get('price_recovery_check_minutes', 2)} min\n\n"
        
        msg += f"<b>Re-entry Rules:</b>\n"
        msg += f"SL Hunt Offset: {re_cfg.get('sl_hunt_offset_pips', 1.0)} pips\n"
        msg += f"Max Chain Levels: {re_cfg.get('max_chain_levels', 2)}\n"
        msg += f"SL Reduction: {int(re_cfg.get('sl_reduction_per_level', 0.5) * 100)}%"
        
        self.send_message(msg)

    def handle_set_monitor_interval(self, message):
        """Set price monitor interval (30-300 seconds)"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /set_monitor_interval [30-300]")
                return
            
            interval = int(parts[1])
            if not (30 <= interval <= 300):
                self.send_message("❌ Interval must be between 30-300 seconds")
                return
            
            re_cfg = self.config.get('re_entry_config', {})
            re_cfg['price_monitor_interval_seconds'] = interval
            self.config.update('re_entry_config', re_cfg)
            
            self.send_message(f"✅ Price monitor interval set to {interval}s")
        
        except ValueError:
            self.send_message("❌ Invalid number. Use: /set_monitor_interval [30-300]")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_set_sl_offset(self, message):
        """Set SL hunt offset pips (1-5)"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /set_sl_offset [1-5]")
                return
            
            offset = float(parts[1])
            if not (1 <= offset <= 5):
                self.send_message("❌ Offset must be between 1-5 pips")
                return
            
            re_cfg = self.config.get('re_entry_config', {})
            re_cfg['sl_hunt_offset_pips'] = offset
            self.config.update('re_entry_config', re_cfg)
            
            self.send_message(f"✅ SL hunt offset set to {offset} pips")
        
        except ValueError:
            self.send_message("❌ Invalid number. Use: /set_sl_offset [1-5]")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_set_cooldown(self, message):
        """Set SL hunt cooldown (30-300 seconds)"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /set_cooldown [30-300]")
                return
            
            cooldown = int(parts[1])
            if not (30 <= cooldown <= 300):
                self.send_message("❌ Cooldown must be between 30-300 seconds")
                return
            
            re_cfg = self.config.get('re_entry_config', {})
            re_cfg['sl_hunt_cooldown_seconds'] = cooldown
            self.config.update('re_entry_config', re_cfg)
            
            self.send_message(f"✅ SL hunt cooldown set to {cooldown}s")
        
        except ValueError:
            self.send_message("❌ Invalid number. Use: /set_cooldown [30-300]")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_set_recovery_time(self, message):
        """Set price recovery window (1-10 minutes)"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /set_recovery_time [1-10]")
                return
            
            minutes = int(parts[1])
            if not (1 <= minutes <= 10):
                self.send_message("❌ Recovery time must be between 1-10 minutes")
                return
            
            re_cfg = self.config.get('re_entry_config', {})
            re_cfg['price_recovery_check_minutes'] = minutes
            self.config.update('re_entry_config', re_cfg)
            
            self.send_message(f"✅ Price recovery window set to {minutes} minutes")
        
        except ValueError:
            self.send_message("❌ Invalid number. Use: /set_recovery_time [1-10]")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_set_max_levels(self, message):
        """Set max re-entry chain levels (1-5)"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /set_max_levels [1-5]")
                return
            
            levels = int(parts[1])
            if not (1 <= levels <= 5):
                self.send_message("❌ Max levels must be between 1-5")
                return
            
            re_cfg = self.config.get('re_entry_config', {})
            re_cfg['max_chain_levels'] = levels
            self.config.update('re_entry_config', re_cfg)
            
            self.send_message(f"✅ Max re-entry levels set to {levels}")
        
        except ValueError:
            self.send_message("❌ Invalid number. Use: /set_max_levels [1-5]")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_set_sl_reduction(self, message):
        """Set SL reduction percentage (0.3-0.7 = 30%-70%)"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /set_sl_reduction [0.3-0.7]")
                return
            
            reduction = float(parts[1])
            if not (0.3 <= reduction <= 0.7):
                self.send_message("❌ Reduction must be between 0.3-0.7 (30%-70%)")
                return
            
            re_cfg = self.config.get('re_entry_config', {})
            re_cfg['sl_reduction_per_level'] = reduction
            self.config.update('re_entry_config', re_cfg)
            
            self.send_message(f"✅ SL reduction set to {int(reduction * 100)}% per level")
        
        except ValueError:
            self.send_message("❌ Invalid number. Use: /set_sl_reduction [0.3-0.7]")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_reset_reentry_config(self, message):
        """Reset all re-entry settings to defaults"""
        default_re_cfg = {
            "max_chain_levels": 2,
            "sl_reduction_per_level": 0.5,
            "recovery_window_minutes": 30,
            "min_time_between_re_entries": 60,
            "sl_hunt_offset_pips": 1.0,
            "tp_reentry_enabled": True,
            "sl_hunt_reentry_enabled": True,
            "reversal_exit_enabled": True,
            "price_monitor_interval_seconds": 30,
            "tp_continuation_price_gap_pips": 2.0,
            "sl_hunt_cooldown_seconds": 60,
            "price_recovery_check_minutes": 2
        }
        
        self.config.update('re_entry_config', default_re_cfg)
        self.send_message("✅ Re-entry config reset to defaults:\n\n"
                         "Monitor Interval: 30s\n"
                         "SL Offset: 1 pip\n"
                         "Cooldown: 60s\n"
                         "Recovery: 2 min\n"
                         "Max Levels: 2\n"
                         "SL Reduction: 50%")

    def handle_view_sl_config(self, message):
        """Display all symbol SL configurations with dual SL system info"""
        active_system = self.config.get('active_sl_system', 'sl-1')
        sl_enabled = self.config.get('sl_system_enabled', True)
        sl_systems = self.config.get('sl_systems', {})
        sl_reductions = self.config.get('symbol_sl_reductions', {})
        symbol_config = self.config.get('symbol_config', {})
        current_tier = self.config.get('default_risk_tier', '5000')
        
        system_info = sl_systems.get(active_system, {})
        system_name = system_info.get('name', active_system.upper())
        
        msg = f"📊 <b>SL Configuration</b>\n\n"
        msg += f"<b>Active System:</b> {system_name}\n"
        msg += f"<b>Status:</b> {'✅ ENABLED' if sl_enabled else '❌ DISABLED'}\n"
        msg += f"<b>Account Tier:</b> ${current_tier}\n\n"
        
        all_symbols = list(symbol_config.keys())
        
        for symbol in all_symbols:
            volatility = symbol_config.get(symbol, {}).get('volatility', 'MEDIUM')
            
            system_symbols = system_info.get('symbols', {})
            if symbol in system_symbols and current_tier in system_symbols[symbol]:
                original_pips = system_symbols[symbol][current_tier]['sl_pips']
            else:
                original_pips = 0
            
            reduction_percent = sl_reductions.get(symbol, 0)
            
            if reduction_percent > 0:
                current_pips = int(original_pips * (1 - reduction_percent / 100))
                msg += f"<b>{symbol} ({volatility}):</b>\n"
                msg += f"  Original: {original_pips} pips | Reduced: {reduction_percent}% | Current: {current_pips} pips\n\n"
            else:
                msg += f"<b>{symbol} ({volatility}):</b>\n"
                msg += f"  SL: {original_pips} pips (No reduction)\n\n"
        
        self.send_message(msg)

    def handle_set_symbol_sl(self, message):
        """Reduce symbol SL by percentage - /set_symbol_sl SYMBOL PERCENT"""
        try:
            parts = message['text'].split()
            if len(parts) != 3:
                self.send_message(
                    "❌ <b>Usage:</b> /set_symbol_sl SYMBOL PERCENT\n\n"
                    "<b>Example:</b> /set_symbol_sl XAUUSD 20\n"
                    "This reduces Gold SL by 20%\n\n"
                    "<b>Percent Range:</b> 5-50%"
                )
                return
            
            symbol = parts[1].upper()
            percent = float(parts[2])
            
            if not (5 <= percent <= 50):
                self.send_message("❌ Percentage must be between 5-50%")
                return
            
            symbol_config = self.config.get('symbol_config', {})
            if symbol not in symbol_config:
                self.send_message(f"❌ Symbol {symbol} not found in config")
                return
            
            active_system = self.config.get('active_sl_system', 'sl-1')
            sl_systems = self.config.get('sl_systems', {})
            current_tier = self.config.get('default_risk_tier', '5000')
            
            system_info = sl_systems.get(active_system, {})
            system_symbols = system_info.get('symbols', {})
            
            if symbol not in system_symbols or current_tier not in system_symbols[symbol]:
                self.send_message(f"❌ {symbol} not configured in {active_system}")
                return
            
            original_pips = system_symbols[symbol][current_tier]['sl_pips']
            current_pips = int(original_pips * (1 - percent / 100))
            
            sl_reductions = self.config.get('symbol_sl_reductions', {})
            sl_reductions[symbol] = percent
            self.config.update('symbol_sl_reductions', sl_reductions)
            
            self.send_message(
                f"✅ <b>{symbol} SL Reduced</b>\n\n"
                f"Original: {original_pips} pips\n"
                f"Reduction: {percent}%\n"
                f"Current: {current_pips} pips"
            )
        
        except ValueError:
            self.send_message("❌ Invalid percentage. Use numbers only (5-50)")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_sl_status(self, message):
        """Show current active SL system, enabled status, all symbol reductions"""
        active_system = self.config.get('active_sl_system', 'sl-1')
        sl_enabled = self.config.get('sl_system_enabled', True)
        sl_systems = self.config.get('sl_systems', {})
        sl_reductions = self.config.get('symbol_sl_reductions', {})
        
        system_info = sl_systems.get(active_system, {})
        system_name = system_info.get('name', active_system.upper())
        system_desc = system_info.get('description', '')
        
        msg = "⚙️ <b>SL SYSTEM STATUS</b>\n\n"
        msg += f"<b>Active System:</b> {system_name}\n"
        msg += f"<b>Description:</b> {system_desc}\n"
        msg += f"<b>Status:</b> {'✅ ENABLED' if sl_enabled else '❌ DISABLED'}\n\n"
        
        if sl_reductions:
            msg += "<b>Symbol SL Reductions:</b>\n"
            for symbol, percent in sl_reductions.items():
                msg += f"  {symbol}: {percent}% reduction\n"
        else:
            msg += "<b>Symbol SL Reductions:</b> None\n"
        
        self.send_message(msg)
    
    def handle_sl_system_change(self, message):
        """Switch between SL systems - /sl_system_change [sl-1/sl-2]"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message(
                    "❌ <b>Usage:</b> /sl_system_change [sl-1/sl-2]\n\n"
                    "<b>Example:</b> /sl_system_change sl-2\n"
                    "Switches to SL-2 system"
                )
                return
            
            new_system = parts[1].lower()
            
            if new_system not in ['sl-1', 'sl-2']:
                self.send_message("❌ System must be sl-1 or sl-2")
                return
            
            sl_systems = self.config.get('sl_systems', {})
            if new_system not in sl_systems:
                self.send_message(f"❌ System {new_system} not found in config")
                return
            
            self.config.update('active_sl_system', new_system)
            
            system_info = sl_systems[new_system]
            system_name = system_info.get('name', new_system.upper())
            
            self.send_message(
                f"✅ <b>SL System Changed</b>\n\n"
                f"Now using: {system_name}\n"
                f"Description: {system_info.get('description', '')}"
            )
        
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_sl_system_on(self, message):
        """Enable specific SL system - /sl_system_on [sl-1/sl-2]"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message(
                    "❌ <b>Usage:</b> /sl_system_on [sl-1/sl-2]\n\n"
                    "<b>Example:</b> /sl_system_on sl-1\n"
                    "Enables SL-1 system"
                )
                return
            
            system = parts[1].lower()
            
            if system not in ['sl-1', 'sl-2']:
                self.send_message("❌ System must be sl-1 or sl-2")
                return
            
            sl_systems = self.config.get('sl_systems', {})
            if system not in sl_systems:
                self.send_message(f"❌ System {system} not found in config")
                return
            
            self.config.update('active_sl_system', system)
            self.config.update('sl_system_enabled', True)
            
            system_info = sl_systems[system]
            system_name = system_info.get('name', system.upper())
            
            self.send_message(
                f"✅ <b>SL System Enabled</b>\n\n"
                f"Active: {system_name}\n"
                f"Status: ✅ ENABLED"
            )
        
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_complete_sl_system_off(self, message):
        """Disable all SL systems"""
        self.config.update('sl_system_enabled', False)
        
        self.send_message(
            "⚠️ <b>ALL SL SYSTEMS DISABLED</b>\n\n"
            "All SL systems are now turned off.\n"
            "Use /sl_system_on [sl-1/sl-2] to enable."
        )
    
    def handle_reset_symbol_sl(self, message):
        """Reset one symbol to original SL - /reset_symbol_sl SYMBOL"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message(
                    "❌ <b>Usage:</b> /reset_symbol_sl SYMBOL\n\n"
                    "<b>Example:</b> /reset_symbol_sl XAUUSD\n"
                    "Resets Gold to original SL"
                )
                return
            
            symbol = parts[1].upper()
            
            sl_reductions = self.config.get('symbol_sl_reductions', {})
            
            if symbol not in sl_reductions:
                self.send_message(f"❌ {symbol} has no SL reduction to reset")
                return
            
            del sl_reductions[symbol]
            self.config.update('symbol_sl_reductions', sl_reductions)
            
            self.send_message(
                f"✅ <b>{symbol} SL Reset</b>\n\n"
                f"{symbol} has been reset to original SL values"
            )
        
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_reset_all_sl(self, message):
        """Reset all symbols to original SL - clear all reductions"""
        sl_reductions = self.config.get('symbol_sl_reductions', {})
        
        if not sl_reductions:
            self.send_message("❌ No SL reductions to reset")
            return
        
        count = len(sl_reductions)
        self.config.update('symbol_sl_reductions', {})
        
        self.send_message(
            f"✅ <b>All SL Reductions Reset</b>\n\n"
            f"Reset {count} symbol(s) to original SL values"
        )

    def handle_view_risk_caps(self, message):
        """Display risk caps and current loss status"""
        if not self.risk_manager:
            self.send_message("❌ Risk manager not initialized")
            return
        
        tiers = self.config.get('risk_tiers', {})
        current_tier = self.config.get('default_risk_tier', '5000')
        
        daily_loss = self.risk_manager.daily_loss
        lifetime_loss = self.risk_manager.lifetime_loss
        
        msg = "💰 <b>Risk Caps &amp; Loss Status</b>\n\n"
        msg += f"<b>Current Tier: ${current_tier}</b>\n\n"
        
        msg += f"<b>Current Loss:</b>\n"
        msg += f"Daily: ${abs(daily_loss):.2f}\n"
        msg += f"Lifetime: ${abs(lifetime_loss):.2f}\n\n"
        
        msg += f"<b>All Risk Tiers:</b>\n"
        for balance, caps in sorted(tiers.items(), key=lambda x: int(x[0])):
            daily_cap = caps.get('daily_loss_limit', 0)
            lifetime_cap = caps.get('max_total_loss', 0)
            msg += f"${balance}: Daily ${daily_cap} | Lifetime ${lifetime_cap}\n"
        
        self.send_message(msg)

    def handle_set_daily_cap(self, message):
        """Set daily loss limit for current tier"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /set_daily_cap AMOUNT\nExample: /set_daily_cap 500")
                return
            
            amount = float(parts[1])
            if amount <= 0:
                self.send_message("❌ Amount must be positive")
                return
            
            current_tier = self.config.get('default_risk_tier', '5000')
            tiers = self.config.get('risk_tiers', {})
            
            if current_tier in tiers:
                tiers[current_tier]['daily_loss_limit'] = amount
                self.config.update('risk_tiers', tiers)
                self.send_message(f"✅ Daily loss limit for ${current_tier} tier set to ${amount}")
            else:
                self.send_message(f"❌ Tier ${current_tier} not found")
        
        except ValueError:
            self.send_message("❌ Invalid amount. Use numbers only")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_set_lifetime_cap(self, message):
        """Set lifetime loss limit for current tier"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /set_lifetime_cap AMOUNT\nExample: /set_lifetime_cap 2000")
                return
            
            amount = float(parts[1])
            if amount <= 0:
                self.send_message("❌ Amount must be positive")
                return
            
            current_tier = self.config.get('default_risk_tier', '5000')
            tiers = self.config.get('risk_tiers', {})
            
            if current_tier in tiers:
                tiers[current_tier]['max_total_loss'] = amount
                self.config.update('risk_tiers', tiers)
                self.send_message(f"✅ Lifetime loss limit for ${current_tier} tier set to ${amount}")
            else:
                self.send_message(f"❌ Tier ${current_tier} not found")
        
        except ValueError:
            self.send_message("❌ Invalid amount. Use numbers only")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_set_risk_tier(self, message):
        """Set complete risk tier - /set_risk_tier BALANCE DAILY LIFETIME"""
        try:
            parts = message['text'].split()
            if len(parts) != 4:
                self.send_message("❌ Usage: /set_risk_tier BALANCE DAILY LIFETIME\nExample: /set_risk_tier 10000 500 2000")
                return
            
            balance = parts[1]
            daily_limit = float(parts[2])
            lifetime_limit = float(parts[3])
            
            if daily_limit <= 0 or lifetime_limit <= 0:
                self.send_message("❌ Limits must be positive")
                return
            
            tiers = self.config.get('risk_tiers', {})
            tiers[balance] = {
                'daily_loss_limit': daily_limit,
                'max_total_loss': lifetime_limit
            }
            self.config.update('risk_tiers', tiers)
            
            self.send_message(f"✅ Risk tier ${balance} configured:\nDaily: ${daily_limit}\nLifetime: ${lifetime_limit}")
        
        except ValueError:
            self.send_message("❌ Invalid values. Use: /set_risk_tier BALANCE DAILY LIFETIME")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    # Dual Order Commands
    def handle_dual_order_status(self, message):
        """Show dual order system status"""
        try:
            dual_config = self.config.get("dual_order_config", {})
            enabled = dual_config.get("enabled", True)
            
            status_msg = (
                f"📊 DUAL ORDER SYSTEM STATUS\n\n"
                f"Status: {'✅ ENABLED' if enabled else '❌ DISABLED'}\n"
                f"Mode: Both orders use same lot size (no split)\n"
                f"Order A: TP Trail (existing system)\n"
                f"Order B: Profit Trail (pyramid system)\n\n"
                f"Note: Orders work independently - no rollback"
            )
            self.send_message(status_msg)
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_toggle_dual_orders(self, message):
        """Toggle dual order system on/off"""
        try:
            dual_config = self.config.get("dual_order_config", {})
            current = dual_config.get("enabled", True)
            new_status = not current
            
            dual_config["enabled"] = new_status
            self.config.update("dual_order_config", dual_config)
            
            status = "✅ ENABLED" if new_status else "❌ DISABLED"
            self.send_message(f"✅ Dual order system: {status}")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    # Profit Booking Commands
    def handle_profit_status(self, message):
        """Show profit booking system status"""
        try:
            profit_config = self.config.get("profit_booking_config", {})
            enabled = profit_config.get("enabled", True)
            max_level = profit_config.get("max_level", 4)
            profit_targets = profit_config.get("profit_targets", [10, 20, 40, 80, 160])
            multipliers = profit_config.get("multipliers", [1, 2, 4, 8, 16])
            
            status_msg = (
                f"💰 PROFIT BOOKING SYSTEM STATUS\n\n"
                f"Status: {'✅ ENABLED' if enabled else '❌ DISABLED'}\n"
                f"Max Level: {max_level}\n\n"
                f"Profit Targets:\n"
            )
            
            for i, target in enumerate(profit_targets[:max_level+1]):
                mult = multipliers[i] if i < len(multipliers) else 1
                status_msg += f"  Level {i}: ${target} ({mult}x orders)\n"
            
            self.send_message(status_msg)
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_profit_stats(self, message):
        """Show profit booking statistics"""
        try:
            if not self.trading_engine:
                self.send_message("❌ Trading engine not available")
                return
            
            profit_manager = getattr(self.trading_engine, 'profit_booking_manager', None)
            if not profit_manager:
                self.send_message("❌ Profit booking manager not available")
                return
            
            # Get stats from database
            db = getattr(self.trading_engine, 'db', None)
            if db:
                stats = db.get_profit_chain_stats()
                
                stats_msg = (
                    f"📊 PROFIT BOOKING STATISTICS\n\n"
                    f"Total Chains: {stats.get('total_chains', 0)}\n"
                    f"Active Chains: {stats.get('active_chains', 0)}\n"
                    f"Completed Chains: {stats.get('completed_chains', 0)}\n"
                    f"Average Level: {stats.get('avg_level', 0):.1f}\n"
                    f"Total Profit: ${stats.get('total_profit', 0):.2f}\n"
                    f"Avg Profit/Chain: ${stats.get('avg_profit_per_chain', 0):.2f}"
                )
                self.send_message(stats_msg)
            else:
                # Fallback: count active chains
                active_chains = profit_manager.get_all_chains()
                stats_msg = (
                    f"📊 PROFIT BOOKING STATISTICS\n\n"
                    f"Active Chains: {len(active_chains)}\n"
                )
                self.send_message(stats_msg)
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_toggle_profit_booking(self, message):
        """Toggle profit booking system on/off"""
        try:
            profit_config = self.config.get("profit_booking_config", {})
            current = profit_config.get("enabled", True)
            new_status = not current
            
            profit_config["enabled"] = new_status
            self.config.update("profit_booking_config", profit_config)
            
            status = "✅ ENABLED" if new_status else "❌ DISABLED"
            self.send_message(f"✅ Profit booking system: {status}")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_set_profit_targets(self, message):
        """Set profit targets - /set_profit_targets 10 20 40 80 160"""
        try:
            parts = message['text'].split()
            if len(parts) < 2:
                self.send_message("❌ Usage: /set_profit_targets TARGET1 TARGET2 ...\nExample: /set_profit_targets 10 20 40 80 160")
                return
            
            targets = [float(t) for t in parts[1:]]
            if any(t <= 0 for t in targets):
                self.send_message("❌ All targets must be positive")
                return
            
            profit_config = self.config.get("profit_booking_config", {})
            profit_config["profit_targets"] = targets
            profit_config["max_level"] = len(targets) - 1
            self.config.update("profit_booking_config", profit_config)
            
            self.send_message(f"✅ Profit targets updated: {targets}")
        except ValueError:
            self.send_message("❌ Invalid values. Use numbers only.")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_profit_chains(self, message):
        """Show all active profit booking chains"""
        try:
            if not self.trading_engine:
                self.send_message("❌ Trading engine not available")
                return
            
            profit_manager = getattr(self.trading_engine, 'profit_booking_manager', None)
            if not profit_manager:
                self.send_message("❌ Profit booking manager not available")
                return
            
            active_chains = profit_manager.get_all_chains()
            if not active_chains:
                self.send_message("📊 No active profit booking chains")
                return
            
            chains_msg = "📊 ACTIVE PROFIT BOOKING CHAINS\n\n"
            for chain_id, chain in list(active_chains.items())[:10]:  # Limit to 10
                chains_msg += (
                    f"Chain: {chain_id[:8]}...\n"
                    f"Symbol: {chain.symbol} {chain.direction.upper()}\n"
                    f"Level: {chain.current_level}/{chain.max_level}\n"
                    f"Profit: ${chain.total_profit:.2f}\n"
                    f"Orders: {len(chain.active_orders)}\n\n"
                )
            
            if len(active_chains) > 10:
                chains_msg += f"... and {len(active_chains) - 10} more chains"
            
            self.send_message(chains_msg)
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_stop_profit_chain(self, message):
        """Stop a specific profit booking chain - /stop_profit_chain CHAIN_ID"""
        try:
            parts = message['text'].split()
            if len(parts) < 2:
                self.send_message("❌ Usage: /stop_profit_chain CHAIN_ID")
                return
            
            chain_id = parts[1]
            
            if not self.trading_engine:
                self.send_message("❌ Trading engine not available")
                return
            
            profit_manager = getattr(self.trading_engine, 'profit_booking_manager', None)
            if not profit_manager:
                self.send_message("❌ Profit booking manager not available")
                return
            
            chain = profit_manager.get_chain(chain_id)
            if not chain:
                self.send_message(f"❌ Chain {chain_id} not found")
                return
            
            profit_manager.stop_chain(chain_id, "Manual stop via Telegram")
            self.send_message(f"✅ Chain {chain_id[:8]}... stopped")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_stop_all_profit_chains(self, message):
        """Stop all active profit booking chains"""
        try:
            if not self.trading_engine:
                self.send_message("❌ Trading engine not available")
                return
            
            profit_manager = getattr(self.trading_engine, 'profit_booking_manager', None)
            if not profit_manager:
                self.send_message("❌ Profit booking manager not available")
                return
            
            active_chains = profit_manager.get_all_chains()
            if not active_chains:
                self.send_message("📊 No active chains to stop")
                return
            
            profit_manager.stop_all_chains("Manual stop all via Telegram")
            self.send_message(f"✅ Stopped {len(active_chains)} profit booking chains")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_set_chain_multipliers(self, message):
        """Set chain multipliers - /set_chain_multipliers 1 2 4 8 16"""
        try:
            parts = message['text'].split()
            if len(parts) < 2:
                self.send_message("❌ Usage: /set_chain_multipliers MULT1 MULT2 ...\nExample: /set_chain_multipliers 1 2 4 8 16")
                return
            
            multipliers = [int(m) for m in parts[1:]]
            if any(m <= 0 for m in multipliers):
                self.send_message("❌ All multipliers must be positive integers")
                return
            
            profit_config = self.config.get("profit_booking_config", {})
            profit_config["multipliers"] = multipliers
            profit_config["max_level"] = len(multipliers) - 1
            self.config.update("profit_booking_config", profit_config)
            
            self.send_message(f"✅ Chain multipliers updated: {multipliers}")
        except ValueError:
            self.send_message("❌ Invalid values. Use integers only.")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_set_sl_reductions(self, message):
        """Set SL reductions - /set_sl_reductions 0 10 25 40 50"""
        try:
            parts = message['text'].split()
            if len(parts) < 2:
                self.send_message("❌ Usage: /set_sl_reductions RED1 RED2 ...\nExample: /set_sl_reductions 0 10 25 40 50")
                return
            
            reductions = [float(r) for r in parts[1:]]
            if any(r < 0 or r > 100 for r in reductions):
                self.send_message("❌ All reductions must be between 0 and 100")
                return
            
            profit_config = self.config.get("profit_booking_config", {})
            profit_config["sl_reductions"] = reductions
            self.config.update("profit_booking_config", profit_config)
            
            self.send_message(f"✅ SL reductions updated: {reductions}")
        except ValueError:
            self.send_message("❌ Invalid values. Use numbers only.")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_profit_config(self, message):
        """Show profit booking configuration"""
        try:
            profit_config = self.config.get("profit_booking_config", {})
            enabled = profit_config.get("enabled", True)
            max_level = profit_config.get("max_level", 4)
            profit_targets = profit_config.get("profit_targets", [10, 20, 40, 80, 160])
            multipliers = profit_config.get("multipliers", [1, 2, 4, 8, 16])
            sl_reductions = profit_config.get("sl_reductions", [0, 10, 25, 40, 50])
            
            config_msg = (
                f"💰 PROFIT BOOKING CONFIGURATION\n\n"
                f"Status: {'✅ ENABLED' if enabled else '❌ DISABLED'}\n"
                f"Max Level: {max_level}\n\n"
                f"Profit Targets:\n"
            )
            
            for i, target in enumerate(profit_targets[:max_level+1]):
                mult = multipliers[i] if i < len(multipliers) else 1
                sl_red = sl_reductions[i] if i < len(sl_reductions) else 0
                config_msg += f"  Level {i}: ${target} ({mult}x orders, SL -{sl_red}%)\n"
            
            config_msg += f"\nMultipliers: {multipliers}\n"
            config_msg += f"SL Reductions: {sl_reductions}%"
            
            self.send_message(config_msg)
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def start_polling(self):
        """Start polling for Telegram commands"""
        def poll_commands():
            offset = 0
            while True:
                try:
                    url = f"{self.base_url}/getUpdates?offset={offset}&timeout=30"
                    response = requests.get(url, timeout=35)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if not data.get("ok"):
                            print(f"Telegram API error: {data}")
                            time.sleep(10)
                            continue 
                            
                        updates = data.get("result", [])
                        
                        for update in updates:
                            offset = update["update_id"] + 1
                            
                            if "message" in update and "text" in update["message"]:
                                message_data = update["message"]
                                user_id = message_data["from"]["id"]
                                text = message_data["text"].strip()
                                
                                if user_id == self.config["allowed_telegram_user"]:
                                    command_parts = text.split()
                                    if command_parts:
                                        command = command_parts[0]
                                        
                                        if command in self.command_handlers:
                                            try:
                                                self.command_handlers[command](message_data)
                                            except Exception as e:
                                                error_msg = f"❌ Error executing {command}: {str(e)}"
                                                self.send_message(error_msg)
                                                print(f"Command error: {e}")
                
                except Exception as e:
                    print(f"Telegram polling error: {str(e)}")
                    time.sleep(10)
        
        thread = threading.Thread(target=poll_commands, daemon=True)
        thread.start()
        print("SUCCESS: Telegram bot polling started")