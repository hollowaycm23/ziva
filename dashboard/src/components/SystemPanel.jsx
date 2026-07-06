import { useState, useEffect, useCallback } from 'react'
import { fetchAgents, fetchSyncStats } from '../api'

export default function SystemPanel() {
  const [agents, setAgents] = useState(null)
  const [sync, setSync] = useState(null)

  const load = useCallback(async () => {
    const [a, s] = await Promise.all([fetchAgents(), fetchSyncStats()])
    setAgents(a)
    setSync(s)
  }, [])

  useEffect(() => { load() }, [load])

  const agentInfo = agents?.multi_agent_enabled
    ? (
      <div className="metric-card">
        <div className="card-title">🤖 Agents</div>
        <div className="info-row"><span className="i-label">Active</span><span className="i-value">{agents.active_agents || 0}</span></div>
        <div className="info-row"><span className="i-label">Max</span><span className="i-value">{agents.max_agents || '—'}</span></div>
      </div>
    )
    : (
      <div className="metric-card">
        <div className="card-title">🤖 Agents</div>
        <div className="info-row"><span className="i-label">Status</span><span className="i-value">Multi-agent inactive</span></div>
      </div>
    )

  const syncInfo = sync && (
    <div className="metric-card">
      <div className="card-title">🔄 Sync</div>
      {Object.entries(sync).map(([k, v]) => (
        <div className="info-row" key={k}>
          <span className="i-label">{k}</span>
          <span className="i-value">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
        </div>
      ))}
    </div>
  )

  return (
    <>
      <div className="system-header">
        <h2>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-purple)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3" /><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" /></svg>
          System Info
        </h2>
      </div>
      <div className="system-grid">
        <div className="metric-card">
          <div className="card-title">📦 ZIVA</div>
          <div className="info-row"><span className="i-label">Version</span><span className="i-value">2.8</span></div>
          <div className="info-row"><span className="i-label">Model</span><span className="i-value">qwen3:14b</span></div>
          <div className="info-row"><span className="i-label">Vector Dims</span><span className="i-value">1024</span></div>
        </div>
        <div className="metric-card">
          <div className="card-title">🗄️ Knowledge</div>
          <div className="info-row"><span className="i-label">Qdrant</span><span className="i-value">localhost:6333</span></div>
          <div className="info-row"><span className="i-label">Collections</span><span className="i-value">main_knowledge, staging_sync</span></div>
          <div className="info-row"><span className="i-label">Kiwix</span><span className="i-value">localhost:8081</span></div>
          <div className="info-row"><span className="i-label">SearXNG</span><span className="i-value">localhost:8080</span></div>
        </div>
        {agentInfo}
        {syncInfo}
      </div>
    </>
  )
}
