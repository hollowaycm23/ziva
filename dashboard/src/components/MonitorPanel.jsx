import { useState, useEffect, useCallback } from 'react'
import { fetchStats, fetchMetrics } from '../api'
import GaugeCard from './GaugeCard'

function ServiceItem({ name, status }) {
  const online = status === 'Online' || !status
  return (
    <div className="service-item">
      <div className="s-left">
        <span className={`s-dot ${online ? 'online' : 'offline'}`} />
        <span className="s-name">{name}</span>
      </div>
      <span className="s-ping">{status || 'Online'}</span>
    </div>
  )
}

export default function MonitorPanel() {
  const [stats, setStats] = useState({ cpu: 0, ram: 0, disk: 0, gpu: null })
  const [metrics, setMetrics] = useState(null)
  const [ts, setTs] = useState('—')

  const load = useCallback(async () => {
    try {
      const [s, m] = await Promise.all([fetchStats(), fetchMetrics()])
      setStats(s)
      if (m) setMetrics(m)
      setTs(new Date().toLocaleTimeString())
    } catch {}
  }, [])

  useEffect(() => {
    load()
    const id = setInterval(load, 5000)
    return () => clearInterval(id)
  }, [load])

  const gpuData = stats.gpu && !stats.gpu.error
    ? stats.gpu[Object.keys(stats.gpu)[0]]
    : null
  const gpuTemp = metrics?.gpu_temp ?? null
  const services = metrics?.services ?? {}

  const tempClass = gpuTemp !== null
    ? (gpuTemp > 75 ? 'bad' : gpuTemp > 60 ? 'warn' : 'good')
    : ''

  return (
    <>
      <div className="monitor-header">
        <h2>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>
          System Monitor
        </h2>
        <span className="last-update">Updated {ts}</span>
      </div>
      <div className="monitor-grid">
        <GaugeCard title="⚡ CPU" value={stats.cpu}>
          <div className="metric-row"><span className="m-label">Cores</span><span className="m-value">{navigator.hardwareConcurrency || '—'}</span></div>
        </GaugeCard>

        <GaugeCard title="🧠 RAM" value={stats.ram} color="var(--accent-amber)">
          <div className="metric-row"><span className="m-label">Load</span><span className="m-value">{stats.ram}%</span></div>
        </GaugeCard>

        <GaugeCard title="💾 DISK" value={Math.round(stats.disk)} color="#3b82f6">
          <div className="metric-row"><span className="m-label">Usage</span><span className="m-value">{Math.round(stats.disk)}%</span></div>
        </GaugeCard>

        <GaugeCard title="🎮 GPU" value={gpuData ? gpuData.gpu_util : 0} color="var(--accent-purple)">
          <div className="metric-row"><span className="m-label">Memory</span><span className="m-value">{gpuData ? `${Math.round(gpuData.mem_util)}%` : '—'}</span></div>
          <div className="metric-row"><span className="m-label">Temp</span><span className={`m-value ${tempClass}`}>{gpuTemp !== null ? `${gpuTemp}°C` : '—'}</span></div>
        </GaugeCard>

        <div className="metric-card">
          <div className="card-title">🔌 Services</div>
          {['api','ollama','qdrant','searxng','kiwix'].map(s => (
            <ServiceItem key={s} name={s} status={services[s]} />
          ))}
        </div>

        <div className="metric-card">
          <div className="card-title">📊 Processes</div>
          <ul className="proc-list">
            <li style={{ color: 'var(--text-muted)' }}>Loading...</li>
          </ul>
        </div>
      </div>
    </>
  )
}
