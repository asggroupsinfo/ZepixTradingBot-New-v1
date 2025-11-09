from src.database import TradeDatabase

class AnalyticsEngine:
    def __init__(self):
        self.db = TradeDatabase()

    def get_performance_report(self):
        trades = self.db.get_trade_history(30)
        
        report = {
            'total_trades': len(trades),
            'winning_trades': sum(1 for t in trades if t['pnl'] > 0),
            'losing_trades': sum(1 for t in trades if t['pnl'] < 0),
            'total_pnl': sum(t['pnl'] for t in trades),
            'win_rate': 0,
            'average_win': 0,
            'average_loss': 0
        }
        
        if report['total_trades'] > 0:
            report['win_rate'] = (report['winning_trades'] / report['total_trades']) * 100
            wins = [t['pnl'] for t in trades if t['pnl'] > 0]
            losses = [t['pnl'] for t in trades if t['pnl'] < 0]
            report['average_win'] = sum(wins) / len(wins) if wins else 0
            report['average_loss'] = sum(losses) / len(losses) if losses else 0

        return report

    def get_pair_performance(self):
        trades = self.db.get_trade_history(30)
        pair_stats = {}
        
        for trade in trades:
            symbol = trade['symbol']
            if symbol not in pair_stats:
                pair_stats[symbol] = {'trades': 0, 'pnl': 0, 'wins': 0}
            
            pair_stats[symbol]['trades'] += 1
            pair_stats[symbol]['pnl'] += trade['pnl']
            if trade['pnl'] > 0:
                pair_stats[symbol]['wins'] += 1
        
        return pair_stats

    def get_strategy_performance(self):
        trades = self.db.get_trade_history(30)
        strategy_stats = {}
        
        for trade in trades:
            strategy = trade['strategy']
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {'trades': 0, 'pnl': 0, 'wins': 0}
            
            strategy_stats[strategy]['trades'] += 1
            strategy_stats[strategy]['pnl'] += trade['pnl']
            if trade['pnl'] > 0:
                strategy_stats[strategy]['wins'] += 1
        
        return strategy_stats