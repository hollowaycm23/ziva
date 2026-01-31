
// --- Stats Polling ---
async function updateStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        document.getElementById('cpu-bar').style.width = `${data.cpu}%`;
        document.getElementById('cpu-val').innerText = `${data.cpu}%`;

        document.getElementById('ram-bar').style.width = `${data.ram}%`;
        document.getElementById('ram-val').innerText = `${data.ram}%`;

        document.getElementById('disk-bar').style.width = `${data.disk}%`;
        document.getElementById('disk-val').innerText = `${Math.round(data.disk)}%`;
    } catch (e) {
        console.error("Stats poll error", e);
    }
}

async function updateMemory() {
    try {
        const response = await fetch('/api/memory');
        const data = await response.json();
        const list = document.getElementById('memory-list');
        list.innerHTML = "";

        data.items.forEach(item => {
            const li = document.createElement('li');
            li.innerHTML = `<span style="color:var(--accent)">[${Math.round(item.score * 100)}%]</span> ${item.text.substring(0, 40)}...`;
            list.appendChild(li);
        });
    } catch (e) {
        // silent fail
    }
}

setInterval(updateStats, 2000);
updateMemory(); // Initial load

// --- Chat Logic ---
const chatHistory = document.getElementById('chat-history');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

function appendMessage(role, content, meta = null) {
    const div = document.createElement('div');
    div.className = `message ${role}`;

    // Markdown parse if Assistant (using marked.js)
    if (role === 'assistant' && window.marked) {
        div.innerHTML = marked.parse(content);
    } else {
        div.innerText = content;
    }

    if (meta) {
        const metaSpan = document.createElement('span');
        metaSpan.className = 'meta-info';
        metaSpan.innerText = `[${meta.model} | ${meta.task}] used ${meta.ctx} memories`;
        div.appendChild(metaSpan);
    }

    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    appendMessage('user', text);
    userInput.value = '';

    // Add loading placeholder
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant loading';
    loadingDiv.innerText = 'Thinking...';
    chatHistory.appendChild(loadingDiv);

    try {
        const payload = {
            message: text,
            compact: true
            // images: [] // Future: Add image support
        };

        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        chatHistory.removeChild(loadingDiv);

        if (data.error) {
            appendMessage('assistant', `⚠️ Error: ${data.error}`);
        } else {
            const meta = {
                model: data.model_used,
                task: data.task_type,
                ctx: data.context_used || 0
            };
            appendMessage('assistant', data.response, meta);
        }

    } catch (e) {
        chatHistory.removeChild(loadingDiv);
        appendMessage('assistant', `❌ Connection Error: ${e}`);
    }
}

sendBtn.addEventListener('click', sendMessage);

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
