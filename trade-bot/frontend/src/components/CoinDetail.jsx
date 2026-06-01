import { useState, useEffect } from 'react'
import TimeframeBar from './TimeframeBar'

function CoinDetail({ symbol, onBack }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDetail()
  }, [symbol])

  const fetchDetail = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/signal/${symbol}`)
      const result = await response.json()
      setData(result)
      setLoading(false)
    } catch (error) {
      console.error('Detay hatası:', error)
      setLoading(false)
    }
  }

  if (loading) return <div className="loading">⏳ Yükleniyor...</div>
  if (!data || data.error) return <div className="loading">⚠️ Veri bulunamadı</div>

  const { layers } = data

  return (
    <div className="coin-detail">
      <button className="back-btn" onClick={onBack}>← Geri</button>
      
      <div className="detail-header">
        <h1>{symbol}</h1>
        <span className="price">${data.price?.toFixed(6)}</span>
        <span className={`signal-badge ${data.signal?.toLowerCase()}`}>
          {data.signal}
        </span>
      </div>

      <div className="score-summary">
        <div className="score-bar">
          <div 
            className="score-fill" 
            style={{width: `${(data.total_score / data.max_score) * 100}%`}}
          />
        </div>
        <span>{data.total_score} / {data.max_score} Katman Onaylı</span>
      </div>

      {data.summary && (
        <div className="summary-text">{data.summary}</div>
      )}

      <div className="timeframes">
        <h2>Zaman Dilimleri</h2>
        
        {layers?.constitution && (
          <TimeframeBar 
            name={layers.constitution.name}
            tf={layers.constitution.tf}
            passed={layers.constitution.passed}
            details={layers.constitution.details}
            extra={`Rejim: ${layers.constitution.regime}`}
          />
        )}

        {layers?.trend && (
          <TimeframeBar 
            name={layers.trend.name}
            tf={layers.trend.tf}
            passed={layers.trend.passed}
            score={layers.trend.score}
            maxScore={layers.trend.max_score}
            details={layers.trend.details}
            checks={layers.trend.checks}
          />
        )}

        {layers?.correction && (
          <TimeframeBar 
            name={layers.correction.name}
            tf={layers.correction.tf}
            passed={layers.correction.passed}
            score={layers.correction.score}
            maxScore={layers.correction.max_score}
            details={layers.correction.details}
            checks={layers.correction.checks}
          />
        )}

        {layers?.divergence && (
          <TimeframeBar 
            name={layers.divergence.name}
            tf={layers.divergence.tf}
            passed={layers.divergence.passed}
            score={layers.divergence.score}
            maxScore={layers.divergence.max_score}
            details={layers.divergence.details}
            checks={layers.divergence.checks}
          />
        )}

        {layers?.trigger && (
          <TimeframeBar 
            name={layers.trigger.name}
            tf={layers.trigger.tf}
            passed={layers.trigger.passed}
            score={layers.trigger.score}
            maxScore={layers.trigger.max_score}
            details={layers.trigger.details}
            checks={layers.trigger.checks}
          />
        )}
      </div>
    </div>
  )
}

export default CoinDetail