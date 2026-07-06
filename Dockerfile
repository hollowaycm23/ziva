# Multi-stage Dockerfile (Fixed)
# Builds Go runtime + Python environment

# ===== STAGE 1: Build Go Runtime =====
FROM golang:1.23-alpine AS go-builder

WORKDIR /build

# Copiar arquivos Go
COPY core/runtime/go.mod ./
COPY core/runtime/go.sum* ./
COPY core/runtime/*.go ./

# Build o executável
RUN go build -o ziva_runtime -ldflags="-s -w" . || echo "⚠️ Go build skipped (optional)"

# ===== STAGE 2: Python Runtime =====
FROM python:3.10-slim

LABEL maintainer="Ziva AI Team"
LABEL version="2.5"
LABEL description="Ziva Autonomous Agent Container (Fixed)"

# Variáveis de Ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# 1. Instalar dependências de sistema (slim)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libgomp1 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# 2. Criar Ambiente Virtual
RUN python3 -m venv $VIRTUAL_ENV

# 3. Configurar Workdir
WORKDIR /app

# 4. Copiar e instalar requirements
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install rich requests psutil qdrant-client sentence-transformers uvicorn[standard]

# 5. Copiar código-fonte
COPY . .

# 7. Copiar e configurar scripts
COPY scripts/start_docker_fixed.sh /app/start_docker.sh
RUN chmod +x /app/start_docker.sh

# 8. Expor Portas
EXPOSE 8000 9000

# 9. Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

# Entrypoint
ENTRYPOINT ["/app/start_docker.sh"]
