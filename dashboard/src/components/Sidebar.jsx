import { useStats } from '../hooks/useStats'
import { useMemory } from '../hooks/useMemory'

const VITAL_ICONS = { cpu: '⚡', ram: '🧠', disk: '💾', gpu: '🎮' }
const FILL_COLORS = { cpu: 'cyan', ram: 'amber', disk: 'blue', gpu: 'purple' }

function VitalItem({ name, value, sub }) {
  const fillClass = FILL_COLORS[name]
  return (
    <div className="vital-item">
      <div className={`vital-icon ${name}`}>{VITAL_ICONS[name]}</div>
      <div className="vital-info">
        <div className="label">{name.toUpperCase()}</div>
        <div className="vital-track">
          <div className={`fill ${fillClass}`} style={{ width: `${Math.min(value, 100)}%` }} />
        </div>
        {sub && <div className="gpu-sub"><span className="sub-item">MEM <span>{sub}</span></span></div>}
      </div>
      <span className="vital-value">{Math.round(value)}%</span>
    </div>
  )
}

function MemoryItem({ item }) {
  return (
    <li>
      <span className="mem-score">{Math.round(item.score * 100)}%</span>
      {item.text.substring(0, 34)}{item.text.length > 34 ? '…' : ''}
    </li>
  )
}

export default function Sidebar({ activeTab, onTabChange }) {
  const stats = useStats()
  const memory = useMemory()

  const gpuData = stats.gpu && !stats.gpu.error
    ? stats.gpu[Object.keys(stats.gpu)[0]]
    : null

  const tabs = [
    { id: 'chat', label: 'Chat' },
    { id: 'monitor', label: 'Monitor' },
    { id: 'system', label: 'System' },
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo-icon">Z</div>
        <span className="logo-text">ZIVA</span>
        <div className="status-badge">
          <span className="dot" />
          ON
        </div>
      </div>

      <nav className="sidebar-tabs">
        {tabs.map(t => (
          <button
            key={t.id}
            className={`stab-btn${activeTab === t.id ? ' active' : ''}`}
            data-tab={t.id}
            onClick={() => onTabChange(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-section">
        <h3>Vitals</h3>
        <VitalItem name="cpu" value={stats.cpu} />
        <VitalItem name="ram" value={stats.ram} />
        <VitalItem name="disk" value={Math.round(stats.disk)} />
        <VitalItem
          name="gpu"
          value={gpuData ? gpuData.gpu_util : 0}
          sub={gpuData ? `${Math.round(gpuData.mem_util)}%` : '0%'}
        />
      </div>

      <div className="sidebar-section">
        <h3>Context</h3>
        <ul id="memory-list">
          {memory.length === 0 ? (
            <li style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Waiting...</li>
          ) : (
            memory.map((item, i) => <MemoryItem key={item.id || i} item={item} />)
          )}
        </ul>
      </div>
    </aside>
  )
}
