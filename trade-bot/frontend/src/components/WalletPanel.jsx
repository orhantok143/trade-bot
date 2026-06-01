import { useState, useEffect } from 'react'

function WalletPanel({ wallet: initialWallet }) {
  const [wallet, setWallet] = useState(initialWallet)

  useEffect(() => {
    if (initialWallet) setWallet(initialWallet)
  }, [initialWallet])

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/wallet/`)
        const data = await res.json()
        setWallet(data)
      } catch (e) {
        console.error('Cüzdan güncelleme hatası:', e)
      }
    }, 10000) // 10 saniyede bir
    return () => clearInterval(interval)
  }, [])

  if (!wallet) {
    return <div className="loading">⏳ Cüzdan yükleniyor...</div>
  }

  const profitColor = wallet.daily_profit >= 0 ? '#00ff88' : '#ff4444'

  return (
    <div className="wallet-panel">
      <h2>💰 Cüzdan Durumu</h2>

      <div className="wallet-grid">
        <div className="wallet-card main">
          <span className="wallet-label">Toplam Sermaye</span>
          <span className="wallet-value large">${wallet.total_capital?.toFixed(2)}</span>
          <span className="wallet-sub">Başlangıç: ${wallet.initial_capital?.toFixed(2)}</span>
        </div>

        <div className="wallet-card">
          <span className="wallet-label">Günlük Kâr/Zarar</span>
          <span className="wallet-value" style={{color: profitColor}}>
            {wallet.daily_profit >= 0 ? '+' : ''}{wallet.daily_profit?.toFixed(2)} USDT
          </span>
          <span className="wallet-sub" style={{color: profitColor}}>
            %{wallet.daily_profit_pct?.toFixed(2)}
          </span>
        </div>

        <div className="wallet-card">
          <span className="wallet-label">Günlük Hedef</span>
          <span className="wallet-value">${wallet.daily_target?.toFixed(2)}</span>
          <span className="wallet-sub">
            {wallet.target_reached ? '✅ Hedefe Ulaşıldı!' : '🎯 Devam Ediyor'}
          </span>
        </div>

        <div className="wallet-card">
          <span className="wallet-label">Slot Durumu</span>
          <span className="wallet-value">{wallet.active_slots} / 3</span>
          <span className="wallet-sub">{wallet.available_slots} boş slot</span>
        </div>

        <div className="wallet-card">
          <span className="wallet-label">Slot Büyüklüğü</span>
          <span className="wallet-value">${wallet.slot_size?.toFixed(2)}</span>
          <span className="wallet-sub">Nakit Rezerv: ${wallet.cash_reserve?.toFixed(2)}</span>
        </div>

        <div className="wallet-card">
          <span className="wallet-label">İstatistik</span>
          <span className="wallet-value">%{wallet.win_rate}</span>
          <span className="wallet-sub">{wallet.winning_trades}K / {wallet.losing_trades}Z</span>
        </div>
      </div>

      {/* Aktif Pozisyonlar */}
      {wallet.active_positions?.length > 0 && (
        <div className="active-positions">
          <h3>📈 Aktif Pozisyonlar</h3>
          <div className="positions-grid">
            {wallet.active_positions.map((pos, index) => (
              <div key={pos.id} className="position-card">
                <div className="pos-header">
                  <span className="pos-symbol">{pos.symbol}</span>
                  <span className={`pos-type ${pos.type?.toLowerCase()}`}>
                    {pos.type} {pos.leverage}x
                  </span>
                </div>
                <div className="pos-details">
                  <div className="pos-row">
                    <span>Giriş:</span>
                    <span>${pos.entry_price?.toFixed(4)}</span>
                  </div>
                  <div className="pos-row">
                    <span>Sermaye:</span>
                    <span>${pos.capital?.toFixed(2)}</span>
                  </div>
                  <div className="pos-row">
                    <span>Kâr/Zarar:</span>
                    <span style={{color: pos.profit_loss >= 0 ? '#00ff88' : '#ff4444'}}>
                      {pos.profit_loss >= 0 ? '+' : ''}{pos.profit_loss?.toFixed(4)}
                    </span>
                  </div>
                  <div className="pos-row">
                    <span>Çıkış:</span>
                    <span>
                      {pos.stage_1 ? 'A1✅ ' : 'A1⬜ '}
                      {pos.stage_2 ? 'A2✅ ' : 'A2⬜ '}
                    </span>
                  </div>
                </div>
                <div className="pos-stage-bar">
                  <div 
                    className="stage-fill" 
                    style={{
                      width: `${(pos.stage_1 ? 33 : 0) + (pos.stage_2 ? 33 : 0)}%`
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Slot Görselleştirme */}
      <div className="slot-visual">
        <h3>🎰 Slot Durumu</h3>
        <div className="slot-bars">
          {[0, 1, 2].map(i => (
            <div 
              key={i} 
              className={`slot-bar ${i < wallet.active_slots ? 'active' : 'empty'}`}
            >
              <span>Slot {i + 1}</span>
              <span>{i < wallet.active_slots ? '🔒 Dolu' : '🟢 Boş'}</span>
            </div>
          ))}
          <div className="slot-bar cash">
            <span>Nakit</span>
            <span>💰 ${wallet.cash_reserve?.toFixed(2)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default WalletPanel