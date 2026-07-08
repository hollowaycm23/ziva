# API — Ziva AI Agent

## Endpoints

### POST /chat
Chat interativo com sessão.

```json
// Request
{
  "message": "Qual a capital da França?",
  "session_id": "sessao-123"
}

// Response
{
  "response": "A capital da França é Paris.",
  "session_id": "sessao-123",
  "request_id": "req_123456789"
}
```

### POST /v1/chat/completions
API compatível com OpenAI.

```json
// Request
{
  "model": "ziva",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "session_id": "sessao-123",
  "stream": false
}

// Response
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1712345678,
  "model": "ziva",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    }
  }]
}
```

### GET /health
Status do servidor e serviços.

```json
{
  "status": "healthy",
  "services": {
    "qdrant": {"status": "healthy"},
    "ollama": {"status": "healthy", "models": ["qwen3:14b", "nomic-embed-text"]},
    "searxng": {"status": "healthy"},
    "kiwix": {"status": "unavailable"}
  }
}
```

### GET /metrics
Métricas de performance e VRAM.

```json
{
  "cpu_per_core": [12.5, 8.3, 15.1, ...],
  "ram_used_gb": 14.2,
  "ram_total_gb": 32.0,
  "gpu_mem_used_gb": 8.5,
  "gpu_mem_total_gb": 12.0,
  "vram_pct": 70.8,
  "vram_threshold_warning": false,
  "node_metrics": {
    "input_node": {"count": 156, "avg": 0.002, "last": 0.001},
    "analyze_node": {"count": 145, "avg": 1.234, "last": 1.102},
    "respond_node": {"count": 142, "avg": 0.876, "last": 0.654}
  }
}
```

### POST /memory/search
Busca na memória vetorial.

```json
// Request
{
  "query": "Python functions",
  "limit": 5
}

// Response
{
  "results": [
    {"text": "def add(a, b): return a + b", "score": 0.95, "metadata": {"source": "code"}}
  ]
}
```

### POST /tools (dynamic tools)
Lista ferramentas dinâmicas criadas pelo usuário.

```json
// Response
{
  "tools": [
    {"name": "converter_temperatura", "version": 1, "description": "Converte temperaturas",
     "usage_count": 5, "success_rate": 1.0}
  ]
}
```

## Ferramentas Ziva (LLM-callable)

| Ferramenta | Descrição |
|---|---|
| `web_search(query)` | Busca na web via SearXNG |
| `create_tool(name, code, desc)` | Cria ferramenta Python dinâmica |
| `list_dynamic_tools()` | Lista ferramentas criadas |
| `delete_tool(name)` | Remove ferramenta |
| `get_current_datetime()` | Data/hora atual |
| `search_knowledge_base(query)` | Busca na base RAG |
| `get_weather(city)` | Clima para uma cidade |

## Códigos de Erro

| Status | Significado |
|---|---|
| 200 | Sucesso |
| 400 | Requisição inválida |
| 404 | Recurso não encontrado |
| 429 | Rate limit |
| 500 | Erro interno |

## Headers

| Header | Descrição |
|---|---|
| `X-Request-ID` | ID único da requisição (tracing) |
| `X-Session-ID` | ID da sessão do usuário |
| `Authorization` | Bearer token (se configurado) |
