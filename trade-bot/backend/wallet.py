from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, date
from enum import Enum


class PositionType(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class PositionStatus(Enum):
    ACTIVE = "ACTIVE"
    PARTIAL_EXIT = "PARTIAL_EXIT"  # Kısmi çıkış yapıldı
    CLOSED = "CLOSED"


@dataclass
class Position:
    """Tek bir işlem pozisyonu"""
    id: int
    symbol: str
    type: PositionType
    entry_price: float
    quantity: float  # Coin miktarı
    capital: float  # Kullanılan sermaye (USDT)
    leverage: int  # 3x veya 5x
    total_score: int  # 4 veya 5
    max_score: int  # 5
    entry_time: datetime
    stop_loss: float
    take_profit_levels: List[float] = field(default_factory=list)
    exit_levels: Dict = field(default_factory=dict)
    
    # Çıkış takibi
    status: PositionStatus = PositionStatus.ACTIVE
    stage_1_exit: bool = False  # %33 çıkıldı mı?
    stage_2_exit: bool = False  # %33 daha çıkıldı mı?
    stage_3_exit: bool = False  # Tamamen çıkıldı mı?
    
    exit_price: Optional[float] = None
    profit_loss: float = 0.0
    profit_loss_pct: float = 0.0
    
    def get_remaining_capital(self) -> float:
        """Kalan sermaye miktarı"""
        if self.stage_3_exit:
            return 0.0
        elif self.stage_2_exit:
            return self.capital * 0.33
        elif self.stage_1_exit:
            return self.capital * 0.66
        else:
            return self.capital
    
    def calculate_profit(self, current_price: float) -> float:
        """Anlık kâr/zarar hesapla"""
        if self.type == PositionType.LONG:
            price_diff = current_price - self.entry_price
        else:
            price_diff = self.entry_price - current_price
        
        remaining = self.get_remaining_capital()
        leveraged_capital = remaining * self.leverage
        profit = (price_diff / self.entry_price) * leveraged_capital
        return profit


@dataclass
class Wallet:
    """Mock cüzdan - 4 parçalı sistem"""
    
    initial_capital: float  # Başlangıç sermayesi (örn: 1000 USDT)
    current_capital: float  # Güncel toplam değer
    
    # 4 parça
    slot_size: float  # Her parçanın büyüklüğü (initial_capital / 4)
    cash_reserve: float  # 4. parça - her zaman nakit
    
    # Aktif pozisyonlar (max 3)
    positions: List[Position] = field(default_factory=list)
    closed_positions: List[Position] = field(default_factory=list)
    
    # Günlük takip
    today: date = field(default_factory=lambda: date.today())
    daily_start_capital: float = 0.0  # Gün başı sermaye
    daily_profit_target: float = 0.0  # Günlük %1 hedef
    daily_profit: float = 0.0  # Günlük toplam kâr
    daily_profit_pct: float = 0.0
    
    # İstatistik
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    def __post_init__(self):
        if self.daily_start_capital == 0.0:
            self.daily_start_capital = self.current_capital
        if self.daily_profit_target == 0.0:
            self.daily_profit_target = self.current_capital * 0.01  # %1
        if self.slot_size == 0.0:
            self.slot_size = self.current_capital / 4
        if self.cash_reserve == 0.0:
            self.cash_reserve = self.slot_size
    
    # ==========================================
    # GÜNLÜK KONTROL
    # ==========================================
    def check_new_day(self):
        """Yeni gün kontrolü - günlük hedefi sıfırla"""
        today = date.today()
        if today != self.today:
            # Günlük kârı ana sermayeye ekle
            self.current_capital += self.daily_profit
            
            # Parçaları yeniden hesapla
            self.slot_size = self.current_capital / 4
            self.cash_reserve = self.slot_size
            
            # Yeni gün
            self.today = today
            self.daily_start_capital = self.current_capital
            self.daily_profit_target = self.current_capital * 0.01
            self.daily_profit = 0.0
            self.daily_profit_pct = 0.0
            
            print(f"\n{'='*50}")
            print(f"🌅 YENİ GÜN - {today}")
            print(f"   Sermaye: {self.current_capital:.2f} USDT")
            print(f"   Günlük Hedef: +{self.daily_profit_target:.2f} USDT (%1)")
            print(f"   Slot Başı: {self.slot_size:.2f} USDT")
            print(f"{'='*50}\n")
    
    # ==========================================
    # SLOT KONTROLÜ
    # ==========================================
    def get_active_slots(self) -> int:
        """Kaç slot aktif?"""
        return len([p for p in self.positions if p.status != PositionStatus.CLOSED])
    
    def has_available_slot(self) -> bool:
        """Boş slot var mı?"""
        return self.get_active_slots() < 3
    
    def get_available_capital(self) -> float:
        """İşlem için kullanılabilir sermaye"""
        active = self.get_active_slots()
        available_slots = 3 - active
        
        if available_slots <= 0:
            return 0.0
        
        # Her boş slot için slot_size kadar
        return self.slot_size * available_slots
    
    # ==========================================
    # KALDIRAÇ BELİRLEME
    # ==========================================
    def determine_leverage(self, total_score: int, max_score: int) -> int:
        """Sinyal gücüne göre kaldıraç"""
        if total_score == max_score:  # 5/5
            return 5
        elif total_score >= max_score - 1:  # 4/5
            return 3
        else:
            return 0  # İşlem yok
    
    # ==========================================
    # POZİSYON AÇMA
    # ==========================================
    def can_open_position(self, signal: Dict) -> tuple[bool, str]:
        """Pozisyon açılabilir mi?"""
        # Yeni gün kontrolü
        self.check_new_day()
        
        # Sinyal ENTER mi?
        if signal.get('signal') != 'ENTER':
            return False, "Sinyal ENTER değil"
        
        # Boş slot var mı?
        if not self.has_available_slot():
            return False, "Tüm slotlar dolu (3/3)"
        
        # Kaldıraç uygun mu?
        leverage = self.determine_leverage(
            signal.get('total_score', 0),
            signal.get('max_score', 5)
        )
        if leverage == 0:
            return False, "Sinyal gücü yetersiz (min 4/5 gerekli)"
        
        # Günlük kayıp limiti aşıldı mı?
        if self.daily_profit < -self.current_capital * 0.075:  # %7.5 max kayıp
            return False, "Günlük kayıp limiti aşıldı"
        
        return True, f"Onaylandı ({leverage}x)"
    
    def open_position(self, symbol: str, signal: Dict, current_price: float) -> Optional[Position]:
        """Yeni pozisyon aç"""
        can_open, reason = self.can_open_position(signal)
        
        if not can_open:
            print(f"❌ Pozisyon açılamadı: {reason}")
            return None
        
        direction = signal.get('direction', 'LONG')
        leverage = self.determine_leverage(
            signal.get('total_score', 0),
            signal.get('max_score', 5)
        )
        
        # Sermaye = 1 slot
        capital = self.slot_size
        leveraged_capital = capital * leverage
        
        # Coin miktarı
        quantity = leveraged_capital / current_price
        
        # Stop-loss hesapla (ATR bazlı)
        atr = signal.get('layers', {}).get('trend', {}).get('checks', {})
        # Basit stop: %2
        if direction == 'LONG':
            stop_loss = current_price * 0.98
            take_profit_1 = current_price * 1.02  # %2
            take_profit_2 = current_price * 1.04  # %4
        else:
            stop_loss = current_price * 1.02
            take_profit_1 = current_price * 0.98
            take_profit_2 = current_price * 0.96
        
        position = Position(
            id=len(self.positions) + len(self.closed_positions) + 1,
            symbol=symbol,
            type=PositionType.LONG if direction == 'LONG' else PositionType.SHORT,
            entry_price=current_price,
            quantity=quantity,
            capital=capital,
            leverage=leverage,
            total_score=signal.get('total_score', 0),
            max_score=signal.get('max_score', 5),
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            take_profit_levels=[take_profit_1, take_profit_2],
            exit_levels=signal.get('layers', {})
        )
        
        self.positions.append(position)
        self.total_trades += 1
        
        print(f"\n{'='*50}")
        print(f"🔵 POZİSYON AÇILDI - {symbol}")
        print(f"   Yön: {direction} | Kaldıraç: {leverage}x")
        print(f"   Giriş: {current_price:.4f}")
        print(f"   Sermaye: {capital:.2f} USDT")
        print(f"   Pozisyon: {leveraged_capital:.2f} USDT")
        print(f"   Miktar: {quantity:.4f}")
        print(f"   Stop-Loss: {stop_loss:.4f}")
        print(f"   Slot: {self.get_active_slots()}/3")
        print(f"{'='*50}\n")
        
        return position
    
    # ==========================================
    # POZİSYON ÇIKIŞ (3 AŞAMALI)
    # ==========================================
    def check_exit_conditions(self, position: Position, current_price: float, 
                               layers: Dict = None) -> int:
        """
        Kaç aşama çıkılması gerektiğini kontrol et
        Returns: 0 (çıkış yok), 1, 2, veya 3 (tamamen çık)
        """
        if position.status == PositionStatus.CLOSED:
            return 0
        
        # Stop-loss kontrolü
        if position.type == PositionType.LONG:
            if current_price <= position.stop_loss:
                return 3  # Tamamen çık
        else:
            if current_price >= position.stop_loss:
                return 3  # Tamamen çık
        
        # Katman bozulma kontrolü (eğer layer bilgisi varsa)
        if layers:
            trigger = layers.get('trigger', {})
            divergence = layers.get('divergence', {})
            correction = layers.get('correction', {})
            trend = layers.get('trend', {})
            
            # 3. katman bozuldu → Aşama 1
            if not position.stage_1_exit and not divergence.get('passed', True):
                return 1
            
            # 2. katman bozuldu → Aşama 2
            if position.stage_1_exit and not position.stage_2_exit:
                if not correction.get('passed', True):
                    return 2
            
            # 1. katman bozuldu → Aşama 3
            if position.stage_2_exit and not position.stage_3_exit:
                if not trend.get('passed', True):
                    return 3
        
        return 0
    
    def execute_exit(self, position: Position, current_price: float, 
                     stage: int = 1) -> Dict:
        """Çıkış işlemini gerçekleştir"""
        
        exit_percentage = stage * 0.33  # %33, %66, %100
        
        # Kâr/zarar hesapla
        if position.type == PositionType.LONG:
            profit_pct = (current_price - position.entry_price) / position.entry_price
        else:
            profit_pct = (position.entry_price - current_price) / position.entry_price
        
        # Kaldıraçlı kâr
        leveraged_profit_pct = profit_pct * position.leverage
        exiting_capital = position.capital * exit_percentage
        profit = exiting_capital * leveraged_profit_pct
        
        # Stage güncelle
        if stage >= 1:
            position.stage_1_exit = True
        if stage >= 2:
            position.stage_2_exit = True
        if stage >= 3:
            position.stage_3_exit = True
            position.status = PositionStatus.CLOSED
            position.exit_price = current_price
        
        position.profit_loss += profit
        position.profit_loss_pct = leveraged_profit_pct
        
        # Cüzdan güncelle
        self.daily_profit += profit
        self.daily_profit_pct = (self.daily_profit / self.daily_start_capital) * 100
        
        # Tamamen kapandıysa
        if position.status == PositionStatus.CLOSED:
            self.positions.remove(position)
            self.closed_positions.append(position)
            
            if profit > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
            
            # Slot'u ana sermayeye geri ekle
            self.current_capital += position.capital + profit
        
        emoji = "🟢" if profit > 0 else "🔴"
        print(f"\n{emoji} ÇIKIŞ - Aşama {stage}/3 - {position.symbol}")
        print(f"   Fiyat: {current_price:.4f}")
        print(f"   %{exit_percentage*100:.0f} pozisyon çıkıldı")
        print(f"   Kâr/Zarar: {profit:.2f} USDT ({leveraged_profit_pct*100:.2f}%)")
        print(f"   Günlük Toplam: {self.daily_profit:.2f} USDT ({self.daily_profit_pct:.2f}%)\n")
        
        return {
            'position_id': position.id,
            'symbol': position.symbol,
            'stage': stage,
            'exit_price': current_price,
            'profit': round(profit, 4),
            'profit_pct': round(leveraged_profit_pct * 100, 2),
            'daily_total': round(self.daily_profit, 2),
            'daily_pct': round(self.daily_profit_pct, 2)
        }
    
    # ==========================================
    # DURUM RAPORU
    # ==========================================
    def get_status(self) -> Dict:
        """Cüzdan durum raporu"""
        self.check_new_day()
        
        active_positions = []
        for p in self.positions:
            active_positions.append({
                'id': p.id,
                'symbol': p.symbol,
                'type': p.type.value,
                'entry_price': p.entry_price,
                'capital': p.capital,
                'leverage': p.leverage,
                'status': p.status.value,
                'stage_1': p.stage_1_exit,
                'stage_2': p.stage_2_exit,
                'profit_loss': round(p.profit_loss, 4),
            })
        
        return {
            'total_capital': round(self.current_capital + self.daily_profit, 2),
            'initial_capital': self.initial_capital,
            'slot_size': round(self.slot_size, 2),
            'cash_reserve': round(self.cash_reserve, 2),
            'active_slots': self.get_active_slots(),
            'available_slots': 3 - self.get_active_slots(),
            'daily_profit': round(self.daily_profit, 2),
            'daily_profit_pct': round(self.daily_profit_pct, 2),
            'daily_target': round(self.daily_profit_target, 2),
            'target_reached': self.daily_profit >= self.daily_profit_target,
            'active_positions': active_positions,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': round(self.winning_trades / self.total_trades * 100, 1) if self.total_trades > 0 else 0
        }


# ==========================================
# DEFAULT CÜZDAN OLUŞTURMA
# ==========================================
def create_wallet(initial_capital: float = 1000.0) -> Wallet:
    """Yeni cüzdan oluştur"""
    return Wallet(
        initial_capital=initial_capital,
        current_capital=initial_capital,
        slot_size=initial_capital / 4,
        cash_reserve=initial_capital / 4,
    )