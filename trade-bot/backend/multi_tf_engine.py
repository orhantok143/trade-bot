import pandas as pd
import numpy as np
from typing import Dict
from indicators import Indicators


class MultiTimeframeEngine:
    """
    Çoklu timeframe sinyal motoru
    
    Hiyerarşi:
    1D   → Anayasa (Rejim)
    4H   → Katman 1 (Trend)
    1H   → Katman 2 (Düzeltme)
    15m  → Katman 3 (Divergence)
    5m   → Tetik (Son onay)
    """
    
    def __init__(self, data: Dict[str, pd.DataFrame]):
        self.data = data
        self.indicators = {}
        
        for tf, df in data.items():
            self.indicators[tf] = Indicators.calculate_all(df)
    
    def get_latest(self, tf: str) -> pd.Series:
        return self.indicators[tf].iloc[-1]
    
    # ==========================================
    # 1D - ANAYASA
    # ==========================================
    def check_constitution(self) -> Dict:
        latest = self.get_latest("1d")
        ema_50 = latest['EMA_50']
        ema_200 = latest['EMA_200']
        
        if pd.isna(ema_50) or pd.isna(ema_200):
            return {
                'tf': '1D', 'name': 'ANAYASA', 'passed': False,
                'regime': 'UNKNOWN', 'allowed': 'NONE',
                'details': 'EMA değerleri hesaplanamadı'
            }
        
        if ema_50 > ema_200:
            regime = 'BULL'
            allowed = 'LONG_ONLY'
            details = f'Golden Cross aktif (50 EMA: {ema_50:.2f} > 200 EMA: {ema_200:.2f})'
        else:
            regime = 'BEAR'
            allowed = 'SHORT_ONLY'
            details = f'Death Cross aktif (50 EMA: {ema_50:.2f} < 200 EMA: {ema_200:.2f})'
        
        return {
            'tf': '1D', 'name': 'ANAYASA', 'passed': True,
            'regime': regime, 'allowed': allowed, 'details': details,
            'ema_50': round(float(ema_50), 2), 'ema_200': round(float(ema_200), 2)
        }
    
    # ==========================================
    # 4H - KATMAN 1 (Trend)
    # ==========================================
    def check_trend(self, direction: str) -> Dict:
        latest = self.get_latest("4h")
        price = latest['close']
        ema_50 = latest['EMA_50']
        adx = latest['ADX']
        volume_above = latest['Volume_Above_Avg']
        
        score = 0
        checks = {}
        
        if not pd.isna(ema_50) and ema_50 > 0:
            distance = abs(price - ema_50) / ema_50
            near_ema = distance < 0.03
            checks['price_near_ema'] = {
                'passed': near_ema,
                'value': f'%{distance*100:.1f} uzaklık',
                'detail': f'Fiyat: {price:.2f}, EMA50: {ema_50:.2f}'
            }
            if near_ema:
                score += 1
        else:
            checks['price_near_ema'] = {'passed': False, 'value': 'Hesaplanamadı', 'detail': ''}
        
        adx_strong = not pd.isna(adx) and adx > 25
        checks['adx_strong'] = {
            'passed': adx_strong,
            'value': f'ADX: {adx:.1f}' if not pd.isna(adx) else 'N/A',
            'detail': 'Trend güçlü' if adx_strong else 'Trend zayıf veya yok'
        }
        if adx_strong:
            score += 1
        
        checks['volume_above'] = {
            'passed': bool(volume_above),
            'value': f'Hacim: {latest["volume"]:.0f}, Ort: {latest["Volume_MA"]:.0f}',
            'detail': 'Para girişi var' if volume_above else 'Hacim düşük'
        }
        if volume_above:
            score += 1
        
        passed = score >= 2
        
        return {
            'tf': '4H', 'name': 'KATMAN 1 - TREND', 'passed': passed,
            'score': score, 'max_score': 3, 'checks': checks,
            'details': f'Trend onayı: {score}/3' + (' ✅' if passed else ' ❌')
        }
    
    # ==========================================
    # 1H - KATMAN 2 (Düzeltme)
    # ==========================================
    def check_correction(self, direction: str) -> Dict:
        latest = self.get_latest("1h")
        rsi = latest['RSI']
        in_fibo = latest['In_Fibo_Zone']
        bb_position = latest['BB_Position']
        volume_above = latest['Volume_Above_Avg']
        
        score = 0
        checks = {}
        
        if direction == 'LONG':
            checks['in_fibo'] = {
                'passed': bool(in_fibo),
                'value': f'Fibo: {latest["Fibo_382"]:.2f} - {latest["Fibo_618"]:.2f}',
                'detail': 'Deep bölgesinde' if in_fibo else 'Fibo dışında'
            }
            if in_fibo:
                score += 1
            
            rsi_ok = not pd.isna(rsi) and 30 <= rsi <= 50
            checks['rsi_deep'] = {
                'passed': rsi_ok,
                'value': f'RSI: {rsi:.1f}',
                'detail': 'Dip bölgesinde' if rsi_ok else 'RSI uygun değil'
            }
            if rsi_ok:
                score += 1
            
            bb_ok = not pd.isna(bb_position) and bb_position < 0.3
            checks['bb_low'] = {
                'passed': bb_ok,
                'value': f'BB Pozisyon: %{bb_position*100:.0f}',
                'detail': 'Alt banda yakın' if bb_ok else 'Bant dışı'
            }
            if bb_ok:
                score += 1
        else:
            checks['in_fibo'] = {
                'passed': bool(in_fibo),
                'value': f'Fibo: {latest["Fibo_382"]:.2f} - {latest["Fibo_618"]:.2f}',
                'detail': 'Peak bölgesinde' if in_fibo else 'Fibo dışında'
            }
            if in_fibo:
                score += 1
            
            rsi_ok = not pd.isna(rsi) and 50 <= rsi <= 70
            checks['rsi_peak'] = {
                'passed': rsi_ok,
                'value': f'RSI: {rsi:.1f}',
                'detail': 'Tepe bölgesinde' if rsi_ok else 'RSI uygun değil'
            }
            if rsi_ok:
                score += 1
            
            bb_ok = not pd.isna(bb_position) and bb_position > 0.7
            checks['bb_high'] = {
                'passed': bb_ok,
                'value': f'BB Pozisyon: %{bb_position*100:.0f}',
                'detail': 'Üst banda yakın' if bb_ok else 'Bant dışı'
            }
            if bb_ok:
                score += 1
        
        checks['volume_declining'] = {
            'passed': not bool(volume_above),
            'value': f'Hacim: {latest["volume"]:.0f}',
            'detail': 'Tükenme var' if not volume_above else 'Hacim hala yüksek'
        }
        if not volume_above:
            score += 1
        
        passed = score >= 3
        
        return {
            'tf': '1H', 'name': 'KATMAN 2 - DÜZELTME', 'passed': passed,
            'score': score, 'max_score': 4, 'checks': checks,
            'details': f'{"Deep" if direction == "LONG" else "Peak"} onayı: {score}/4' + (' ✅' if passed else ' ❌')
        }
    
    # ==========================================
    # 15m - KATMAN 3 (Divergence)
    # ==========================================
    def check_divergence(self, direction: str) -> Dict:
        latest = self.get_latest("15m")
        bullish_div = latest['Bullish_Div']
        bearish_div = latest['Bearish_Div']
        macd_hist = latest['MACD_Histogram']
        obv = latest['OBV']
        
        score = 0
        checks = {}
        
        if direction == 'LONG':
            checks['rsi_div'] = {
                'passed': bool(bullish_div),
                'value': 'Var' if bullish_div else 'Yok',
                'detail': 'RSI Bullish divergence' if bullish_div else 'RSI uyumsuzluk yok'
            }
            if bullish_div:
                score += 1
            
            macd_rising = not pd.isna(macd_hist) and macd_hist > 0
            checks['macd_rising'] = {
                'passed': macd_rising,
                'value': f'MACD Hist: {macd_hist:.4f}',
                'detail': 'MACD yükseliyor' if macd_rising else 'MACD zayıf'
            }
            if macd_rising:
                score += 1
            
            checks['obv_rising'] = {
                'passed': not pd.isna(obv),
                'value': 'Kontrol edildi',
                'detail': 'OBV takip ediliyor'
            }
            if not pd.isna(obv):
                score += 1
        else:
            checks['rsi_div'] = {
                'passed': bool(bearish_div),
                'value': 'Var' if bearish_div else 'Yok',
                'detail': 'RSI Bearish divergence' if bearish_div else 'RSI uyumsuzluk yok'
            }
            if bearish_div:
                score += 1
            
            macd_falling = not pd.isna(macd_hist) and macd_hist < 0
            checks['macd_falling'] = {
                'passed': macd_falling,
                'value': f'MACD Hist: {macd_hist:.4f}',
                'detail': 'MACD düşüyor' if macd_falling else 'MACD güçlü'
            }
            if macd_falling:
                score += 1
            
            checks['obv_falling'] = {
                'passed': not pd.isna(obv),
                'value': 'Kontrol edildi',
                'detail': 'OBV takip ediliyor'
            }
            if not pd.isna(obv):
                score += 1
        
        passed = score >= 2
        
        return {
            'tf': '15m', 'name': 'KATMAN 3 - DİVERGENCE', 'passed': passed,
            'score': score, 'max_score': 3, 'checks': checks,
            'details': f'Divergence onayı: {score}/3' + (' ✅' if passed else ' ❌')
        }
    
    # ==========================================
    # 5m - TETİK
    # ==========================================
    def check_trigger(self, direction: str) -> Dict:
        latest = self.get_latest("5m")
        price = latest['close']
        open_price = latest['open']
        volume = latest['volume']
        volume_ma = latest['Volume_MA']
        
        score = 0
        checks = {}
        
        if direction == 'LONG':
            bull_candle = price > open_price
            checks['candle_direction'] = {
                'passed': bull_candle,
                'value': f'Açılış: {open_price:.2f}, Kapanış: {price:.2f}',
                'detail': 'Yükseliş mumu' if bull_candle else 'Düşüş mumu'
            }
            if bull_candle:
                score += 1
        else:
            bear_candle = price < open_price
            checks['candle_direction'] = {
                'passed': bear_candle,
                'value': f'Açılış: {open_price:.2f}, Kapanış: {price:.2f}',
                'detail': 'Düşüş mumu' if bear_candle else 'Yükseliş mumu'
            }
            if bear_candle:
                score += 1
        
        volume_spike = not pd.isna(volume_ma) and volume > volume_ma * 1.5
        checks['volume_spike'] = {
            'passed': volume_spike,
            'value': f'Hacim: {volume:.0f}, Ort: {volume_ma:.0f}',
            'detail': 'Hacim patlaması var' if volume_spike else 'Hacim normal'
        }
        if volume_spike:
            score += 1
        
        passed = score >= 1
        
        return {
            'tf': '5m', 'name': 'TETİK', 'passed': passed,
            'score': score, 'max_score': 2, 'checks': checks,
            'details': f'Tetik onayı: {score}/2' + (' ✅' if passed else ' ❌')
        }
    
    # ==========================================
    # ANA SİNYAL ÜRETİM
    # ==========================================
    def generate_signal(self) -> Dict:
        constitution = self.check_constitution()
        
        if not constitution['passed'] or constitution['allowed'] == 'NONE':
            return {
                'signal': 'NONE', 'direction': None,
                'total_score': 0, 'max_score': 5,
                'constitution': self._clean_dict(constitution),
                'layers': {
                    'constitution': self._clean_dict(constitution),
                    'trend': None, 'correction': None,
                    'divergence': None, 'trigger': None
                },
                'summary': 'Rejim belirsiz, işlem yok'
            }
        
        direction = 'LONG' if constitution['allowed'] == 'LONG_ONLY' else 'SHORT'
        total_score = 1
        max_score = 5
        
        trend = self.check_trend(direction)
        if trend['passed']:
            total_score += 1
        
        correction = self.check_correction(direction)
        if correction['passed']:
            total_score += 1
        
        divergence = self.check_divergence(direction)
        if divergence['passed']:
            total_score += 1
        
        trigger = self.check_trigger(direction)
        if trigger['passed']:
            total_score += 1
        
        if total_score >= 4:
            signal = 'ENTER'
            summary = f'🔥 GİRİŞ SİNYALİ - {direction}'
        elif total_score >= 2:
            signal = 'WAIT'
            summary = f'🟡 BEKLE - {total_score}/{max_score} katman onaylı'
        else:
            signal = 'NONE'
            summary = f'🔴 İŞLEM YOK - {total_score}/{max_score} katman onaylı'
        
        return {
            'signal': signal,
            'direction': direction,
            'total_score': int(total_score),
            'max_score': int(max_score),
            'constitution': self._clean_dict(constitution),
            'layers': {
                'constitution': self._clean_dict(constitution),
                'trend': self._clean_dict(trend),
                'correction': self._clean_dict(correction),
                'divergence': self._clean_dict(divergence),
                'trigger': self._clean_dict(trigger)
            },
            'summary': summary
        }
    
    # ==========================================
    # TEMİZLEME YARDIMCILARI
    # ==========================================
    def _clean_value(self, value):
        if isinstance(value, (bool, np.bool_)):
            return bool(value)
        elif isinstance(value, (np.integer,)):
            return int(value)
        elif isinstance(value, (np.floating, np.float64)):
            if np.isnan(value) or np.isinf(value):
                return None
            return float(value)
        elif isinstance(value, np.ndarray):
            return value.tolist()
        elif isinstance(value, dict):
            return self._clean_dict(value)
        elif isinstance(value, (str, int, float, type(None))):
            return value
        else:
            return str(value)
    
    def _clean_dict(self, d):
        if d is None:
            return None
        return {key: self._clean_value(value) for key, value in d.items()}