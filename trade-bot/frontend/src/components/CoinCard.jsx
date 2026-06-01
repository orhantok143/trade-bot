function CoinCard({ coin, onClick, compact = false }) {
  const getSignalColor = (signal) => {
    switch(signal) {
      case 'ENTER': return '#00ff88'
      case 'WAIT': return '#ffaa00'
      case 'NONE': return '#ff4444'
      default: return '#888'
    }
  }

  const getSignalEmoji = (signal) => {
    switch(signal) {
      case 'ENTER': return '🔥'
      case 'WAIT': return '🟡'
      case 'NONE': return '🔴'
      default: return '❓'
    }
  }

  if (compact) {
    return (
      <div className="coin-card compact" onClick={onClick}>
        <span className="coin-symbol">{coin.symbol.replace('USDT', '')}</span>
        <span className="coin-signal" style={{color: getSignalColor(coin.signal)}}>
          {getSignalEmoji(coin.signal)}
        </span>
      </div>
    )
  }

  return (
    <div 
      className={`coin-card ${coin.signal === 'ENTER' ? 'highlight' : ''}`}
      onClick={onClick}
    >
      <div className="card-header">
        <span className="coin-symbol">{coin.symbol.replace('USDT', '')}</span>
        <span className="coin-price">${coin.price?.toFixed(4)}</span>
      </div>
      
      <div className="card-signal" style={{color: getSignalColor(coin.signal)}}>
        {getSignalEmoji(coin.signal)} {coin.signal}
      </div>
      
      <div className="card-score">
        Skor: {coin.total_score}/{coin.max_score}
      </div>
      
      {coin.direction && (
        <div className={`card-direction ${coin.direction?.toLowerCase()}`}>
          {coin.direction}
        </div>
      )}
      
      {coin.summary && (
        <div className="card-summary">{coin.summary}</div>
      )}
    </div>
  )
}

export default CoinCard