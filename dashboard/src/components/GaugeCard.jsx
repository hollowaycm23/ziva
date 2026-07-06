const CIRCUMFERENCE = 2 * Math.PI * 42

export default function GaugeCard({ title, value, color = 'var(--accent)', children }) {
  const offset = CIRCUMFERENCE * (1 - Math.min(value, 100) / 100)
  return (
    <div className="metric-card">
      <div className="card-title">{title}</div>
      <div className="gauge-wrap">
        <div className="gauge">
          <svg width="100" height="100" viewBox="0 0 100 100">
            <circle className="bg" cx="50" cy="50" r="42" />
            <circle
              className="progress"
              cx="50" cy="50" r="42"
              stroke={color}
              strokeDasharray={CIRCUMFERENCE}
              strokeDashoffset={offset}
            />
          </svg>
          <div className="center-text">{Math.round(value)}%</div>
          <div className="center-label">Used</div>
        </div>
      </div>
      {children}
    </div>
  )
}
