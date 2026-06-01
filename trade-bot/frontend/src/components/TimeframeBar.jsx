function TimeframeBar({ name, tf, passed, score, maxScore, details, checks, extra }) {
  return (
    <div className={`tf-bar ${passed ? 'passed' : 'failed'}`}>
      <div className="tf-header">
        <span className="tf-badge">{tf}</span>
        <span className="tf-name">{name}</span>
        <span className="tf-status">{passed ? '✅' : '❌'}</span>
        {score !== undefined && (
          <span className="tf-score">{score}/{maxScore}</span>
        )}
      </div>
      
      <div className="tf-details">{details}</div>
      
      {extra && <div className="tf-extra">{extra}</div>}
      
      {checks && (
        <div className="tf-checks">
          {Object.entries(checks).map(([key, check]) => (
            <div key={key} className={`check-item ${check.passed ? 'pass' : 'fail'}`}>
              <span className="check-icon">{check.passed ? '✓' : '✗'}</span>
              <span className="check-value">{check.value}</span>
              <span className="check-detail">{check.detail}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default TimeframeBar