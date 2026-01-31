"""
title: Ziva Dashboard
author: Antigravity
author_url: https://github.com/holloway/ziva
version: 1.0
"""

from pydantic import BaseModel, Field
import requests
import time

class Action:
    def __init__(self):
        self.api_url = "http://ziva-core:8000/v1/health"

    async def action(self, body: dict, __user__: dict = None, __event_emitter__=None):
        await __event_emitter__(
            {
                "type": "status",
                "data": {"description": "Consultando Status dos Sistemas Ziva...", "done": False},
            }
        )
        
        try:
            response = requests.get(self.api_url, timeout=5)
            data = response.json()
            
            status_emoji = "✅" if data["status"] == "healthy" else "⚠️"
            
            output = f"## {status_emoji} Ziva System Dashboard\n\n"
            output += "| Serviço | Status | Host:Port | Saúde |\n"
            output += "| :--- | :--- | :--- | :--- |\n"
            
            for name, info in data["services"].items():
                health_icon = "🟢" if info.get("healthy") else "🔴"
                if info.get("status") == "external":
                    health_icon = "🔵 (Ext)" if info.get("healthy") else "🔴"
                
                # Formatar detalhes extras se houver (ex: inbox/outbox)
                extra = ""
                if name == "message_daemon":
                    extra = f" (📥{info.get('inbox')} 📤{info.get('outbox')})"
                
                output += f"| **{name.replace('_', ' ').title()}**{extra} | {info.get('status').title()} | `{info.get('host')}:{info.get('port', '-')}` | {health_icon} |\n"
            
            output += f"\n---\n*Atualizado em: {time.strftime('%H:%M:%S', time.localtime(data['timestamp']))}*"

            await __event_emitter__(
                {
                    "type": "message",
                    "data": {"content": output},
                }
            )

            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Dashboard Ziva Atualizado", "done": True},
                }
            )
            
            return output

        except Exception as e:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": f"Erro ao consultar API: {str(e)}", "done": True},
                }
            )
            return f"❌ Erro ao conectar na API Ziva: {str(e)}"
