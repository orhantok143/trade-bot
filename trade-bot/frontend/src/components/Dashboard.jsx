import CoinCard from './CoinCard'

function Dashboard({ signals, onSelectCoin, loading }) {
  if (loading) {
    return <div className="loading">⏳ Veriler yükleniyor...</div>
  }

  if (!signals) {
    return <div className="loading">⚠️ Bağlantı bekleniyor...</div>
  }

  const { enter_signals, wait_signals, none_signals, summary } = signals

  return (
    <div className="dashboard">
      <div className="summary-bar">
        <div className="summary-item enter">
          <span className="count">{summary?.enter || 0}</span>
          <span>GİRİŞ 🔥</span>
        </div>
        <div className="summary-item wait">
          <span className="count">{summary?.wait || 0}</span>
          <span>BEKLE 🟡</span>
        </div>
        <div className="summary-item none">
          <span className="count">{summary?.none || 0}</span>
          <span>İŞLEM YOK 🔴</span>
        </div>
      </div>

      {enter_signals?.length > 0 && (
        <div className="signal-section">
          <h2>🔥 GİRİŞ SİNYALLERİ</h2>
          <div className="coin-grid">
            {enter_signals.map(coin => (
              <CoinCard 
                key={coin.symbol} 
                coin={coin} 
                onClick={() => onSelectCoin(coin.symbol)}
              />
            ))}
          </div>
        </div>
      )}

      {wait_signals?.length > 0 && (
        <div className="signal-section">
          <h2>🟡 BEKLEMEDE</h2>
          <div className="coin-grid">
            {wait_signals.map(coin => (
              <CoinCard 
                key={coin.symbol} 
                coin={coin} 
                onClick={() => onSelectCoin(coin.symbol)}
              />
            ))}
          </div>
        </div>
      )}

      {none_signals?.length > 0 && (
        <div className="signal-section">
          <h2>🔴 İŞLEM YOK</h2>
          <div className="coin-grid collapsed">
            {none_signals.slice(0, 12).map(coin => (
              <CoinCard 
                key={coin.symbol} 
                coin={coin} 
                onClick={() => onSelectCoin(coin.symbol)}
                compact
              />
            ))}
            {none_signals.length > 12 && (
              <div className="show-more">+{none_signals.length - 12} daha...</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard