import { useState, useEffect } from 'react'

function LogPanel() {
  const [activeLogTab, setActiveLogTab] = useState('signals') // signals | trades | backtest
  const [signals, setSignals] = useState([])
  const [trades, setTrades] = useState([])
  const [backtest, setBacktest] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchLogs()
    const interval = setInterval(fetchLogs, 15000)
    return () => clearInterval(interval)
  }, [activeLogTab])

  const fetchLogs = async () => {
    try {
      if (activeLogTab === 'signals') {
        const res = await fetch(`${API_URL}/api/logs/signals?limit=50`)
        const data = await res.json()
        setSignals(data.signals || [])
      } else if (activeLogTab === 'trades') {
        const res = await fetch(`${API_URL}/api/logs/trades?limit=50`)
        const data = await res.json()
        setTrades(data.trades || [])
      } else if (activeLogTab === 'backtest') {
        const res = await fetch(`${API_URL}/api/logs/backtest?limit=100`)
        const data = await res.json()
        setBacktest(data.logs || [])
      }
      setLoading(false)
    } catch (e) {
      console.error('Log çekme hatası:', e)
      setLoading(false)
    }
  }

  const formatTime = (timestamp) => {
    if (!timestamp) return '-'
    const d = new Date(timestamp)
    return d.toLocaleTimeString('tr-TR')
  }

  const getLogTypeColor = (type) => {
    switch(type) {
      case 'POSITION_OPEN': return '#00aaff'
      case 'POSITION_EXIT': return '#ffaa00'
      case 'WALLET_SNAPSHOT': return '#888'
      case 'SIGNAL': return '#00ff88'
      default: return '#aaa'
    }
  }

  return (
    <div className="log-panel">
      <h2>📋 Sistem Logları</h2>

      <div className="log-tabs">
        <button 
          className={`log-tab ${activeLogTab === 'signals' ? 'active' : ''}`}
          onClick={() => setActiveLogTab('signals')}
        >
          📡 Sinyaller ({signals.length})
        </button>
        <button 
          className={`log-tab ${activeLogTab === 'trades' ? 'active' : ''}`}
          onClick={() => setActiveLogTab('trades')}
        >
          💹 İşlemler ({trades.length})
        </button>
        <button 
          className={`log-tab ${activeLogTab === 'backtest' ? 'active' : ''}`}
          onClick={() => setActiveLogTab('backtest')}
        >
          📊 Backtest ({backtest.length})
        </button>
      </div>

      {loading ? (
        <div className="loading">⏳ Loglar yükleniyor...</div>
      ) : (
        <div className="log-list">
          {/* Sinyal Logları */}
          {activeLogTab === 'signals' && (
            <>
              {signals.length === 0 ? (
                <div className="no-logs">Henüz sinyal logu yok</div>
              ) : (
                signals.slice().reverse().map((log, i) => (
                  <div key={i} className="log-item signal">
                    <span className="log-time">{formatTime(log.timestamp)}</span>
                    <span className="log-symbol">{log.symbol}</span>
                    <span className={`log-signal ${log.signal?.toLowerCase()}`}>
                      {log.signal}
                    </span>
                    <span className="log-score">
                      {log.total_score}/{log.max_score}
                    </span>
                    <span className="log-summary">{log.summary}</span>
                  </div>
                ))
              )}
            </>
          )}

          {/* İşlem Logları */}
          {activeLogTab === 'trades' && (
            <>
              {trades.length === 0 ? (
                <div className="no-logs">Henüz işlem logu yok</div>
              ) : (
                trades.slice().reverse().map((log, i) => (
                  <div key={i} className={`log-item ${log.type === 'POSITION_OPEN' ? 'open' : 'exit'}`}>
                    <span className="log-time">{formatTime(log.timestamp)}</span>
                    <span className="log-type" style={{color: getLogTypeColor(log.type)}}>
                      {log.type === 'POSITION_OPEN' ? '🔵 AÇIŞ' : '🔴 ÇIKIŞ'}
                    </span>
                    <span className="log-symbol">{log.symbol}</span>
                    {log.type === 'POSITION_OPEN' ? (
                      <>
                        <span className="log-detail">{log.direction} {log.leverage}x</span>
                        <span className="log-detail">${log.capital?.toFixed(2)}</span>
                      </>
                    ) : (
                      <>
                        <span className="log-detail">Aşama {log.stage}</span>
                        <span className="log-detail" style={{color: log.profit >= 0 ? '#00ff88' : '#ff4444'}}>
                          {log.profit >= 0 ? '+' : ''}{log.profit?.toFixed(4)}
                        </span>
                      </>
                    )}
                  </div>
                ))
              )}
            </>
          )}

          {/* Backtest Logları */}
          {activeLogTab === 'backtest' && (
            <>
              {backtest.length === 0 ? (
                <div className="no-logs">Henüz backtest logu yok</div>
              ) : (
                backtest.slice().reverse().map((log, i) => (
                  <div key={i} className="log-item backtest">
                    <span className="log-time">{formatTime(log.timestamp)}</span>
                    <span className="log-type" style={{color: getLogTypeColor(log.type)}}>
                      {log.type}
                    </span>
                    {log.symbol && <span className="log-symbol">{log.symbol}</span>}
                    {log.signal && <span className="log-signal">{log.signal}</span>}
                    {log.profit !== undefined && (
                      <span className="log-detail" style={{color: log.profit >= 0 ? '#00ff88' : '#ff4444'}}>
                        {log.profit >= 0 ? '+' : ''}{log.profit?.toFixed(4)}
                      </span>
                    )}
                    {log.daily_profit !== undefined && (
                      <span className="log-detail">
                        Günlük: ${log.daily_profit?.toFixed(2)}
                      </span>
                    )}
                  </div>
                ))
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default LogPanel