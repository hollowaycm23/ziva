# 🔍 RELATÓRIO: Conflitos e Má Configurações Docker - Ziva

**Data**: 2025-01-14  
**Status**: ⚠️ CRÍTICO - 12 problemas identificados

---

## 1. ❌ CONFLITO CRÍTICO: Ollama vs LM Studio

**Arquivo**: `docker-compose.yml` + `.env.example` + `ziva.yaml`

### Problema:
- `docker-compose.yml` define `ZIVA_LLM_BASE_URL=http://localhost:11434/v1` (Ollama)
- `.env.example` define `ZIVA_LLM_BASE_URL=http://host.docker.internal:1234/v1` (LM Studio)
- `ziva.yaml` tenta configurar ambos: `ollama/primary` e `lm-studio/primary`
- Código em `api/server.py` usa `qwen3:14b` (Ollama) hardcoded

### Impacto:
- Container falha se nenhum serviço está rodando na porta especificada
- Configuração não é clara qual backend usar
- `.env` não está criado → valores padrão incoerentes carregam

### Solução:
```bash
# Opção 1: Se usar Ollama (Docker)
ZIVA_LLM_BACKEND=ollama
ZIVA_LLM_BASE_URL=http://ziva-ollama:11434/v1  # Use container name, não localhost

# Opção 2: Se usar LM Studio (Host)
ZIVA_LLM_BACKEND=lm_studio
ZIVA_LLM_BASE_URL=http://host.docker.internal:1234/v1
```

---

## 2. ❌ SERVIÇO FALTANDO: Ollama não está em docker-compose.yml

**Arquivo**: `docker-compose.yml`

### Problema:
- `ziva-core` depende de `ollama-server` (linha `depends_on`)
- Mas `ollama-server` não é definido no compose
- Extra_hosts tenta apontar para `ollama-server:host-gateway` (incoerente)

### Impacto:
- `docker-compose up` falha com erro: `service "ollama-server" not found`
- Container fica em estado degradado aguardando serviço que nunca sobe

### Solução Recomendada:
Adicionar ao `docker-compose.yml`:
```yaml
ollama:
  image: ollama/ollama:latest
  container_name: ziva-ollama
  networks:
    - ziva-net
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
  environment:
    - OLLAMA_HOST=0.0.0.0:11434
  restart: always

volumes:
  # ... existing ...
  ollama_data:
```

OU remover `depends_on: ollama-server` se for usar host LM Studio.

---

## 3. ❌ NETWORK EXTERNA SEM INICIALIZAÇÃO

**Arquivo**: `docker-compose.yml` linha `networks:`

### Problema:
```yaml
networks:
  ziva-net:
    external: true  # ← Rede DEVE existir antes de usar
```

### Impacto:
- Primeiro `docker-compose up` falha: `network "ziva-net" not found`
- Usuário precisa rodar `docker network create ziva-net` manualmente (não documentado)

### Solução:
```yaml
networks:
  ziva-net:
    external: false  # Docker cria automaticamente
    # OU deixar como external:true + documentar:
    # docker network create ziva-net
```

---

## 4. ❌ PLAYWRIGHT_WS_ENDPOINT MAL CONFIGURADO

**Arquivo**: `docker-compose.yml` + `.env.example`

### Problema:
- Compose define: `PLAYWRIGHT_WS_ENDPOINT=ws://ziva-browser:3000` (correto, nome do service)
- `.env.example` define: `PLAYWRIGHT_WS_ENDPOINT=ws://localhost:3000` (ERRADO)
- Código em `api/server.py` pode usar valor do .env (se existir)

### Impacto:
- Se .env copia de .env.example: Playwright tenta conectar no localhost da máquina host (fora do container)
- Falha: `WebSocket connection refused on localhost:3000`

### Solução:
Atualizar `.env.example`:
```bash
PLAYWRIGHT_WS_ENDPOINT=ws://ziva-browser:3000
```

---

## 5. ⚠️ VOLUMES COM HOT-RELOAD SEM SINCRONIZAÇÃO

**Arquivo**: `docker-compose.yml` (ziva-core service)

### Problema:
```yaml
volumes:
  - ./core:/app/core         # Hot-reload Python code
  - ./api:/app/api
  - ./agent:/app/agent
  - ./scripts:/app/scripts
```

Python não recarrega módulos automaticamente durante execução de Uvicorn. Mudanças em `.py` não refletem sem restart.

### Impacto:
- Desenvolvedores pensam que código está atualizado (não está)
- Require restart do container manualmente
- Causa confusão em ambiente de desenvolvimento

### Solução:
Adicionar restart automático com `watchdog` ou usar Uvicorn `--reload`:
```yaml
# Em docker-compose.yml, mudar:
entrypoint: /app/scripts/start_docker.sh
# Para:
command: >
  bash -c "source /opt/venv/bin/activate && 
  python -m uvicorn api.server:app 
  --host 0.0.0.0 --port 8000 --reload"
```

---

## 6. ❌ MESSAGE DAEMON + BINARY SERVER NÃO SÃO MONITORED

**Arquivo**: `scripts/start_docker.sh`

### Problema:
```bash
python3 -c "from network.daemon import MessageDaemon; ..." &
DAEMON_PID=$!

python3 core/binary_server.py &
BINARY_PID=$!

/app/core/runtime/ziva_runtime &
RUNTIME_PID=$!

exec python3 -m uvicorn ...  # ← exec substitui shell, orphaning os &
```

Se API Server falha, processos background (~Message Daemon, Binary Server) ficam órfãos.

### Impacto:
- Processos background continuam rodando sem gerenciamento
- Consumem recursos após container morrer
- Logs não são capturados (apenas em background)
- Sem health checks, difícil diagnosticar

### Solução:
Usar supervisor/systemd ou re-arquitetar:
```bash
#!/bin/bash
set -e
source /opt/venv/bin/activate
export PYTHONPATH=/app
cd /app

mkdir -p /app/inbox /app/outbox /app/data
chmod -R 777 /app/data /app/inbox /app/outbox

# Rodá tudo em foreground com trap para cleanup
trap 'kill $(jobs -p) 2>/dev/null' EXIT

python3 -c "from network.daemon import MessageDaemon; daemon = MessageDaemon(); daemon.run()" &
python3 core/binary_server.py &
/app/core/runtime/ziva_runtime &

# Main process em foreground
exec python3 -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --log-level info
```

---

## 7. ⚠️ LETTA DATABASE FALTA NETWORKING

**Arquivo**: `docker-compose.yml` (letta-db + letta-server)

### Problema:
```yaml
letta-db:
  # NÃO especifica networks: ziva-net
  # Ficará em network default (bridge)

letta-server:
  networks:
    - ziva-net
  # Mas ziva-core NÃO tenta conectar a letta-server
```

### Impacto:
- letta-db e letta-server não podem comunicar (redes diferentes)
- letta-server não consegue conectar ao banco
- Serviço Letta não funciona

### Solução:
```yaml
letta-db:
  networks:
    - ziva-net  # ← Adicionar
  
letta-server:
  depends_on:
    - letta-db  # ← Adicionar
  networks:
    - ziva-net
```

---

## 8. ❌ SECRETS EXPOSTOS EM VARIÁVEIS

**Arquivo**: `docker-compose.yml` + `.env.example`

### Problema:
```yaml
environment:
  - ZIVA_LLM_KEY=${ZIVA_LLM_KEY}  # ← API KEY exposta em processo env
  - OPENAI_API_KEY=${OPENAI_API_KEY}
  - LETTA_DB_PASSWORD=${LETTA_DB_PASSWORD}
```

Secrets visíveis com `docker inspect`, `ps aux`, logs.

### Impacto:
- Qualquer pessoa com acesso ao container pode ler secrets
- Não recomendado para produção
- Viola segurança

### Solução:
Usar Docker Secrets (Swarm) ou Volume Mounts:
```yaml
ziva-core:
  environment:
    - ZIVA_LLM_KEY_FILE=/run/secrets/ziva_llm_key
  secrets:
    - ziva_llm_key

secrets:
  ziva_llm_key:
    file: ./secrets/ziva_llm_key.txt  # ← Not in git
```

---

## 9. ⚠️ QDRANT VOLUME NÃO DEFNIDO

**Arquivo**: `docker-compose.yml`

### Problema:
```yaml
qdrant:
  volumes:
    - ./qdrant_storage:/qdrant/storage  # ← Path local

volumes:
  qdrant_data:  # ← Definido mas NÃO usado
```

Qdrant usa bind mount (./qdrant_storage), não named volume.

### Impacto:
- Inconsistência: `qdrant_data` nunca é usado
- Se ./qdrant_storage não existir, Docker cria automaticamente (com permissões erradas)
- Dados podem ser perdidos se diretório é deletado

### Solução:
Usar named volume consistentemente:
```yaml
qdrant:
  volumes:
    - qdrant_data:/qdrant/storage  # ← Use named volume

volumes:
  qdrant_data:  # ← Agora é usado
```

---

## 10. ❌ KIWIX COMANDO HARDCODED E ARQUIVO FALTANDO

**Arquivo**: `docker-compose.yml`

### Problema:
```yaml
kiwix:
  command: "wikipedia_pt_all_nopic_2026-05.zim"  # ← Arquivo específico
  volumes:
    - ./data/kiwix:/data
```

Arquivo `wikipedia_pt_all_nopic_2026-05.zim` não existe, é ~20GB.

### Impacto:
- `docker-compose up` não falha imediatamente, mas Kiwix não serve conteúdo
- Container fica em estado "running" mas sem dados
- Confunde usuários

### Solução:
Tornar dinâmico ou documentar download:
```yaml
kiwix:
  command: >
    bash -c "ls /data/*.zim | head -1 | xargs -I {} /app/kiwix-serve /data/{}"
  # OU adicionar init script que baixa arquivo

# Documentação:
# Run: docker exec ziva-kiwix kiwix-download wikipedia_pt_all_nopic
```

---

## 11. ⚠️ SEARXNG SECRET_KEY NÃO GERADO

**Arquivo**: `docker-compose.yml`

### Problema:
```yaml
searxng:
  environment:
    - SEARXNG_SECRET_KEY=${SEARXNG_SECRET_KEY}  # ← Vazio se .env não existe
```

Se `.env` não for criado, `SEARXNG_SECRET_KEY` fica vazio → SearXNG usa default inseguro.

### Impacto:
- SearXNG rodando com segurança comprometida
- CSRF tokens não são validados corretamente

### Solução:
Gerar no startup:
```bash
# scripts/init_env.sh
if [ -z "$SEARXNG_SECRET_KEY" ]; then
  SEARXNG_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  echo "SEARXNG_SECRET_KEY=$SEARXNG_SECRET_KEY" >> .env
fi
```

---

## 12. ❌ DOCKERFILE MISSING NÃO EXISTE

**Arquivo**: `scripts/start_docker.sh`

### Problema:
```bash
/app/core/runtime/ziva_runtime &  # ← Executável Go
```

Arquivo existe (`./core/runtime/ziva_runtime`), mas:
1. Não é compilado no Dockerfile
2. Copiado como arquivo binário pré-compilado
3. Se arquitetura muda (Linux amd64 → arm64), binário não funciona

### Impacto:
- Dependência de binário pré-compilado
- Frágil em diferentes plataformas
- Difícil de manter

### Solução:
Adicionar build stage ao Dockerfile:
```dockerfile
# Stage 1: Build Go Runtime
FROM golang:1.23-alpine AS go-builder
WORKDIR /build
COPY core/runtime/*.go ./
COPY core/runtime/go.mod ./
RUN go build -o ziva_runtime .

# Stage 2: Python Runtime
FROM python:3.10-slim
...
COPY --from=go-builder /build/ziva_runtime /app/core/runtime/ziva_runtime
```

---

## RESUMO DE PRIORIDADES

| Nível | Problema | Ação |
|-------|----------|------|
| 🔴 CRÍTICO | Ollama vs LM Studio (conflito) | Decidir backend + corrigir compose |
| 🔴 CRÍTICO | Ollama-server faltando em compose | Adicionar serviço ou remover depends_on |
| 🔴 CRÍTICO | Network externa sem criação | Mudar external:false ou documentar |
| 🔴 CRÍTICO | Letta-db sem networking | Adicionar a ziva-net |
| 🟠 ALTO | Message Daemon + Binary Server orphaned | Implementar supervisor/systemd |
| 🟠 ALTO | Hot-reload volumes não funcionam | Adicionar --reload a Uvicorn |
| 🟡 MÉDIO | Secrets expostos em env | Usar Docker Secrets |
| 🟡 MÉDIO | PLAYWRIGHT_WS_ENDPOINT errado em .env | Corrigir para nome de container |
| 🟡 MÉDIO | Kiwix arquivo faltando | Documentar download ou tornar dinâmico |
| 🟡 MÉDIO | Go Runtime binário pré-compilado | Multi-stage build |

---

## ARQUIVOS RECOMENDADOS A CRIAR/CORRIGIR

1. ✅ `.env` (de `.env.example` + ajustes)
2. ✅ `docker-compose-fixed.yml` (versão corrigida)
3. ✅ `scripts/init_env.sh` (geração de secrets)
4. ✅ `Dockerfile.fixed` (multi-stage com Go)
5. ✅ `DOCKER_SETUP.md` (guia de inicialização)
