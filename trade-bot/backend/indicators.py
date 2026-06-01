import pandas as pd
import numpy as np

class Indicators:
    @staticmethod
    def calculate_emas(df):
        """EMA 50 ve 200"""
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
        df['EMA_50_above_200'] = df['EMA_50'] > df['EMA_200']
        return df
    
    @staticmethod
    def calculate_adx(df, period=14):
        """ADX hesapla"""
        high, low, close = df['high'], df['low'], df['close']
        
        plus_dm = high.diff()
        minus_dm = low.diff().abs() * -1  # negatif yap
        
        # Doğru DM hesaplama
        plus_dm = np.where((high.diff() > low.diff().abs()) & (high.diff() > 0), high.diff(), 0)
        minus_dm = np.where((low.diff().abs() > high.diff()) & (low.diff() < 0), low.diff().abs(), 0)
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.ewm(span=period, adjust=False).mean()
        plus_di = 100 * (pd.Series(plus_dm).ewm(span=period, adjust=False).mean() / atr)
        minus_di = 100 * (pd.Series(minus_dm).ewm(span=period, adjust=False).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        df['ADX'] = dx.ewm(span=period, adjust=False).mean()
        df['ADX_Strong'] = df['ADX'] > 25
        return df
    
    @staticmethod
    def calculate_rsi(df, period=14):
        """RSI hesapla"""
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df
    
    @staticmethod
    def calculate_macd(df):
        """MACD hesapla"""
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema_12 - ema_26
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        return df
    
    @staticmethod
    def calculate_bollinger(df, period=20, std=2):
        """Bollinger Bands"""
        df['BB_Middle'] = df['close'].rolling(period).mean()
        bb_std = df['close'].rolling(period).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * std)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * std)
        df['BB_Position'] = (df['close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        return df
    
    @staticmethod
    def calculate_obv(df):
        """OBV hesapla"""
        df['OBV'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        return df
    
    @staticmethod
    def calculate_atr(df, period=14):
        """ATR"""
        high, low, close = df['high'], df['low'], df['close']
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATR'] = tr.ewm(span=period, adjust=False).mean()
        return df
    
    @staticmethod
    def calculate_volume_ma(df, period=20):
        """Hacim ortalaması"""
        df['Volume_MA'] = df['volume'].rolling(period).mean()
        df['Volume_Above_Avg'] = df['volume'] > df['Volume_MA']
        return df
    
    @staticmethod
    def calculate_fibonacci(df, lookback=50):
        """Fibonacci seviyeleri"""
        df['Fibo_High'] = df['high'].rolling(lookback).max()
        df['Fibo_Low'] = df['low'].rolling(lookback).min()
        df['Fibo_Range'] = df['Fibo_High'] - df['Fibo_Low']
        df['Fibo_382'] = df['Fibo_High'] - df['Fibo_Range'] * 0.382
        df['Fibo_500'] = df['Fibo_High'] - df['Fibo_Range'] * 0.500
        df['Fibo_618'] = df['Fibo_High'] - df['Fibo_Range'] * 0.618
        df['In_Fibo_Zone'] = (df['close'] >= df['Fibo_618']) & (df['close'] <= df['Fibo_382'])
        return df
    
    @staticmethod
    def find_divergence(df, lookback=20):
        """Bullish/Bearish divergence tespiti"""
        # Basitleştirilmiş divergence kontrolü
        df['Price_Low_20'] = df['low'].rolling(lookback).min()
        df['Price_High_20'] = df['high'].rolling(lookback).max()
        df['RSI_Low_20'] = df['RSI'].rolling(lookback).min()
        df['RSI_High_20'] = df['RSI'].rolling(lookback).max()
        
        # Fiyat düşük dip yaparken RSI yüksek dip = Bullish
        df['Bullish_Div'] = (
            (df['low'] <= df['Price_Low_20'].shift(1)) & 
            (df['RSI'] > df['RSI_Low_20'].shift(1))
        ).astype(int)
        
        # Fiyat yüksek tepe yaparken RSI düşük tepe = Bearish
        df['Bearish_Div'] = (
            (df['high'] >= df['Price_High_20'].shift(1)) & 
            (df['RSI'] < df['RSI_High_20'].shift(1))
        ).astype(int)
        
        return df
    
    @staticmethod
    def calculate_all(df):
        """Tüm indikatörleri hesapla"""
        df = df.copy()
        df = Indicators.calculate_emas(df)
        df = Indicators.calculate_adx(df)
        df = Indicators.calculate_rsi(df)
        df = Indicators.calculate_macd(df)
        df = Indicators.calculate_bollinger(df)
        df = Indicators.calculate_obv(df)
        df = Indicators.calculate_atr(df)
        df = Indicators.calculate_volume_ma(df)
        df = Indicators.calculate_fibonacci(df)
        df = Indicators.find_divergence(df)
        return df