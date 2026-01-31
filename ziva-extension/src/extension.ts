import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
	console.log('Ziva Extension is now active!');

	const provider = new ZivaChatViewProvider(context.extensionUri);

	context.subscriptions.push(
		vscode.window.registerWebviewViewProvider(ZivaChatViewProvider.viewType, provider)
	);

	context.subscriptions.push(
		vscode.commands.registerCommand('ziva-extension.openChat', () => {
			vscode.commands.executeCommand('ziva-chat-view.focus');
		})
	);

	context.subscriptions.push(
		vscode.commands.registerCommand('ziva-extension.openDashboard', () => {
			const panel = vscode.window.createWebviewPanel(
				'zivaDashboard',
				'Ziva: System Monitor',
				vscode.ViewColumn.One,
				{}
			);
			panel.webview.html = getDashboardHtml();
		})
	);

	context.subscriptions.push(
		vscode.commands.registerCommand('ziva-extension.askZiva', () => {
			const editor = vscode.window.activeTextEditor;
			if (!editor) {
				return;
			}
			const selection = editor.selection;
			const text = editor.document.getText(selection);

			if (text) {
				provider.postMessageToWebview({ type: 'addMessage', value: `Analisar código selecionado:\n\n${text}` });
			} else {
				provider.postMessageToWebview({ type: 'addMessage', value: `Analisar arquivo: ${editor.document.fileName}` });
			}
			vscode.commands.executeCommand('ziva-chat-view.focus');
		})
	);
}

class ZivaChatViewProvider implements vscode.WebviewViewProvider {
	public static readonly viewType = 'ziva-chat-view';
	private _view?: vscode.WebviewView;

	constructor(private readonly _extensionUri: vscode.Uri) { }

	public resolveWebviewView(
		webviewView: vscode.WebviewView,
		context: vscode.WebviewViewResolveContext,
		_token: vscode.CancellationToken,
	) {
		this._view = webviewView;

		webviewView.webview.options = {
			enableScripts: true,
			localResourceRoots: [this._extensionUri]
		};

		webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

		webviewView.webview.onDidReceiveMessage(data => {
			switch (data.type) {
				case 'sendMessage':
					{
						vscode.window.showInformationMessage(`Ziva recebeu: ${data.value}`);
						break;
					}
			}
		});
	}

	public postMessageToWebview(message: any) {
		if (this._view) {
			this._view.webview.postMessage(message);
		}
	}

	private _getHtmlForWebview(webview: vscode.Webview) {
		return `<!DOCTYPE html>
			<html lang="en">
			<head>
				<meta charset="UTF-8">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<title>Ziva Chat</title>
				<style>
					body { font-family: sans-serif; padding: 10px; color: var(--vscode-foreground); background: var(--vscode-sideBar-background); }
					.chat-container { display: flex; flex-direction: column; height: 95vh; }
					#messages { flex: 1; overflow-y: auto; margin-bottom: 10px; padding-right: 5px; }
					.input-area { display: flex; gap: 5px; padding-top: 10px; border-top: 1px solid var(--vscode-divider); }
					input { flex: 1; background: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); padding: 8px; border-radius: 4px; }
					button { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; padding: 8px 12px; cursor: pointer; border-radius: 4px; font-weight: bold; }
					button:hover { background: var(--vscode-button-hoverBackground); }
					.message { margin-bottom: 12px; padding: 8px 12px; border-radius: 6px; line-height: 1.4; font-size: 13px; max-width: 90%; }
					.user { background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); align-self: flex-end; margin-left: auto; border-bottom-right-radius: 2px; }
					.ziva { background: var(--vscode-editor-background); border: 1px solid var(--vscode-widget-border); align-self: flex-start; border-bottom-left-radius: 2px; }
					.system { font-size: 11px; opacity: 0.6; text-align: center; margin: 10px 0; }
					::-webkit-scrollbar { width: 6px; }
					::-webkit-scrollbar-thumb { background: var(--vscode-scrollbarSlider-background); border-radius: 3px; }
				</style>
			</head>
			<body>
				<div class="chat-container">
					<div id="messages">
						<div class="message ziva">Ziva: Olá! Sou sua assistente local. Como posso ajudar com seu código agora?</div>
					</div>
					<div class="input-area">
						<input type="text" id="chatInput" placeholder="Pergunte à Ziva..." />
						<button id="sendBtn">Enviar</button>
					</div>
				</div>
				<script>
					const vscode = acquireVsCodeApi();
					const input = document.getElementById('chatInput');
					const btn = document.getElementById('sendBtn');
					const messages = document.getElementById('messages');
					let sessionId = null;

					function appendMessage(sender, text) {
						const msgDiv = document.createElement('div');
						msgDiv.className = 'message ' + sender;
						// Handle simple markdown-ish line breaks
						msgDiv.innerHTML = '<b>' + (sender === 'user' ? 'Você: ' : 'Ziva: ') + '</b><br>' + text.replace(/\\n/g, '<br>');
						messages.appendChild(msgDiv);
						messages.scrollTop = messages.scrollHeight;
					}

					async function sendMessage(text) {
						try {
							const response = await fetch('http://localhost:8000/chat', {
								method: 'POST',
								headers: { 'Content-Type': 'application/json' },
								body: JSON.stringify({ message: text, session_id: sessionId, compact: true })
							});
							const data = await response.json();
							sessionId = data.session_id;
							appendMessage('ziva', data.response);
						} catch (err) {
							appendMessage('ziva', 'Erro ao conectar à Ziva API. Verifique se o servidor está rodando na porta 8000.');
						}
					}

					btn.addEventListener('click', () => {
						const value = input.value;
						if (value) {
							appendMessage('user', value);
							sendMessage(value);
							input.value = '';
						}
					});

					input.addEventListener('keypress', (e) => {
						if (e.key === 'Enter') btn.click();
					});

					window.addEventListener('message', event => {
						const message = event.data;
						switch (message.type) {
							case 'addMessage':
								appendMessage('user', message.value);
								sendMessage(message.value);
								break;
						}
					});
				</script>
			</body>
			</html>`;
	}
}

function getDashboardHtml() {
	return `<!DOCTYPE html>
		<html lang="en">
		<head>
			<meta charset="UTF-8">
			<title>Ziva Dashboard</title>
			<style>
				body { background: #0f172a; color: #f8fafc; font-family: 'Inter', system-ui, sans-serif; padding: 20px; }
				.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
				.card { background: #1e293b; padding: 15px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
				h2 { color: #38bdf8; font-size: 14px; margin-top: 0; text-transform: uppercase; letter-spacing: 0.1em; }
				.value { font-size: 24px; font-weight: bold; margin: 10px 0; }
				.bar-bg { background: #334155; height: 8px; border-radius: 4px; overflow: hidden; }
				.bar-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
				.cpu-fill { background: linear-gradient(90deg, #0ea5e9, #38bdf8); }
				.ram-fill { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
				.gpu-fill { background: linear-gradient(90deg, #10b981, #34d399); }
				.status-online { color: #10b981; font-size: 12px; font-weight: bold; }
				.status-offline { color: #f43f5e; font-size: 12px; font-weight: bold; }
			</style>
		</head>
		<body>
			<h1 style="font-size: 20px; color: #38bdf8; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
				<svg width="24" height="24" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="45" stroke="#38bdf8" stroke-width="5" fill="none"/><path d="M30 50 L50 30 L70 50 L50 70 Z" fill="#38bdf8"/></svg>
				Ziva Intelligence System Monitor
			</h1>
			
			<div class="grid">
				<div class="card">
					<h2>CPU Usage</h2>
					<div class="value" id="cpuVal">0%</div>
					<div class="bar-bg"><div id="cpuBar" class="bar-fill cpu-fill" style="width: 0%"></div></div>
				</div>
				<div class="card">
					<h2>RAM Usage</h2>
					<div class="value" id="ramVal">0%</div>
					<div class="bar-bg"><div id="ramBar" class="bar-fill ram-fill" style="width: 0%"></div></div>
				</div>
				<div class="card">
					<h2>GPU Load</h2>
					<div class="value" id="gpuVal">N/A</div>
					<div class="bar-bg"><div id="gpuBar" class="bar-fill gpu-fill" style="width: 0%"></div></div>
				</div>
				<div class="card">
					<h2>GPU Temp</h2>
					<div class="value" id="tempVal">N/A</div>
					<div id="tempStatus" style="font-size: 12px; margin-top: 5px;"></div>
				</div>
			</div>

			<div class="card" style="margin-top: 20px;">
				<h2>Service Status</h2>
				<div id="serviceStatus" class="status-online">● Ziva Core API: Synchronizing...</div>
			</div>

			<script>
				async function updateMetrics() {
					try {
						const response = await fetch('http://localhost:8000/metrics');
						const data = await response.json();
						
						document.getElementById('cpuVal').innerText = data.cpu.toFixed(1) + '%';
						document.getElementById('cpuBar').style.width = data.cpu + '%';
						
						document.getElementById('ramVal').innerText = data.ram.toFixed(1) + '%';
						document.getElementById('ramBar').style.width = data.ram + '%';
						
						if (data.gpu !== null) {
							document.getElementById('gpuVal').innerText = data.gpu.toFixed(1) + '%';
							document.getElementById('gpuBar').style.width = data.gpu + '%';
							document.getElementById('tempVal').innerText = data.gpu_temp + '°C';
							
							const tempStatus = document.getElementById('tempStatus');
							if (data.gpu_temp < 70) tempStatus.innerHTML = '<span style="color: #10b981;">Optimal</span>';
							else if (data.gpu_temp < 80) tempStatus.innerHTML = '<span style="color: #f59e0b;">Warm</span>';
							else tempStatus.innerHTML = '<span style="color: #f43f5e;">Critical</span>';
						}
						
						document.getElementById('serviceStatus').className = 'status-online';
						document.getElementById('serviceStatus').innerText = '● Ziva Core API: Online (Port 8000)';
					} catch (err) {
						document.getElementById('serviceStatus').className = 'status-offline';
						document.getElementById('serviceStatus').innerText = '● Ziva Core API: Offline (Reconnecting...)';
					}
				}

				setInterval(updateMetrics, 2000);
				updateMetrics();
			</script>
		</body>
		</html>`;
}

export function deactivate() { }
