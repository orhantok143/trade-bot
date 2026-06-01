from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from binance_api import BinanceAPI
from multi_tf_engine import MultiTimeframeEngine
from wallet import create_wallet
from logger import logger
from datetime import datetime
from contextlib import asynccontextmanager


# ==========================================
# LIFESPAN
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    await analyze_all_coins()
    yield


# ==========================================
# APP
# ==========================================
app = FastAPI(title="Multi-TF Trade Bot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# GLOBAL DEĞİŞKENLER
# ==========================================
binance = BinanceAPI()
wallet = create_wallet(initial_capital=1000.0)

cached_results = {
    'last_update': None,
    'coins': [],
    'results': []
}


# ==========================================
# ANALİZ FONKSİYONU
# ==========================================
async def analyze_all_coins():
    global cached_results
    
    print(f"\n{'='*50}")
    print(f"[{datetime.now()}] ANALİZ BAŞLADI...")
    
    try:
        coins = await binance.get_top_coins()
        results = []
        
        for symbol in coins:
            try:
                data = await binance.get_all_timeframes(symbol)
                engine = MultiTimeframeEngine(data)
                signal = engine.generate_signal()
                
                price = data['5m'].iloc[-1]['close'] if '5m' in data else 0
                
                result = {
                    'symbol': symbol,
                    'price': round(float(price), 4),
                    'signal': signal['signal'],
                    'direction': signal['direction'],
                    'total_score': signal['total_score'],
                    'max_score': signal['max_score'],
                    'summary': signal['summary'],
                    'constitution': signal['constitution'],
                    'layers': signal['layers']
                }
                
                if signal['signal'] == 'ENTER':
                    logger.log_signal(symbol, result)
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    'symbol': symbol,
                    'error': str(e),
                    'signal': 'ERROR'
                })
        
        signal_order = {'ENTER': 0, 'WAIT': 1, 'NONE': 2, 'ERROR': 3}
        results.sort(key=lambda x: signal_order.get(x.get('signal', 'ERROR'), 3))
        
        cached_results = {
            'last_update': datetime.now().isoformat(),
            'coins': coins,
            'results': results
        }
        
        logger.log_wallet_snapshot(wallet.get_status())
        await check_positions_and_exit()
        
        print(f"[{datetime.now()}] Analiz tamamlandı. {len(results)} coin kontrol edildi.")
        enter_count = sum(1 for r in results if r.get('signal') == 'ENTER')
        if enter_count > 0:
            print(f"🔥 {enter_count} GİRİŞ sinyali bulundu!")
        
    except Exception as e:
        print(f"Analiz hatası: {e}")

     # >>> ENTER sinyalleri için otomatik pozisyon aç <<<
    for result in results:
        if result.get('signal') == 'ENTER':
            symbol = result['symbol']
            price = result['price']
            
            # Pozisyon açmayı dene
            position = wallet.open_position(symbol, result, price)
            
            if position:
                logger.log_position_open({
                    'id': position.id,
                    'symbol': position.symbol,
                    'type': position.type,
                    'entry_price': position.entry_price,
                    'capital': position.capital,
                    'leverage': position.leverage,
                    'quantity': position.quantity,
                    'stop_loss': position.stop_loss,
                    'total_score': position.total_score
                })
                print(f"✅ Otomatik pozisyon açıldı: {symbol}")


async def check_positions_and_exit():
    for position in wallet.positions[:]:
        results = cached_results.get('results', [])
        coin_data = None
        for r in results:
            if r.get('symbol') == position.symbol:
                coin_data = r
                break
        
        if not coin_data:
            continue
        
        current_price = coin_data.get('price', 0)
        layers = coin_data.get('layers', {})
        
        exit_stage = wallet.check_exit_conditions(position, current_price, layers)
        
        if exit_stage > 0:
            result = wallet.execute_exit(position, current_price, exit_stage)
            logger.log_position_exit(result)


# ==========================================
# SCHEDULER
# ==========================================
scheduler = AsyncIOScheduler()
scheduler.add_job(analyze_all_coins, 'interval', seconds=300)
scheduler.start()


# ==========================================
# ENDPOINT'LER
# ==========================================

@app.get("/")
async def root():
    return {
        "message": "Multi-Timeframe Trade Bot API",
        "timeframes": ["1d", "4h", "1h", "15m", "5m"],
        "update_interval": "5 dakika",
        "last_update": cached_results.get('last_update')
    }


@app.get("/api/coins")
async def get_coins():
    return {
        'coins': cached_results.get('coins', []),
        'count': len(cached_results.get('coins', [])),
        'last_update': cached_results.get('last_update')
    }


@app.get("/api/signals")
async def get_signals():
    results = cached_results.get('results', [])
    
    enter = [r for r in results if r.get('signal') == 'ENTER']
    wait = [r for r in results if r.get('signal') == 'WAIT']
    none_signals = [r for r in results if r.get('signal') == 'NONE']
    errors = [r for r in results if r.get('signal') == 'ERROR']
    
    return {
        'last_update': cached_results.get('last_update'),
        'summary': {
            'enter': len(enter),
            'wait': len(wait),
            'none': len(none_signals),
            'errors': len(errors),
            'total': len(results)
        },
        'enter_signals': enter,
        'wait_signals': wait,
        'none_signals': none_signals,
        'errors': errors
    }


@app.get("/api/signal/{symbol}")
async def get_coin_signal(symbol: str):
    results = cached_results.get('results', [])
    for r in results:
        if r.get('symbol') == symbol:
            return r
    return {'error': f'{symbol} bulunamadı'}


@app.get("/api/analyze")
async def force_analyze():
    await analyze_all_coins()
    return {'status': 'ok', 'last_update': cached_results.get('last_update')}


# ==========================================
# CÜZDAN ENDPOINT'LERİ
# ==========================================

@app.get("/api/wallet")
async def get_wallet_status():
    return wallet.get_status()


@app.post("/api/wallet/open/{symbol}")
async def open_position(symbol: str):
    results = cached_results.get('results', [])
    coin_data = None
    for r in results:
        if r.get('symbol') == symbol:
            coin_data = r
            break
    
    if not coin_data:
        return {'error': f'{symbol} için sinyal bulunamadı'}
    
    price = coin_data.get('price', 0)
    position = wallet.open_position(symbol, coin_data, price)
    
    if position:
        logger.log_position_open({
            'id': position.id,
            'symbol': position.symbol,
            'type': position.type,
            'entry_price': position.entry_price,
            'capital': position.capital,
            'leverage': position.leverage,
            'quantity': position.quantity,
            'stop_loss': position.stop_loss,
            'total_score': position.total_score
        })
        return {'status': 'opened', 'position_id': position.id}
    return {'status': 'rejected', 'reason': 'Sinyal uygun değil veya slot dolu'}


# ==========================================
# LOG ENDPOINT'LERİ
# ==========================================

@app.get("/api/logs/signals")
async def get_signal_logs(limit: int = Query(default=50)):
    return {'signals': logger.get_today_signals()[-limit:]}


@app.get("/api/logs/trades")
async def get_trade_logs(limit: int = Query(default=50)):
    return {'trades': logger.get_today_trades()[-limit:]}


@app.get("/api/logs/backtest")
async def get_backtest_logs(limit: int = Query(default=100)):
    return {'logs': logger.get_backtest_logs(limit)}


@app.get("/api/logs/history")
async def get_signal_history():
    return {'history': logger.get_all_signals_history()}


# ==========================================
# BAŞLAT
# ==========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)