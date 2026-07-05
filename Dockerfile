# Base Image: Python 3.10 Slim (Leve e compatível)
FROM python:3.10-slim

# Metadados
LABEL maintainer="Ziva AI Team"
LABEL version="2.4"
LABEL description="Ziva Autonomous Agent Container"

# Variáveis de Ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    VIRTUAL_ENV=/opt/venv

# 1. Instalar dependências de sistema
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

# 2. Configurar Ambiente Virtual
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 3. Workdir
WORKDIR /app

# 4. Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install rich requests psutil qdrant-client sentence-transformers

# 5. Copiar Código Fonte
COPY . .

# 6. Expor Portas (API = 8000, P2P = 9000)
EXPOSE 8000
EXPOSE 9000

# 7. Script de Inicialização
COPY scripts/start_docker.sh /app/start_docker.sh
RUN chmod +x /app/start_docker.sh

# Entrypoint
ENTRYPOINT ["/app/start_docker.sh"]
