# Setup — Ziva AI Agent

## Pré-requisitos

- **Hardware**: NVIDIA GPU com ≥8GB VRAM (testado em RTX 4070 12GB)
- **SO**: Windows 11 (testado) ou Linux
- **Docker Desktop**: Para containers de infraestrutura
- **Python**: 3.10+
- **Ollama**: Instalado nativamente (não em Docker)

## 1. Infraestrutura (Docker)

```bash
# Qdrant (vector store)
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant

# SearXNG (web search)
docker run -d --name searxng -p 8080:8080 searxng/searxng

# Kiwix (offline knowledge)
docker run -d --name kiwix -p 8081:8081 kiwix/kiwix-serve

# Browserless (web scraping)
docker run -d --name browserless -p 3000:3000 browserless/chrome
```

## 2. Ollama (Bare-metal)

```bash
# Instalar modelos
ollama pull qwen2.5:7b
ollama pull qwen3:14b
ollama pull nomic-embed-text

# Verificar
ollama list
```

## 3. Python Environment

```bash
# Criar virtualenv
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux

# Instalar dependências
pip install -r requirements.txt
```

## 4. Configuração

### .env
```env
# Ollama
OLLAMA_HOST=http://localhost:11434

# Qdrant
QDRANT_URL=http://localhost:6333

# Ziva
ZIVA_LOG_LEVEL=INFO
ZIVA_API_KEY=your-key-here
```

### ziva.yaml
```yaml
models:
  providers:
    ollama:
      base_url: http://localhost:11434/v1
      api_key: ollama
  aliases:
    agent.primary_model: ollama/qwen3:14b
    agent.coder_model: ollama/qwen3:14b
    agent.embedding_model: ollama/nomic-embed-text
```

## 5. Executar

```bash
# Iniciar servidor
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000

# Ou usando script de startup
python scripts/start_ziva.py
```

## 6. Verificar

```bash
# Health check
curl http://localhost:8000/health

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá!", "session_id": "test"}'

# Métricas
curl http://localhost:8000/metrics
```

## 7. Testes

```bash
# Todos os testes
python -m unittest discover tests -v

# Testes específicos
python -m unittest tests.test_dynamic_tools
python -m unittest tests.test_governance
python -m unittest tests.test_integration_graph
```
