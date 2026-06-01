import json
import os
from datetime import datetime
from typing import Dict, List


class TradeLogger:
    """Tüm sinyal, pozisyon ve işlem loglarını kaydeder"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        
        # Klasörleri oluştur
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(f"{log_dir}/signals", exist_ok=True)
        os.makedirs(f"{log_dir}/trades", exist_ok=True)
        os.makedirs(f"{log_dir}/daily", exist_ok=True)
        
        # Günlük log dosyaları
        today = datetime.now().strftime("%Y-%m-%d")
        self.signal_log_file = f"{log_dir}/signals/{today}.jsonl"
        self.trade_log_file = f"{log_dir}/trades/{today}.jsonl"
        self.daily_summary_file = f"{log_dir}/daily/{today}.json"
        
        # Backtest logu (tüm zamanlar)
        self.backtest_file = f"{log_dir}/backtest_all.jsonl"
    
    def log_signal(self, symbol: str, signal_data: Dict):
        """Sinyal logla"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'signal': signal_data.get('signal'),
            'direction': signal_data.get('direction'),
            'total_score': signal_data.get('total_score'),
            'max_score': signal_data.get('max_score'),
            'summary': signal_data.get('summary'),
            'price': signal_data.get('price'),
            'constitution': signal_data.get('constitution', {}).get('details'),
            'layers_passed': {}
        }
        
        # Katman detayları
        layers = signal_data.get('layers', {})
        for layer_name, layer_data in layers.items():
            if layer_data:
                log_entry['layers_passed'][layer_name] = layer_data.get('passed', False)
        
        self._append_jsonl(self.signal_log_file, log_entry)
        self._append_jsonl(self.backtest_file, {**log_entry, 'type': 'SIGNAL'})
    
    def log_position_open(self, position_data: Dict):
        """Pozisyon açılışı logla"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'POSITION_OPEN',
            'position_id': position_data.get('id'),
            'symbol': position_data.get('symbol'),
            'direction': str(position_data.get('type', 'UNKNOWN')),
            # 'direction': position_data.get('type', {}).get('value') if hasattr(position_data.get('type'), 'value') else str(position_data.get('type')),
            'entry_price': position_data.get('entry_price'),
            'capital': position_data.get('capital'),
            'leverage': position_data.get('leverage'),
            'quantity': position_data.get('quantity'),
            'stop_loss': position_data.get('stop_loss'),
            'signal_score': position_data.get('total_score')
        }
        
        self._append_jsonl(self.trade_log_file, log_entry)
        self._append_jsonl(self.backtest_file, log_entry)
    
    def log_position_exit(self, exit_data: Dict):
        """Pozisyon çıkışı logla"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'POSITION_EXIT',
            'position_id': exit_data.get('position_id'),
            'symbol': exit_data.get('symbol'),
            'stage': exit_data.get('stage'),
            'exit_price': exit_data.get('exit_price'),
            'profit': exit_data.get('profit'),
            'profit_pct': exit_data.get('profit_pct'),
            'daily_total': exit_data.get('daily_total'),
            'daily_pct': exit_data.get('daily_pct')
        }
        
        self._append_jsonl(self.trade_log_file, log_entry)
        self._append_jsonl(self.backtest_file, log_entry)
    
    def log_wallet_snapshot(self, wallet_status: Dict):
        """Cüzdan anlık durumu logla"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'WALLET_SNAPSHOT',
            'total_capital': wallet_status.get('total_capital'),
            'daily_profit': wallet_status.get('daily_profit'),
            'daily_profit_pct': wallet_status.get('daily_profit_pct'),
            'active_slots': wallet_status.get('active_slots'),
            'available_slots': wallet_status.get('available_slots'),
            'active_positions': len(wallet_status.get('active_positions', [])),
            'win_rate': wallet_status.get('win_rate')
        }
        
        self._append_jsonl(self.backtest_file, log_entry)
    
    def save_daily_summary(self, wallet_status: Dict):
        """Günlük özet kaydet"""
        summary = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'final_capital': wallet_status.get('total_capital'),
            'daily_profit': wallet_status.get('daily_profit'),
            'daily_profit_pct': wallet_status.get('daily_profit_pct'),
            'total_trades': wallet_status.get('total_trades'),
            'winning_trades': wallet_status.get('winning_trades'),
            'losing_trades': wallet_status.get('losing_trades'),
            'win_rate': wallet_status.get('win_rate'),
            'saved_at': datetime.now().isoformat()
        }
        
        with open(self.daily_summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
    
    def get_today_signals(self) -> List[Dict]:
        """Bugünün sinyallerini getir"""
        return self._read_jsonl(self.signal_log_file)
    
    def get_today_trades(self) -> List[Dict]:
        """Bugünün işlemlerini getir"""
        return self._read_jsonl(self.trade_log_file)
    
    def get_backtest_logs(self, limit: int = 100) -> List[Dict]:
        """Backtest loglarını getir"""
        all_logs = self._read_jsonl(self.backtest_file)
        return all_logs[-limit:]
    
    def get_all_signals_history(self) -> List[Dict]:
        """Tüm sinyal geçmişini getir"""
        signals_dir = f"{self.log_dir}/signals"
        all_signals = []
        
        if os.path.exists(signals_dir):
            for filename in sorted(os.listdir(signals_dir)):
                if filename.endswith('.jsonl'):
                    filepath = os.path.join(signals_dir, filename)
                    all_signals.extend(self._read_jsonl(filepath))
        
        return all_signals
    
    def _append_jsonl(self, filepath: str, data: Dict):
        """JSONL dosyasına satır ekle"""
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, default=str) + '\n')
    
    def _read_jsonl(self, filepath: str) -> List[Dict]:
        """JSONL dosyasını oku"""
        if not os.path.exists(filepath):
            return []
        
        lines = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    lines.append(json.loads(line.strip()))
                except:
                    continue
        return lines


# Global logger instance
logger = TradeLogger()