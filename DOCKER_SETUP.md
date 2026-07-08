# 🚀 Guia de Configuração Docker - Ziva

## 📋 Pré-requisitos

- Docker 20.10+
- Docker Compose 2.0+
- 16GB RAM mínimo (32GB recomendado para Ollama + Ziva)
- ~50GB espaço em disco

## 🔧 Instalação Passo a Passo

### 1. Clonar/Preparar Projeto

```bash
cd /path/to/ziva
```

### 2. Criar Network Docker

```bash
docker network create ziva-net
```

### 3. Gerar .env

```bash
cp .env.production .env
```

Editar `.env` com valores específicos:
```bash
nano .env
```

**Campos críticos a preencher:**

```bash
# Escolher backend LLM
ZIVA_LLM_BACKEND=ollama

# Gerar secrets (copie output)
python3 << EOF
import secrets
print("SEARXNG_SECRET_KEY=" + secrets.token_hex(32))
print("WEBUI_SECRET_KEY=" + secrets.token_hex(16))
print("LETTA_DB_PASSWORD=" + secrets.token_hex(16))
EOF
```

### 4. Usar Docker Compose Corrigido

```bash
# Use a versão corrigida
cp docker-compose-fixed.yml docker-compose.yml

# Ou se quiser manter ambos:
docker-compose -f docker-compose-fixed.yml up -d
```

### 5. Verificar Inicialização

```bash
# Aguardar ~30-60 segundos para todos services estarem prontos
sleep 60

# Ver status dos containers
docker ps

# Esperado (todos com status "Up"):
# ziva-core
# ziva-ollama
# ziva-qdrant
# ziva-searxng
# ziva-kiwix
# ziva-openwebui
# ziva-browser
# letta-db
# letta-server
```

### 6. Verificar Health

```bash
# API Health
curl http://localhost:8000/v1/health

# Esperado:
# {"status":"healthy","services":{...}}

# Ollama Ready
curl http://localhost:11434/api/tags

# Qdrant Ready
curl http://localhost:6333/health

# Open WebUI
open http://localhost:3000
```

---

## 🐛 Troubleshooting

### Problema: Container ziva-core entra em CrashLoopBackOff

```bash
# 1. Ver logs
docker logs ziva-core

# 2. Checar errors comuns:
# - "service "ollama-server" not found" → Use docker-compose-fixed.yml
# - "connection refused" → Aguarde 30s para Ollama inicializar
# - "PYTHONPATH" → Verificar variável de ambiente em .env
```

### Problema: Ziva não consegue conectar ao Ollama

```bash
# Verificar se Ollama está rodando
docker ps | grep ollama

# Testar conexão dentro do container
docker exec ziva-core curl http://ollama:11434/api/tags

# Se falhar, entrar no container e debugar
docker exec -it ziva-core bash
# Dentro do container:
curl -v http://ollama:11434/api/tags
# Verificar /etc/hosts
cat /etc/hosts
```

### Problema: "Network ziva-net not found"

```bash
# Recriar network
docker network create ziva-net 2>/dev/null || true

# Ou editar docker-compose para criar automaticamente:
# networks:
#   ziva-net:
#     driver: bridge
```

### Problema: Playwright/Browser não conecta

```bash
# Verificar se container browser está rodando
docker logs ziva-browser

# Conectar do container Ziva
docker exec ziva-core curl -v ws://ziva-browser:3000/

# Se timeout, browser pode estar sem memória
docker stats ziva-browser
```

### Problema: Erro "No such file: /app/core/runtime/ziva_runtime"

```bash
# 1. Verificar se arquivo existe localmente
ls -la core/runtime/ziva_runtime

# 2. Se não existir, usar Dockerfile.fixed que compila via Docker
docker build -f Dockerfile.fixed -t ziva:latest .

# 3. Se existir mas é binário wrong arch:
# Recompilar no Alpine:
docker run --rm -v $(pwd)/core/runtime:/work golang:1.23-alpine \
  sh -c "cd /work && go build -o ziva_runtime ."
```

### Problema: Banco de dados corrompido

```bash
# Limpar volumes (CUIDADO - perde dados)
docker-compose down -v

# Recriar do zero
docker-compose up -d
```

---

## 📊 Monitoramento

### Logs em Real-time

```bash
# Seguir logs do Ziva Core
docker logs -f ziva-core

# Ver logs de todos os serviços
docker-compose logs -f

# Logs específicos
docker logs -f ziva-core --tail 50 | grep ERROR
```

### Métricas de Recursos

```bash
# Monitorar uso em tempo real
docker stats

# Apenas ziva-core
docker stats ziva-core

# Salvar snapshot de stats
docker stats --no-stream > stats.txt
```

### Verificar Database

```bash
# SQLite
docker exec ziva-core sqlite3 /app/data/ziva.db ".tables"

# Qdrant REST API
curl http://localhost:6333/collections

# Letta PostgreSQL
docker exec ziva-letta-db psql -U letta_user -d lettadb -c "\dt"
```

---

## 🚀 Deploy em Produção

### 1. Usar Docker Compose com restart policies

```yaml
services:
  ziva-core:
    restart: unless-stopped  # ← Importante
```

### 2. Usar Secrets Docker (Swarm mode)

```bash
docker secret create ziva_llm_key <(echo "your-key-here")

# Em docker-compose:
ziva-core:
  secrets:
    - ziva_llm_key
  environment:
    ZIVA_LLM_KEY_FILE: /run/secrets/ziva_llm_key
```

### 3. Backup Periódico

```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backups/ziva-$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

docker-compose exec -T qdrant tar czf - /qdrant/storage > $BACKUP_DIR/qdrant.tar.gz
docker-compose exec -T ziva-core tar czf - /app/data > $BACKUP_DIR/app_data.tar.gz
docker-compose exec -T letta-db pg_dump -U letta_user lettadb > $BACKUP_DIR/letta.sql

# Guardar por 30 dias
find /backups -name "ziva-*" -mtime +30 -delete
```

### 4. Logging Centralizado

```yaml
# Adicionar a docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "100m"
    max-file: "10"
    labels: "ziva.service"
```

---

## ✅ Checklist de Inicialização

- [ ] Network `ziva-net` existe
- [ ] `.env` preenchido com valores únicos
- [ ] `docker-compose-fixed.yml` renomeado para `docker-compose.yml`
- [ ] `go.mod` existe em `core/runtime/` (se compilando)
- [ ] 16GB+ RAM disponível
- [ ] `docker ps` mostra todos 9 containers em estado "Up"
- [ ] `curl http://localhost:8000/v1/health` retorna 200 OK
- [ ] `curl http://localhost:11434/api/tags` retorna array de modelos
- [ ] Open WebUI acessível em http://localhost:3000

---

## 📞 Suporte

Se tiver problema:

1. Verificar logs: `docker logs <container_name>`
2. Verificar network: `docker network inspect ziva-net`
3. Verificar volumes: `docker volume ls | grep ziva`
4. Limpar e reconstruir: `docker-compose down -v && docker-compose up -d --build`
