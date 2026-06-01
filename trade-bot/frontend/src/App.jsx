import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import CoinDetail from './components/CoinDetail'
import WalletPanel from './components/WalletPanel'
import API_URL from './config'
import LogPanel from './components/LogPanel';

function App() {
  const [selectedCoin, setSelectedCoin] = useState(null)
  const [signals, setSignals] = useState(null)
  const [wallet, setWallet] = useState(null)
  const [activeTab, setActiveTab] = useState('dashboard') // dashboard | wallet | logs
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)

  useEffect(() => {
    fetchAllData()
    const interval = setInterval(fetchAllData, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchAllData = async () => {
    try {
      const [signalsRes, walletRes] = await Promise.all([
        fetch(`${API_URL}/api/signals`),
        fetch(`${API_URL}/api/wallet`)
      ])
      
      const signalsData = await signalsRes.json()
      const walletData = await walletRes.json()
      
      setSignals(signalsData)
      setWallet(walletData)
      setLastUpdate(signalsData.last_update)
      setLoading(false)
    } catch (error) {
      console.error('Veri çekme hatası:', error)
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🤖 Multi-TF Trade Bot</h1>
        <div className="header-info">
          <span className="timeframes">1D → 4H → 1H → 15m → 5m</span>
          {lastUpdate && (
            <span className="update-time">
              Son güncelleme: {new Date(lastUpdate).toLocaleTimeString('tr-TR')}
            </span>
          )}
        </div>
      </header>

      {/* Hızlı Cüzdan Özeti */}
      {wallet && (
        <div className="wallet-mini-bar">
          <div className="mini-item">
            <span className="mini-label">Sermaye</span>
            <span className="mini-value">${wallet.total_capital?.toFixed(2)}</span>
          </div>
          <div className="mini-item profit">
            <span className="mini-label">Günlük Kâr</span>
            <span className="mini-value" style={{color: wallet.daily_profit >= 0 ? '#00ff88' : '#ff4444'}}>
              {wallet.daily_profit >= 0 ? '+' : ''}{wallet.daily_profit?.toFixed(2)} USDT
            </span>
          </div>
          <div className="mini-item">
            <span className="mini-label">Hedef</span>
            <span className="mini-value">{wallet.target_reached ? '✅' : '🎯'} %{wallet.daily_profit_pct?.toFixed(2)}</span>
          </div>
          <div className="mini-item">
            <span className="mini-label">Slot</span>
            <span className="mini-value">{wallet.active_slots}/3</span>
          </div>
          <div className="mini-item">
            <span className="mini-label">Win Rate</span>
            <span className="mini-value">%{wallet.win_rate}</span>
          </div>
        </div>
      )}

      {/* Tab Menü */}
      <div className="tab-menu">
        <button 
          className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          📊 Sinyaller
        </button>
        <button 
          className={`tab-btn ${activeTab === 'wallet' ? 'active' : ''}`}
          onClick={() => setActiveTab('wallet')}
        >
          💰 Cüzdan
        </button>
        <button 
          className={`tab-btn ${activeTab === 'logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          📋 Loglar
        </button>
      </div>
      
      <main>
        {selectedCoin ? (
          <CoinDetail 
            symbol={selectedCoin} 
            onBack={() => setSelectedCoin(null)} 
          />
        ) : (
          <>
            {activeTab === 'dashboard' && (
              <Dashboard 
                signals={signals} 
                onSelectCoin={setSelectedCoin}
                loading={loading}
              />
            )}
            {activeTab === 'wallet' && (
              <WalletPanel wallet={wallet} />
            )}
            {activeTab === 'logs' && (
              <LogPanel />
            )}
          </>
        )}
      </main>
    </div>
  )
}

export default App