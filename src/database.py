import sqlite3
from datetime import datetime
from src.models import Trade, ReEntryChain
from typing import List, Dict, Any

class TradeDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('data/trading_bot.db', check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Main trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY,
                trade_id TEXT,
                symbol TEXT,
                entry_price REAL,
                exit_price REAL,
                sl_price REAL,
                tp_price REAL,
                lot_size REAL,
                direction TEXT,
                strategy TEXT,
                pnl REAL,
                status TEXT,
                open_time DATETIME,
                close_time DATETIME,
                chain_id TEXT,
                chain_level INTEGER,
                is_re_entry BOOLEAN,
                order_type TEXT,
                profit_chain_id TEXT,
                profit_level INTEGER DEFAULT 0
            )
        ''')
        
        # Add new columns if they don't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE trades ADD COLUMN order_type TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE trades ADD COLUMN profit_chain_id TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE trades ADD COLUMN profit_level INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Re-entry chains table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reentry_chains (
                chain_id TEXT PRIMARY KEY,
                symbol TEXT,
                direction TEXT,
                original_entry REAL,
                original_sl_distance REAL,
                max_level_reached INTEGER,
                total_profit REAL,
                status TEXT,
                created_at DATETIME,
                completed_at DATETIME
            )
        ''')
        
        # SL hunting events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sl_events (
                id INTEGER PRIMARY KEY,
                trade_id TEXT,
                symbol TEXT,
                sl_price REAL,
                original_entry REAL,
                hit_time DATETIME,
                recovery_attempted BOOLEAN,
                recovery_successful BOOLEAN
            )
        ''')
        
        # TP re-entry tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tp_reentry_events (
                id INTEGER PRIMARY KEY,
                chain_id TEXT,
                symbol TEXT,
                tp_level INTEGER,
                tp_price REAL,
                reentry_price REAL,
                sl_reduction_percent REAL,
                pnl REAL,
                timestamp DATETIME
            )
        ''')
        
        # Reversal exit events table  
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reversal_exit_events (
                id INTEGER PRIMARY KEY,
                trade_id TEXT,
                symbol TEXT,
                exit_price REAL,
                exit_signal TEXT,
                pnl REAL,
                timestamp DATETIME
            )
        ''')
        
        # System state table for pause/resume control
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME
            )
        ''')
        
        # Profit booking chains table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profit_booking_chains (
                chain_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                base_lot REAL NOT NULL,
                current_level INTEGER DEFAULT 0,
                total_profit REAL DEFAULT 0,
                status TEXT DEFAULT 'ACTIVE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Profit booking orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profit_booking_orders (
                order_id TEXT PRIMARY KEY,
                chain_id TEXT,
                level INTEGER,
                profit_target REAL,
                sl_reduction INTEGER,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chain_id) REFERENCES profit_booking_chains(chain_id)
            )
        ''')
        
        # Profit booking events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profit_booking_events (
                id INTEGER PRIMARY KEY,
                chain_id TEXT,
                level INTEGER,
                profit_booked REAL,
                orders_closed INTEGER,
                orders_placed INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()

    def save_trade(self, trade: Trade):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO trades VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (None, trade.trade_id, trade.symbol, trade.entry, trade.close_time, 
              trade.sl, trade.tp, trade.lot_size, trade.direction, trade.strategy,
              trade.pnl, trade.status, trade.open_time, trade.close_time,
              trade.chain_id, trade.chain_level, trade.is_re_entry,
              trade.order_type, trade.profit_chain_id, trade.profit_level))
        self.conn.commit()

    def save_chain(self, chain: ReEntryChain):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO reentry_chains VALUES (?,?,?,?,?,?,?,?,?,?)
        ''', (chain.chain_id, chain.symbol, chain.direction, 
              chain.original_entry, chain.original_sl_distance,
              chain.current_level, chain.total_profit, chain.status,
              chain.created_at, datetime.now().isoformat() if chain.status == "completed" else None))
        self.conn.commit()

    def save_sl_event(self, trade_id: str, symbol: str, sl_price: float, 
                     original_entry: float, recovery_attempted: bool = False,
                     recovery_successful: bool = False):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sl_events VALUES (?,?,?,?,?,?,?,?)
        ''', (None, trade_id, symbol, sl_price, original_entry, 
              datetime.now().isoformat(), recovery_attempted, recovery_successful))
        self.conn.commit()

    def get_trade_history(self, days=30) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM trades 
            WHERE close_time >= datetime('now', ?)
            ORDER BY close_time DESC
        ''', (f'-{days} days',))
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_chain_statistics(self) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        
        # Get chain performance
        cursor.execute('''
            SELECT 
                COUNT(*) as total_chains,
                AVG(max_level_reached) as avg_max_level,
                SUM(total_profit) as total_chain_profit,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_chains,
                COUNT(CASE WHEN total_profit > 0 THEN 1 END) as profitable_chains
            FROM reentry_chains
        ''')
        
        result = cursor.fetchone()
        columns = [description[0] for description in cursor.description]
        
        return dict(zip(columns, result))

    def get_sl_recovery_stats(self) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_sl_hits,
                COUNT(CASE WHEN recovery_attempted THEN 1 END) as recovery_attempts,
                COUNT(CASE WHEN recovery_successful THEN 1 END) as successful_recoveries
            FROM sl_events
            WHERE hit_time >= datetime('now', '-30 days')
        ''')
        
        result = cursor.fetchone()
        columns = [description[0] for description in cursor.description]
        
        return dict(zip(columns, result))
    
    def clear_lifetime_losses(self):
        """Reset lifetime loss counter (database side)"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE system_state SET value = '0', updated_at = ? WHERE key = 'lifetime_loss'
        ''', (datetime.now().isoformat(),))
        self.conn.commit()
        
    def get_tp_reentry_stats(self) -> Dict[str, Any]:
        """Get TP re-entry statistics"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as total_tp_reentries,
                SUM(pnl) as total_tp_reentry_pnl,
                AVG(pnl) as avg_tp_reentry_pnl,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as profitable_tp_reentries
            FROM tp_reentry_events
            WHERE timestamp >= datetime('now', '-30 days')
        ''')
        result = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, result)) if result else {}
    
    def get_sl_hunt_reentry_stats(self) -> Dict[str, Any]:
        """Get SL hunt re-entry statistics (from sl_events where recovery_successful=1)"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN recovery_successful THEN 1 END) as total_sl_hunt_reentries,
                COUNT(CASE WHEN recovery_attempted THEN 1 END) as sl_hunt_attempts
            FROM sl_events
            WHERE hit_time >= datetime('now', '-30 days')
        ''')
        result = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, result)) if result else {}
    
    def save_profit_chain(self, chain):
        """Save profit booking chain to database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO profit_booking_chains 
            (chain_id, symbol, direction, base_lot, current_level, total_profit, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            chain.chain_id,
            chain.symbol,
            chain.direction,
            chain.base_lot,
            chain.current_level,
            chain.total_profit,
            chain.status,
            chain.created_at,
            chain.updated_at
        ))
        self.conn.commit()
    
    def get_active_profit_chains(self) -> List[Dict[str, Any]]:
        """Get all active profit booking chains from database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM profit_booking_chains
            WHERE status = 'ACTIVE'
        ''')
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def save_profit_booking_order(self, order_id: str, chain_id: str, level: int, 
                                  profit_target: float, sl_reduction: int, status: str):
        """Save profit booking order to database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO profit_booking_orders
            (order_id, chain_id, level, profit_target, sl_reduction, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (order_id, chain_id, level, profit_target, sl_reduction, status, datetime.now().isoformat()))
        self.conn.commit()
    
    def save_profit_booking_event(self, chain_id: str, level: int, profit_booked: float,
                                  orders_closed: int, orders_placed: int):
        """Save profit booking event to database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO profit_booking_events
            (chain_id, level, profit_booked, orders_closed, orders_placed, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (chain_id, level, profit_booked, orders_closed, orders_placed, datetime.now().isoformat()))
        self.conn.commit()
    
    def get_profit_chain_stats(self) -> Dict[str, Any]:
        """Get profit booking chain statistics"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as total_chains,
                COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed_chains,
                COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active_chains,
                AVG(current_level) as avg_level,
                SUM(total_profit) as total_profit,
                AVG(total_profit) as avg_profit_per_chain
            FROM profit_booking_chains
        ''')
        result = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, result)) if result else {}