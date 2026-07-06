import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import MonitorPanel from './components/MonitorPanel'
import SystemPanel from './components/SystemPanel'

export default function App() {
  const [tab, setTab] = useState('chat')

  return (
    <div className="app">
      <Sidebar activeTab={tab} onTabChange={setTab} />
      <main className="content">
        <div className={`tab-panel${tab === 'chat' ? ' active' : ''}`} id="panel-chat">
          <ChatPanel />
        </div>
        <div className={`tab-panel${tab === 'monitor' ? ' active' : ''}`} id="panel-monitor">
          <MonitorPanel />
        </div>
        <div className={`tab-panel${tab === 'system' ? ' active' : ''}`} id="panel-system">
          <SystemPanel />
        </div>
      </main>
    </div>
  )
}
