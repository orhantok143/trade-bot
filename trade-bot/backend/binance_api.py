import asyncio  # en başa ekle
import httpx
import pandas as pd
from config import (
    BINANCE_BASE_URL, STABLE_COINS, TOP_COINS, 
    TIMEFRAMES, LOOKBACK_BARS
)
from typing import Dict

class BinanceAPI:
    def __init__(self):
        self.base_url = BINANCE_BASE_URL
    
    async def get_top_coins(self) -> list:
        """İlk 25 USDT paritesini getir (stable coin'ler hariç)"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/ticker/24hr")
            tickers = response.json()
            
            usdt_pairs = [t for t in tickers if t['symbol'].endswith('USDT')]
            
            filtered = []
            for pair in usdt_pairs:
                base = pair['symbol'].replace('USDT', '')
                if base not in STABLE_COINS:
                    filtered.append(pair)
            
            filtered.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
            return [coin['symbol'] for coin in filtered[:TOP_COINS]]
    
    async def get_historical_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Belirli timeframe için geçmiş veriyi çek"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/klines",
                params={
                    "symbol": symbol,
                    "interval": timeframe,
                    "limit": LOOKBACK_BARS.get(timeframe, 500)
                }
            )
            data = response.json()
            
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume', 'quote_volume']:
                df[col] = df[col].astype(float)
            
            return df
    
    async def get_all_timeframes(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """Tüm timeframe'ler için veri çek"""
        result = {}
        for tf_name, tf_value in TIMEFRAMES.items():
            df = await self.get_historical_data(symbol, tf_value)
            result[tf_name] = df
            await asyncio.sleep(0.3)  # Her çağrı arası 300ms bekle (rate limit için)
        return result