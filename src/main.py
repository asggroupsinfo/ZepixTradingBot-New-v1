#!/usr/bin/env python3
import json
import os
import sys
import asyncio
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load .env file before anything else (highest priority for credentials)
load_dotenv()

from src.config import Config
from src.core.trading_engine import TradingEngine
from src.managers.risk_manager import RiskManager
from src.clients.mt5_client import MT5Client
from src.clients.telegram_bot import TelegramBot
from src.processors.alert_processor import AlertProcessor
from src.services.analytics_engine import AnalyticsEngine 
from src.models import Alert

# Initialize components
config = Config()
risk_manager = RiskManager(config)
mt5_client = MT5Client(config)
telegram_bot = TelegramBot(config)
alert_processor = AlertProcessor(config)

# Initialize trading engine with all components
trading_engine = TradingEngine(config, risk_manager, mt5_client, telegram_bot, alert_processor)

# Set dependencies
telegram_bot.set_dependencies(risk_manager, trading_engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    success = await trading_engine.initialize()
    
    if success:
        # MT5 initialization successful (connected OR simulation mode active)
        mode = "SIMULATION" if config.get('simulate_orders', False) else "LIVE TRADING"
        telegram_bot.send_message(f"Trading Bot v2.0 Started Successfully!\n"
                                 f"Mode: {mode}\n"
                                 f"1:1.5 RR System Active\n"
                                 f"Re-entry System Enabled")
        # Start background tasks
        asyncio.create_task(trading_engine.manage_open_trades())
        telegram_bot.start_polling()
    else:
        # MT5 connection failed AND simulation not enabled - enable it now
        print("WARNING: MT5 connection failed - auto-enabling SIMULATION MODE")
        config.update('simulate_orders', True)
        
        # Retry initialization with simulation mode enabled
        success_retry = await trading_engine.initialize()
        if success_retry:
            telegram_bot.send_message(f"Trading Bot v2.0 Started in SIMULATION MODE\n"
                                     f"WARNING: MT5 unavailable - simulating all trades\n"
                                     f"To enable live trading: run windows_setup_admin.bat\n"
                                     f"Re-entry System Active")
            asyncio.create_task(trading_engine.manage_open_trades())
            telegram_bot.start_polling()
        else:
            error_msg = "ERROR: CRITICAL: Bot initialization failed even in simulation mode"
            telegram_bot.send_message(error_msg)
            print(error_msg)
            raise RuntimeError("Bot initialization failed")
    
    yield
    
    # Shutdown (cleanup if needed)
    print("Trading bot shutting down...")

app = FastAPI(title="Zepix Automated Trading Bot v2.0", lifespan=lifespan)

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Handle incoming webhook alerts from TradingView/Zepix"""
    try:
        data = await request.json()
        
        print(f"Webhook received: {json.dumps(data, indent=2)}")
        
        # Validate alert
        if not alert_processor.validate_alert(data):
            return JSONResponse(content={"status": "rejected", "message": "Alert validation failed"})
        
        # Process alert
        result = await trading_engine.process_alert(data)
        
        if result:
            return JSONResponse(content={"status": "success", "message": "Alert processed"})
        else:
            return JSONResponse(content={"status": "rejected", "message": "Alert processing failed"})
            
    except Exception as e:
        error_msg = f"Webhook processing error: {str(e)}"
        telegram_bot.send_message(f"ERROR: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "daily_loss": risk_manager.daily_loss,
        "lifetime_loss": risk_manager.lifetime_loss,
        "mt5_connected": mt5_client.initialized,
        "features": {
            "fixed_lots": True,
            "reentry_system": True,
            "sl_hunting_protection": True,
            "1_1_rr": True
        }
    }

@app.get("/stats")
async def get_stats():
    """Get current statistics"""
    stats = risk_manager.get_stats()
    return {
        "daily_profit": stats["daily_profit"],
        "daily_loss": stats["daily_loss"],
        "lifetime_loss": stats["lifetime_loss"],
        "total_trades": stats["total_trades"],
        "winning_trades": stats["winning_trades"],
        "win_rate": stats["win_rate"],
        "current_risk_tier": stats["current_risk_tier"],
        "risk_parameters": stats["risk_parameters"],
        "trading_paused": trading_engine.is_paused,
        "simulation_mode": config["simulate_orders"],
        "lot_size": stats["current_lot_size"],
        "balance": stats["account_balance"]
    }

@app.post("/pause")
async def pause_trading():
    """Pause trading"""
    trading_engine.is_paused = True
    return {"status": "success", "message": "Trading paused"}

@app.post("/resume")
async def resume_trading():
    """Resume trading"""
    trading_engine.is_paused = False
    return {"status": "success", "message": "Trading resumed"}

@app.get("/trends")
async def get_trends():
    """Get all trends"""
    trends = {}
    
    # Get all symbols that have trends set (both from webhooks and manual)
    trend_data = trading_engine.trend_manager.trends.get("symbols", {})
    
    # If no symbols set, show default list
    if not trend_data:
        symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD"]
    else:
        symbols = list(trend_data.keys())
    
    for symbol in symbols:
        trends[symbol] = trading_engine.trend_manager.get_all_trends(symbol)
    
    return {"status": "success", "trends": trends}

@app.post("/set_trend")
async def set_trend_api(symbol: str, timeframe: str, trend: str, mode: str = "MANUAL"):
    """Set trend via API"""
    try:
        trading_engine.trend_manager.update_trend(symbol, timeframe, trend.lower(), mode)
        return {"status": "success", "message": f"Trend set for {symbol} {timeframe}: {trend}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/chains")
async def get_reentry_chains():
    """Get active re-entry chains"""
    chains = []
    for chain_id, chain in trading_engine.reentry_manager.active_chains.items():
        chains.append(chain.dict())
    return {"status": "success", "chains": chains}

@app.get("/lot_config")
async def get_lot_config():
    """Get lot size configuration"""
    return {
        "fixed_lots": config["fixed_lot_sizes"],
        "manual_overrides": config.get("manual_lot_overrides", {}),
        "current_balance": mt5_client.get_account_balance(),
        "current_lot": risk_manager.get_fixed_lot_size(mt5_client.get_account_balance())
    }

@app.post("/set_lot_size")
async def set_lot_size(tier: int, lot_size: float):
    """Set manual lot size override"""
    try:
        risk_manager.set_manual_lot_size(tier, lot_size)
        return {"status": "success", "message": f"Lot size set: ${tier} → {lot_size}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/reset_stats")
async def reset_stats():
    """Reset risk manager stats (for testing only)"""
    try:
        risk_manager.daily_loss = 0.0
        risk_manager.daily_profit = 0.0
        risk_manager.lifetime_loss = 0.0
        risk_manager.total_trades = 0
        risk_manager.winning_trades = 0
        risk_manager.save_stats()
        return {"status": "success", "message": "Stats reset successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/status")
async def get_status():
    """Get bot status with open trades"""
    stats = risk_manager.get_stats()
    open_trades_data = []
    for trade in trading_engine.open_trades:
        open_trades_data.append(trade.to_dict())
    
    return {
        "status": "running",
        "trading_paused": trading_engine.is_paused,
        "simulation_mode": config["simulate_orders"],
        "daily_profit": stats["daily_profit"],
        "daily_loss": stats["daily_loss"],
        "lifetime_loss": stats["lifetime_loss"],
        "total_trades": stats["total_trades"],
        "winning_trades": stats["winning_trades"],
        "win_rate": stats["win_rate"],
        "open_trades": open_trades_data,
        "open_trades_count": len(trading_engine.open_trades),
        "mt5_connected": mt5_client.initialized,
        "dual_orders_enabled": config.get("dual_order_config", {}).get("enabled", True),
        "profit_booking_enabled": config.get("profit_booking_config", {}).get("enabled", True)
    }

def check_port_available(host: str, port: int) -> bool:
    """Check if port is available"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            return True
    except OSError:
        return False

def kill_process_on_port(port: int) -> bool:
    """Kill process using the specified port (Windows)"""
    import subprocess
    try:
        # Find process using port
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    try:
                        # Kill the process
                        subprocess.run(
                            ["taskkill", "/F", "/PID", pid],
                            capture_output=True,
                            timeout=5
                        )
                        print(f"Killed process {pid} using port {port}")
                        return True
                    except Exception as e:
                        print(f"WARNING: Could not kill process {pid}: {e}")
                        return False
        return False
    except Exception as e:
        print(f"WARNING: Could not check port {port}: {e}")
        return False

if __name__ == "__main__":
    import argparse
    import socket
    import subprocess
    import time
    parser = argparse.ArgumentParser(description="Zepix Trading Bot v2.0")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", default=80, type=int, help="Port number (default: 80 for Windows VM)")
    args = parser.parse_args()
    
    # Check if port is available
    if not check_port_available(args.host, args.port):
        print(f"WARNING: Port {args.port} is already in use")
        print(f"Attempting to kill process using port {args.port}...")
        if kill_process_on_port(args.port):
            print(f"Process killed. Waiting 2 seconds...")
            time.sleep(2)
            if not check_port_available(args.host, args.port):
                print(f"ERROR: Port {args.port} is still in use. Please manually kill the process.")
                print(f"Run: netstat -ano | findstr :{args.port}")
                exit(1)
        else:
            print(f"ERROR: Could not free port {args.port}. Please manually kill the process.")
            print(f"Run: netstat -ano | findstr :{args.port}")
            print(f"Then: taskkill /F /PID <process_id>")
            exit(1)
    
    rr_ratio = config.get("rr_ratio", 1.0)
    print("=" * 50)
    print("ZEPIX TRADING BOT v2.0")
    print("=" * 50)
    print(f"Starting server on {args.host}:{args.port}")
    print("Features enabled:")
    print("+ Fixed lot sizes")
    print("+ Re-entry system") 
    print("+ SL hunting protection")
    print(f"+ 1:{rr_ratio} Risk-Reward")
    print("+ Progressive SL reduction")
    print("=" * 50)
    
    uvicorn.run(app, host=args.host, port=args.port)