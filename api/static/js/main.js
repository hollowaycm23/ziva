const AUTH_HEADER = 'Basic ' + btoa('admin:ziva_admin_password');

// ===== TAB SYSTEM =====
document.querySelectorAll('.stab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.stab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const tab = btn.dataset.tab;
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        document.getElementById(`panel-${tab}`).classList.add('active');
        if (tab === 'monitor') updateMonitor();
        if (tab === 'system') updateSystemPanel();
    });
});

// ===== SIDEBAR STATS =====
async function updateStats() {
    try {
        const r = await fetch('/api/stats', { headers: { Authorization: AUTH_HEADER } });
        const d = await r.json();
        document.getElementById('cpu-bar').style.width = `${d.cpu}%`;
        document.getElementById('cpu-val').innerText = `${d.cpu}%`;
        document.getElementById('ram-bar').style.width = `${d.ram}%`;
        document.getElementById('ram-val').innerText = `${d.ram}%`;
        document.getElementById('disk-bar').style.width = `${d.disk}%`;
        document.getElementById('disk-val').innerText = `${Math.round(d.disk)}%`;
        const g = d.gpu;
        if (g && !g.error) {
            const n = Object.keys(g);
            if (n.length > 0) {
                const gpu = g[n[0]];
                document.getElementById('gpu-bar').style.width = `${gpu.gpu_util}%`;
                document.getElementById('gpu-val').innerText = `${gpu.gpu_util}%`;
                document.getElementById('gpu-mem-val').innerText = `${Math.round(gpu.mem_util)}%`;
            }
        }
    } catch (_) {}
}

async function updateMemory() {
    try {
        const r = await fetch('/api/memory', { headers: { Authorization: AUTH_HEADER } });
        const d = await r.json();
        const list = document.getElementById('memory-list');
        list.innerHTML = '';
        if (!d.items || d.items.length === 0) {
            list.innerHTML = '<li style="color:var(--text-muted);font-style:italic;">No context loaded</li>';
        } else {
            d.items.forEach(item => {
                const li = document.createElement('li');
                li.innerHTML = `<span class="mem-score">${Math.round(item.score * 100)}%</span> ${item.text.substring(0, 34)}${item.text.length > 34 ? '…' : ''}`;
                list.appendChild(li);
            });
        }
    } catch (_) {}
}

setInterval(updateStats, 2000);
updateMemory();

// ===== MONITOR PANEL =====
async function updateMonitor() {
    const CIRCUMFERENCE = 2 * Math.PI * 42;
    let stats, metrics;
    try {
        [stats, metrics] = await Promise.all([
            fetch('/api/stats', { headers: { Authorization: AUTH_HEADER } }).then(r => r.json()),
            fetch('/metrics', { headers: { Authorization: AUTH_HEADER } }).catch(() => null)
        ]);
    } catch (_) { return; }

    const ts = new Date().toLocaleTimeString();
    document.getElementById('monitor-ts').innerText = `Updated ${ts}`;

    const gpuData = stats.gpu && !stats.gpu.error ? stats.gpu[Object.keys(stats.gpu)[0]] : null;
    const gpuTemp = metrics && metrics.gpu_temp != null ? metrics.gpu_temp : null;
    const services = metrics && metrics.services ? metrics.services : {};

    const grid = document.getElementById('monitor-grid');
    grid.innerHTML = `
        <div class="metric-card">
            <div class="card-title">⚡ CPU</div>
            <div class="gauge-wrap">
                <div class="gauge">
                    <svg width="100" height="100" viewBox="0 0 100 100">
                        <circle class="bg" cx="50" cy="50" r="42"/>
                        <circle class="progress" id="cpu-gauge" cx="50" cy="50" r="42"
                            stroke-dasharray="${CIRCUMFERENCE}"
                            stroke-dashoffset="${CIRCUMFERENCE * (1 - stats.cpu / 100)}"/>
                    </svg>
                    <div class="center-text" id="cpu-gauge-val">${stats.cpu}%</div>
                    <div class="center-label">Used</div>
                </div>
            </div>
            <div class="metric-row"><span class="m-label">Cores</span><span class="m-value">${navigator.hardwareConcurrency || '—'}</span></div>
        </div>
        <div class="metric-card">
            <div class="card-title">🧠 RAM</div>
            <div class="gauge-wrap">
                <div class="gauge">
                    <svg width="100" height="100" viewBox="0 0 100 100">
                        <circle class="bg" cx="50" cy="50" r="42"/>
                        <circle class="progress" id="ram-gauge" cx="50" cy="50" r="42"
                            stroke-dasharray="${CIRCUMFERENCE}"
                            stroke-dashoffset="${CIRCUMFERENCE * (1 - stats.ram / 100)}"/>
                    </svg>
                    <div class="center-text" id="ram-gauge-val">${stats.ram}%</div>
                    <div class="center-label">Used</div>
                </div>
            </div>
            <div class="metric-row"><span class="m-label">Load</span><span class="m-value">${stats.ram}%</span></div>
        </div>
        <div class="metric-card">
            <div class="card-title">💾 DISK</div>
            <div class="gauge-wrap">
                <div class="gauge">
                    <svg width="100" height="100" viewBox="0 0 100 100">
                        <circle class="bg" cx="50" cy="50" r="42"/>
                        <circle class="progress" id="disk-gauge" cx="50" cy="50" r="42"
                            stroke-dasharray="${CIRCUMFERENCE}"
                            stroke-dashoffset="${CIRCUMFERENCE * (1 - stats.disk / 100)}"/>
                    </svg>
                    <div class="center-text" id="disk-gauge-val">${Math.round(stats.disk)}%</div>
                    <div class="center-label">Used</div>
                </div>
            </div>
            <div class="metric-row"><span class="m-label">Usage</span><span class="m-value">${Math.round(stats.disk)}%</span></div>
        </div>
        <div class="metric-card">
            <div class="card-title">🎮 GPU</div>
            <div class="gauge-wrap">
                <div class="gauge">
                    <svg width="100" height="100" viewBox="0 0 100 100">
                        <circle class="bg" cx="50" cy="50" r="42"/>
                        <circle class="progress" id="gpu-gauge" cx="50" cy="50" r="42"
                            stroke="#a855f7"
                            stroke-dasharray="${CIRCUMFERENCE}"
                            stroke-dashoffset="${CIRCUMFERENCE * (1 - (gpuData ? gpuData.gpu_util / 100 : 0))}"/>
                    </svg>
                    <div class="center-text" id="gpu-gauge-val">${gpuData ? gpuData.gpu_util : '—'}</div>
                    <div class="center-label">Util</div>
                </div>
            </div>
            <div class="metric-row"><span class="m-label">Memory</span><span class="m-value">${gpuData ? Math.round(gpuData.mem_util) + '%' : '—'}</span></div>
            <div class="metric-row"><span class="m-label">Temp</span><span class="m-value ${gpuTemp !== null ? (gpuTemp > 75 ? 'bad' : gpuTemp > 60 ? 'warn' : 'good') : ''}">${gpuTemp !== null ? gpuTemp + '°C' : '—'}</span></div>
        </div>
        <div class="metric-card">
            <div class="card-title">🔌 Services</div>
            ${['api','ollama','qdrant','searxng','kiwix'].map(s => `
                <div class="service-item">
                    <div class="s-left">
                        <span class="s-dot ${services[s] === 'Online' || !services[s] ? 'online' : 'offline'}"></span>
                        <span class="s-name">${s}</span>
                    </div>
                    <span class="s-ping">${services[s] || 'Online'}</span>
                </div>
            `).join('')}
        </div>
        <div class="metric-card">
            <div class="card-title">📊 Processes</div>
            <ul class="proc-list" id="proc-list">
                <li style="color:var(--text-muted);">Loading...</li>
            </ul>
        </div>
    `;
}

// ===== SYSTEM PANEL =====
async function updateSystemPanel() {
    const grid = document.getElementById('system-grid');
    const [agentsRes, syncRes] = await Promise.all([
        fetch('/api/v1/agents/status', { headers: { Authorization: AUTH_HEADER } }).catch(() => null),
        fetch('/sync/stats', { headers: { Authorization: AUTH_HEADER } }).catch(() => null)
    ]);
    const agents = agentsRes && agentsRes.ok ? await agentsRes.json().catch(() => null) : null;
    const sync = syncRes && syncRes.ok ? await syncRes.json().catch(() => null) : null;

    const agentInfo = agents && agents.multi_agent_enabled
        ? `<div class="metric-card">
            <div class="card-title">🤖 Agents</div>
            <div class="info-row"><span class="i-label">Active</span><span class="i-value">${agents.active_agents || 0}</span></div>
            <div class="info-row"><span class="i-label">Max</span><span class="i-value">${agents.max_agents || '—'}</span></div>
           </div>`
        : `<div class="metric-card">
            <div class="card-title">🤖 Agents</div>
            <div class="info-row"><span class="i-label">Status</span><span class="i-value">Multi-agent inactive</span></div>
           </div>`;

    const syncInfo = sync
        ? `<div class="metric-card">
            <div class="card-title">🔄 Sync</div>
            ${Object.entries(sync).map(([k, v]) =>
                `<div class="info-row"><span class="i-label">${k}</span><span class="i-value">${typeof v === 'object' ? JSON.stringify(v) : v}</span></div>`
            ).join('')}
           </div>`
        : '';

    grid.innerHTML = `
        <div class="metric-card">
            <div class="card-title">📦 ZIVA</div>
            <div class="info-row"><span class="i-label">Version</span><span class="i-value">2.8</span></div>
            <div class="info-row"><span class="i-label">Model</span><span class="i-value">qwen3:14b</span></div>
            <div class="info-row"><span class="i-label">Vector Dims</span><span class="i-value">1024</span></div>
        </div>
        <div class="metric-card">
            <div class="card-title">🗄️ Knowledge</div>
            <div class="info-row"><span class="i-label">Qdrant</span><span class="i-value">localhost:6333</span></div>
            <div class="info-row"><span class="i-label">Collections</span><span class="i-value">main_knowledge, staging_sync</span></div>
            <div class="info-row"><span class="i-label">Kiwix</span><span class="i-value">localhost:8081</span></div>
            <div class="info-row"><span class="i-label">SearXNG</span><span class="i-value">localhost:8080</span></div>
        </div>
        ${agentInfo}
        ${syncInfo}
    `;
}

// ===== CHAT =====
const chatHistory = document.getElementById('chat-history');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const stopBtn = document.getElementById('stop-btn');
let currentAbortController = null;

function appendMessage(role, content, meta = null) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    if (role === 'assistant' && window.marked) {
        div.innerHTML = marked.parse(content);
    } else {
        div.innerText = content;
    }
    if (meta) {
        const s = document.createElement('span');
        s.className = 'meta-info';
        s.innerText = `[${meta.model} | ${meta.task}] used ${meta.ctx} memories`;
        div.appendChild(s);
    }
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function createLoadingDots() {
    const div = document.createElement('div');
    div.className = 'message loading';
    div.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
    return div;
}

function autoResize(textarea) {
    textarea.style.height = '44px';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;
    appendMessage('user', text);
    userInput.value = '';
    autoResize(userInput);

    const loadingDiv = createLoadingDots();
    chatHistory.appendChild(loadingDiv);

    sendBtn.style.display = 'none';
    stopBtn.style.display = 'flex';

    const controller = new AbortController();
    currentAbortController = controller;
    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': AUTH_HEADER },
            body: JSON.stringify({ message: text, compact: true }),
            signal: controller.signal
        });
        const data = await res.json();
        if (loadingDiv.parentNode) chatHistory.removeChild(loadingDiv);
        if (data.error) {
            appendMessage('assistant', `⚠️ Error: ${data.error}`);
        } else {
            appendMessage('assistant', data.response, {
                model: data.model_used,
                task: data.task_type,
                ctx: data.context_used || 0
            });
        }
    } catch (e) {
        if (loadingDiv.parentNode) chatHistory.removeChild(loadingDiv);
        appendMessage('assistant', e.name === 'AbortError'
            ? '🛑 Raciocínio interrompido.'
            : `❌ Connection Error: ${e}`);
    } finally {
        sendBtn.style.display = 'flex';
        stopBtn.style.display = 'none';
        currentAbortController = null;
    }
}

function stopMessage() {
    if (currentAbortController) currentAbortController.abort();
}

sendBtn.addEventListener('click', sendMessage);
stopBtn.addEventListener('click', stopMessage);
userInput.addEventListener('input', () => autoResize(userInput));
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

// ===== INIT =====
updateMonitor();
setInterval(updateMonitor, 5000);
updateSystemPanel();
