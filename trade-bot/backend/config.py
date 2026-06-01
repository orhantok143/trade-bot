# Binance API
BINANCE_BASE_URL = "https://api.binance.com/api/v3"

# Timeframe'ler
TIMEFRAMES = {
    "1d": "1d",
    "4h": "4h",
    "1h": "1h",
    "15m": "15m",
    "5m": "5m"
}

# Sıralı kontrol için
TF_ORDER = ["1d", "4h", "1h", "15m", "5m"]

# Her timeframe için gerekli bar sayısı
LOOKBACK_BARS = {
    "1d": 500,
    "4h": 500,
    "1h": 500,
    "15m": 500,
    "5m": 500
}

# Stable coin'ler
STABLE_COINS = ["USDC", "USDT", "DAI", "BUSD", "TUSD", "USDP", "FDUSD"]

# İlk kaç coin analiz edilecek
TOP_COINS = 25

# İndikatör parametreleri
EMA_FAST = 50
EMA_SLOW = 200
ADX_PERIOD = 14
ADX_THRESHOLD = 25
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD = 2
ATR_PERIOD = 14
VOLUME_PERIOD = 20

# Kontrol sıklığı (saniye)
CHECK_INTERVAL = 300  # 5 dakika