from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from src.models import Trade, ReEntryChain
import uuid

class ReEntryManager:
    """Manage re-entry chains and SL hunting protection"""
    
    def __init__(self, config):
        self.config = config
        self.active_chains = {}  # chain_id -> ReEntryChain
        self.recent_sl_hits = {}  # symbol -> list of recent SL hits
        self.completed_tps = {}  # symbol -> recent TP completions
        
    def create_chain(self, trade: Trade) -> ReEntryChain:
        """Create a new re-entry chain from initial trade"""
        
        chain_id = f"{trade.symbol}_{uuid.uuid4().hex[:8]}"
        
        # Handle simulation mode where trade_id might be None
        # Use negative timestamp-based ID for simulation trades
        trade_ids = []
        if trade.trade_id is not None:
            trade_ids = [trade.trade_id]
        else:
            # Create a pseudo-ID for simulation mode
            sim_id = int(datetime.now().timestamp() * 1000) % 1000000
            trade_ids = [sim_id]
            print(f"INFO: Simulation mode: Using pseudo trade ID {sim_id}")
        
        # Get active SL system and reduction info
        active_system = self.config.get("active_sl_system", "sl-1")
        symbol_reductions = self.config.get("symbol_sl_reductions", {})
        symbol_reduction = symbol_reductions.get(trade.symbol, 0)
        
        # Get ORIGINAL unreduced SL pips from dual system config
        # Determine account tier based on balance
        balance = self.config.get("account_balance", 10000)
        if balance < 7500:
            tier = "5000"
        elif balance < 17500:
            tier = "10000"
        elif balance < 37500:
            tier = "25000"
        elif balance < 75000:
            tier = "50000"
        else:
            tier = "100000"
        
        # Fetch original SL pips from the active system config
        original_sl_pips = self.config["sl_systems"][active_system]["symbols"][trade.symbol][tier]["sl_pips"]
        
        # Calculate applied SL pips (what was actually used on the trade)
        applied_sl_pips = original_sl_pips * (1 - symbol_reduction / 100) if symbol_reduction > 0 else original_sl_pips
        
        chain = ReEntryChain(
            chain_id=chain_id,
            symbol=trade.symbol,
            direction=trade.direction,
            original_entry=trade.entry,
            original_sl_distance=abs(trade.entry - trade.sl),
            current_level=1,
            max_level=self.config["re_entry_config"]["max_chain_levels"],
            trades=trade_ids,
            created_at=datetime.now().isoformat(),
            last_update=datetime.now().isoformat(),
            metadata={
                "sl_system_used": active_system,
                "sl_reduction_percent": symbol_reduction,
                "original_sl_pips": original_sl_pips,
                "applied_sl_pips": applied_sl_pips
            }
        )
        
        self.active_chains[chain_id] = chain
        trade.chain_id = chain_id
        
        return chain
    
    def check_reentry_opportunity(self, symbol: str, signal: str, 
                                 price: float) -> Dict[str, Any]:
        """Check if new signal qualifies for re-entry"""
        
        result = {
            "is_reentry": False,
            "type": None,  # "tp_continuation" or "sl_recovery"
            "chain_id": None,
            "level": 1,
            "sl_adjustment": 1.0
        }
        
        # Check for TP continuation
        tp_opportunity = self._check_tp_continuation(symbol, signal, price)
        if tp_opportunity["eligible"]:
            result["is_reentry"] = True
            result["type"] = "tp_continuation"
            result["chain_id"] = tp_opportunity["chain_id"]
            result["level"] = tp_opportunity["level"]
            result["sl_adjustment"] = tp_opportunity["sl_adjustment"]
            return result
        
        # Check for SL recovery
        sl_opportunity = self._check_sl_recovery(symbol, signal, price)
        if sl_opportunity["eligible"]:
            result["is_reentry"] = True
            result["type"] = "sl_recovery"
            result["chain_id"] = sl_opportunity["chain_id"]  # Continue existing chain!
            result["level"] = sl_opportunity["level"]  # Use calculated level, not hardcoded!
            result["sl_adjustment"] = sl_opportunity["sl_adjustment"]  # Use progressive reduction!
            return result
        
        return result
    
    def _check_tp_continuation(self, symbol: str, signal: str, 
                              price: float) -> Dict[str, Any]:
        """Check if this is a continuation after TP hit"""
        
        result = {"eligible": False}
        
        if symbol not in self.completed_tps:
            return result
        
        recent_tps = self.completed_tps[symbol]
        current_time = datetime.now()
        
        for tp_event in recent_tps:
            time_since_tp = current_time - tp_event["time"]
            
            # Check if within continuation window
            if time_since_tp > timedelta(minutes=self.config["re_entry_config"]["recovery_window_minutes"]):
                continue
            
            # Check if same direction
            signal_direction = "buy" if signal in ["buy", "bull"] else "sell"
            if signal_direction != tp_event["direction"]:
                continue
            
            # Check if we haven't exceeded max levels
            chain = self.active_chains.get(tp_event["chain_id"])
            if chain and chain.current_level < chain.max_level:
                result["eligible"] = True
                result["chain_id"] = chain.chain_id
                result["level"] = chain.current_level + 1
                
                # Calculate SL adjustment
                reduction_per_level = self.config["re_entry_config"]["sl_reduction_per_level"]
                result["sl_adjustment"] = (1 - reduction_per_level) ** (result["level"] - 1)
                
                break
        
        return result
    
    def _check_sl_recovery(self, symbol: str, signal: str, 
                          price: float) -> Dict[str, Any]:
        """Check if this is a recovery after SL hit - continues existing chain"""
        
        result = {"eligible": False}
        
        if symbol not in self.recent_sl_hits:
            return result
        
        recent_sls = self.recent_sl_hits[symbol]
        current_time = datetime.now()
        
        for sl_event in recent_sls:
            time_since_sl = current_time - sl_event["time"]
            
            # Check if within recovery window
            if time_since_sl > timedelta(minutes=self.config["re_entry_config"]["recovery_window_minutes"]):
                continue
            
            # SAFETY CHECK #1: Enforce minimum time between re-entries (cooldown)
            min_time_seconds = self.config["re_entry_config"]["min_time_between_re_entries"]
            if time_since_sl < timedelta(seconds=min_time_seconds):
                print(f"WAIT: Re-entry cooldown active ({time_since_sl.seconds}s / {min_time_seconds}s)")
                continue
            
            # Check if same direction
            signal_direction = "buy" if signal in ["buy", "bull"] else "sell"
            if signal_direction != sl_event["direction"]:
                continue
            
            # Get chain info to continue it (not create new one!)
            chain_id = sl_event.get("chain_id")
            chain = self.active_chains.get(chain_id) if chain_id else None
            
            # Only allow re-entry if chain exists and hasn't hit max level
            if chain and chain.current_level < chain.max_level:
                # SAFETY CHECK #2: Verify price has recovered towards original entry
                # For BUY: new price should be higher than SL (recovering upwards)
                # For SELL: new price should be lower than SL (recovering downwards)
                price_recovered = False
                if signal_direction == "buy":
                    price_recovered = price > sl_event["sl_price"]
                else:
                    price_recovered = price < sl_event["sl_price"]
                
                if not price_recovered:
                    print(f"ERROR: Re-entry blocked: Price has not recovered from SL level")
                    continue
                
                result["eligible"] = True
                result["chain_id"] = chain.chain_id
                result["level"] = chain.current_level + 1
                
                # Calculate SL adjustment (progressive reduction)
                reduction_per_level = self.config["re_entry_config"]["sl_reduction_per_level"]
                result["sl_adjustment"] = (1 - reduction_per_level) ** (result["level"] - 1)
                
                # Reactivate chain
                chain.status = "active"
                
                print(f"SUCCESS: SL Recovery Re-Entry Eligible (Safe):")
                print(f"   Chain: {chain.chain_id}")
                print(f"   Level: {result['level']}/{chain.max_level}")
                print(f"   SL Adjustment: {result['sl_adjustment']:.2f}")
                print(f"   Time Since SL: {time_since_sl.seconds}s")
                print(f"   Price Recovered: {price_recovered}")
                
                break
        
        return result
    
    def record_tp_hit(self, trade: Trade, tp_price: float):
        """Record TP hit for continuation tracking"""
        
        if trade.symbol not in self.completed_tps:
            self.completed_tps[trade.symbol] = []
        
        # Keep only recent TPs (last 30 minutes)
        self._clean_old_events(self.completed_tps[trade.symbol])
        
        self.completed_tps[trade.symbol].append({
            "time": datetime.now(),
            "chain_id": trade.chain_id,
            "direction": trade.direction,
            "tp_price": tp_price,
            "original_entry": trade.original_entry or trade.entry
        })
        
        # Update chain status
        if trade.chain_id in self.active_chains:
            chain = self.active_chains[trade.chain_id]
            chain.total_profit += abs(tp_price - trade.entry) * trade.lot_size * 10000
            chain.last_update = datetime.now().isoformat()
    
    def record_sl_hit(self, trade: Trade):
        """Record SL hit for recovery tracking"""
        
        if trade.symbol not in self.recent_sl_hits:
            self.recent_sl_hits[trade.symbol] = []
        
        # Keep only recent SLs (last 30 minutes)
        self._clean_old_events(self.recent_sl_hits[trade.symbol])
        
        self.recent_sl_hits[trade.symbol].append({
            "time": datetime.now(),
            "direction": trade.direction,
            "sl_price": trade.sl,
            "original_entry": trade.original_entry or trade.entry,
            "chain_id": trade.chain_id  # Store chain_id to continue chain on re-entry,
        })
        
        # Mark chain as stopped if it exists
        if trade.chain_id in self.active_chains:
            self.active_chains[trade.chain_id].status = "stopped"
    
    def _clean_old_events(self, events: List[Dict]):
        """Remove events older than recovery window"""
        
        current_time = datetime.now()
        window = timedelta(minutes=self.config["re_entry_config"]["recovery_window_minutes"])
        
        events[:] = [e for e in events if current_time - e["time"] <= window]
    
    def update_chain_level(self, chain_id: str, new_trade_id: int):
        """Update chain when new re-entry is placed"""
        
        if chain_id in self.active_chains:
            chain = self.active_chains[chain_id]
            chain.current_level += 1
            
            # Handle None trade_id for simulation mode
            if new_trade_id is not None:
                chain.trades.append(new_trade_id)
            else:
                # Create pseudo-ID for simulation
                sim_id = int(datetime.now().timestamp() * 1000) % 1000000
                chain.trades.append(sim_id)
                print(f"INFO: Simulation mode: Using pseudo trade ID {sim_id} for re-entry")
            
            chain.last_update = datetime.now().isoformat()
            
            if chain.current_level >= chain.max_level:
                chain.status = "completed"