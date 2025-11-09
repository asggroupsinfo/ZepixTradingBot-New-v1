#!/usr/bin/env python3
"""Check trades and profit chains in database"""
import sqlite3

conn = sqlite3.connect('data/trading_bot.db')
cursor = conn.cursor()

print("=" * 60)
print("DATABASE CHECK")
print("=" * 60)

# Check open trades
cursor.execute("SELECT COUNT(*) FROM trades WHERE status='open'")
open_trades = cursor.fetchone()[0]
print(f"Total Open Trades: {open_trades}")

# Check TP trail orders
cursor.execute("SELECT COUNT(*) FROM trades WHERE order_type='TP_TRAIL' AND status='open'")
tp_trail = cursor.fetchone()[0]
print(f"TP Trail Orders: {tp_trail}")

# Check profit trail orders
cursor.execute("SELECT COUNT(*) FROM trades WHERE order_type='PROFIT_TRAIL' AND status='open'")
profit_trail = cursor.fetchone()[0]
print(f"Profit Trail Orders: {profit_trail}")

# Check active profit chains
cursor.execute("SELECT COUNT(*) FROM profit_booking_chains WHERE status='ACTIVE'")
active_chains = cursor.fetchone()[0]
print(f"Active Profit Chains: {active_chains}")

# Show recent trades
cursor.execute("SELECT trade_id, symbol, direction, order_type, status, created_at FROM trades ORDER BY created_at DESC LIMIT 10")
recent_trades = cursor.fetchall()
print(f"\nRecent Trades (last 10):")
for trade in recent_trades:
    print(f"  {trade}")

# Show active chains
cursor.execute("SELECT chain_id, symbol, current_level, status FROM profit_booking_chains WHERE status='ACTIVE'")
chains = cursor.fetchall()
print(f"\nActive Profit Chains:")
for chain in chains:
    print(f"  {chain}")

conn.close()
print("=" * 60)

