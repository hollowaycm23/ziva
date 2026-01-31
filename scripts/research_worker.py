"""
Research Queue Worker - Executa pesquisas profundas em sequência
"""
from typing import List, Dict
from core.llm import LLMService
from core.vector_store import VectorStore
import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class ResearchWorker:
    """
    Worker que executa pesquisas em fila e armazena no Qdrant.
    """

    def __init__(self):
        self.llm = LLMService(model="nomic-embed-text:latest")
        self.vs = VectorStore()
        self.queue = []
        self.completed = []
        self.failed = []

    def add_research(self, topic: str, content: str, metadata: Dict = None):
        """Adiciona pesquisa à fila."""
        self.queue.append({
            "topic": topic,
            "content": content,
            "metadata": metadata or {}
        })

    def process_queue(self):
        """Processa todas as pesquisas na fila."""
        total = len(self.queue)
        print(f"\n{'=' * 80}")
        print(f"🔬 RESEARCH QUEUE WORKER")
        print(f"{'=' * 80}")
        print(f"Total de pesquisas: {total}\n")

        for idx, research in enumerate(self.queue, 1):
            print(f"\n[{idx}/{total}] 📚 Processando: {research['topic']}")
            print(f"{'-' * 80}")

            try:
                # Gerar embedding
                print(f"  🧠 Gerando embedding...")
                embedding = self.llm.embedding(research['content'])

                if not embedding:
                    raise Exception("Falha ao gerar embedding")

                # Armazenar no Qdrant
                print(f"  💾 Armazenando no Qdrant...")
                metadata = {
                    "source": "research_worker",
                    "topic": research['topic'],
                    "language": "pt-BR",
                    **research['metadata']
                }

                self.vs.add_text(
                    text=research['content'],
                    embedding=embedding,
                    metadata=metadata
                )

                self.completed.append(research['topic'])
                print(f"  ✅ Concluído: {research['topic']}")

                # Pequeno delay para não sobrecarregar
                time.sleep(0.5)

            except Exception as e:
                self.failed.append({
                    "topic": research['topic'],
                    "error": str(e)
                })
                print(f"  ❌ Erro: {str(e)}")

        # Resumo final
        print(f"\n{'=' * 80}")
        print(f"📊 RESUMO DA EXECUÇÃO")
        print(f"{'=' * 80}")
        print(f"✅ Concluídas: {len(self.completed)}/{total}")
        print(f"❌ Falharam: {len(self.failed)}/{total}")

        if self.completed:
            print(f"\n✅ Pesquisas concluídas:")
            for topic in self.completed:
                print(f"   - {topic}")

        if self.failed:
            print(f"\n❌ Pesquisas falhadas:")
            for item in self.failed:
                print(f"   - {item['topic']}: {item['error']}")


def create_research_queue():
    """Cria fila de pesquisas sobre os tópicos solicitados."""
    worker = ResearchWorker()

    # ========================================================================
    # PESQUISA 1: Python - Melhores Práticas e Indentação
    # ========================================================================

    research_1 = """
Python: Melhores Práticas, Indentação e Código Limpo

1. INDENTAÇÃO E ESTILO (PEP 8):

a) Regras de Indentação:
   - Usar 4 espaços (NUNCA tabs)
   - Consistência é crucial
   - Evitar misturar espaços e tabs

   Exemplo Correto:
   ```python
   def funcao():
       if condicao:
           print("Correto")
       return True
   ```

b) Comprimento de Linha:
   - Máximo: 79 caracteres (código)
   - Máximo: 72 caracteres (comentários/docstrings)
   - Quebrar linhas longas com \\ ou parênteses

c) Imports:
   - Ordem: stdlib → third-party → local
   - Um import por linha
   - Usar absolute imports

   ```python
   import os
   import sys

   import numpy as np
   from langchain import LLM

   from core.agent import nodes
   ```

2. NAMING CONVENTIONS:

- Classes: PascalCase (MyClass)
- Funções/variáveis: snake_case (my_function)
- Constantes: UPPER_CASE (MAX_SIZE)
- Privados: _leading_underscore (_private)
- Dunder: __double_underscore__ (__init__)

3. DOCSTRINGS E COMENTÁRIOS:

```python
def calculate_score(data: list, threshold: float = 0.5) -> float:
    \"\"\"
    Calcula score baseado em threshold.

    Args:
        data: Lista de valores numéricos
        threshold: Valor mínimo para considerar

    Returns:
        Score calculado (0.0 a 1.0)

    Raises:
        ValueError: Se data estiver vazia
    \"\"\"
    if not data:
        raise ValueError("Data cannot be empty")
    return sum(x for x in data if x > threshold) / len(data)
```

4. TYPE HINTS (Python 3.5+):

```python
from typing import List, Dict, Optional, Union

def process_items(
    items: List[str],
    config: Dict[str, Any],
    max_count: Optional[int] = None
) -> Union[List[str], None]:
    pass
```

5. MELHORES PRÁTICAS:

a) List Comprehensions (preferir):
   ```python
   # Bom
   squares = [x**2 for x in range(10)]

   # Evitar
   squares = []
   for x in range(10):
       squares.append(x**2)
   ```

b) Context Managers:
   ```python
   # Sempre usar with para arquivos
   with open('file.txt', 'r') as f:
       data = f.read()
   ```

c) Generators (economia de memória):
   ```python
   def read_large_file(file_path):
       with open(file_path) as f:
           for line in f:
               yield line.strip()
   ```

6. FERRAMENTAS:

- black: Auto-formatter
- flake8: Linter
- mypy: Type checker
- pylint: Code analyzer
- isort: Import organizer

Comando: `black . && flake8 . && mypy .`
"""

    worker.add_research(
        topic="Python: Melhores Práticas e Indentação",
        content=research_1,
        metadata={"category": "programming", "language_specific": "python"}
    )

    # ========================================================================
    # PESQUISA 2: Ollama e Variantes (ollama.cpp)
    # ========================================================================

    research_2 = """
Ollama e Variantes: Guia Completo

1. OLLAMA - OVERVIEW:

a) O que é:
   - Runtime para LLMs locais
   - Baseado em llama.cpp
   - Interface simples (Docker-like)
   - Suporta múltiplos modelos

b) Instalação:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

c) Uso Básico:
   ```bash
   ollama run llama3.1:8b
   ollama list
   ollama pull mistral
   ```

2. LLAMA.CPP - ENGINE SUBJACENTE:

a) Características:
   - C++ puro (alta performance)
   - Quantização (reduz VRAM)
   - CPU e GPU support
   - Criado por Georgi Gerganov

b) Compilação:
   ```bash
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp
   make LLAMA_CUBLAS=1  # Para NVIDIA GPU
   ```

c) Uso Direto:
   ```bash
   ./main -m models/llama-7b.gguf -p "Hello" -n 128
   ```

3. QUANTIZAÇÃO - REDUÇÃO DE VRAM:

Formatos (menor → maior qualidade):
- Q2_K: 2-bit (muito comprimido, baixa qualidade)
- Q4_K_M: 4-bit (bom balanço)
- Q5_K_M: 5-bit (boa qualidade)
- Q8_0: 8-bit (alta qualidade)
- F16: 16-bit (qualidade máxima)

Exemplo:
```bash
# Baixar modelo quantizado
ollama pull llama3.1:8b-q4_K_M
```

4. OTIMIZAÇÃO PARA HARDWARE:

a) 10GB VRAM (ex: RTX 3080):
   - Modelos recomendados:
     * llama3.1:8b-q4_K_M (~5GB)
     * mistral:7b-q4_K_M (~4GB)
     * qwen2.5:7b-q4_K_M (~4GB)

   - Configuração:
     ```bash
     # Modelfile
     FROM llama3.1:8b-q4_K_M
     PARAMETER num_gpu 1
     PARAMETER num_thread 8
     ```

b) 32GB RAM DDR4 3200MHz (sem GPU dedicada):
   - Usar CPU inference
   - Modelos recomendados:
     * llama3.1:8b-q4_K_M (CPU)
     * phi3:3.8b-mini-q4_K_M (~2GB)

   - Otimizações:
     ```bash
     # Aumentar threads
     OLLAMA_NUM_THREADS=16 ollama run llama3.1:8b
     ```

5. PERFORMANCE TUNING:

a) Variáveis de Ambiente:
   ```bash
   export OLLAMA_NUM_PARALLEL=2        # Requests paralelos
   export OLLAMA_MAX_LOADED_MODELS=2   # Modelos em memória
   export OLLAMA_NUM_THREADS=16        # Threads CPU
   export OLLAMA_FLASH_ATTENTION=1     # Flash attention
   ```

b) GPU Offloading:
   ```bash
   # Modelfile
   PARAMETER num_gpu 35  # Camadas na GPU
   PARAMETER num_thread 8
   PARAMETER num_ctx 4096  # Context window
   ```

6. ALTERNATIVAS E VARIANTES:

a) LocalAI:
   - API compatível com OpenAI
   - Suporta mais backends
   - Docker-first

b) LM Studio:
   - GUI para llama.cpp
   - Fácil para iniciantes
   - Windows/Mac/Linux

c) Text Generation WebUI (oobabooga):
   - Interface web completa
   - Muitas opções de customização
   - Suporta LoRA, quantização

7. MODELOS OTIMIZADOS:

Para 10GB VRAM:
- Llama 3.1 8B (Q4_K_M): ~5GB
- Mistral 7B (Q4_K_M): ~4GB
- Qwen 2.5 7B (Q4_K_M): ~4GB
- Phi-3 Medium (Q4_K_M): ~8GB

Para 32GB RAM (CPU):
- Llama 3.1 8B (Q4_K_M): Rápido
- Phi-3 Mini (Q4_K_M): Muito rápido
- Gemma 2 9B (Q4_K_M): Boa qualidade

8. BENCHMARK E TESTES:

```bash
# Testar velocidade
time ollama run llama3.1:8b "Write a poem" --verbose

# Monitorar VRAM
nvidia-smi -l 1

# Monitorar RAM
htop
```
"""

    worker.add_research(
        topic="Ollama e Variantes (llama.cpp, Quantização)",
        content=research_2,
        metadata={"category": "llm", "subcategory": "local_inference"}
    )

    # ========================================================================
    # PESQUISA 3: Otimizações para Agentes Locais em WSL2/Linux
    # ========================================================================

    research_3 = """
Otimizações para Agentes Locais em WSL2 e Linux

1. WSL2 - CONFIGURAÇÕES ESSENCIAIS:

a) .wslconfig (C:\\Users\\<user>\\.wslconfig):
   ```ini
   [wsl2]
   memory=24GB              # Limite de RAM
   processors=12            # CPUs virtuais
   swap=8GB                 # Swap
   localhostForwarding=true # Port forwarding
   ```

b) GPU Passthrough (NVIDIA):
   ```bash
   # Verificar GPU
   nvidia-smi

   # Instalar CUDA Toolkit
   wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
   sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
   sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/3bf863cc.pub
   sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/ /"
   sudo apt update
   sudo apt install cuda-toolkit-12-3
   ```

2. LINUX - OTIMIZAÇÕES DE SISTEMA:

a) Swappiness (reduzir uso de swap):
   ```bash
   # Ver atual
   cat /proc/sys/vm/swappiness

   # Reduzir (10 = menos swap)
   sudo sysctl vm.swappiness=10

   # Permanente
   echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf
   ```

b) File Descriptors (para muitas conexões):
   ```bash
   # Aumentar limite
   ulimit -n 65536

   # Permanente (/etc/security/limits.conf)
   * soft nofile 65536
   * hard nofile 65536
   ```

c) Transparent Huge Pages (THP):
   ```bash
   # Desabilitar (melhora latência)
   echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
   ```

3. PYTHON - OTIMIZAÇÕES:

a) Virtual Environment:
   ```bash
   python3 -m venv agent_venv
   source agent_venv/bin/activate
   pip install --upgrade pip setuptools wheel
   ```

b) Usar uvloop (async mais rápido):
   ```python
   import uvloop
   uvloop.install()
   ```

c) Caching com functools:
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=128)
   def expensive_function(arg):
       return result
   ```

4. OLLAMA - OTIMIZAÇÕES ESPECÍFICAS:

a) Systemd Service (auto-start):
   ```bash
   sudo systemctl enable ollama
   sudo systemctl start ollama
   ```

b) Configuração de Performance:
   ```bash
   # ~/.bashrc ou /etc/environment
   export OLLAMA_HOST=0.0.0.0:11434
   export OLLAMA_ORIGINS=*
   export OLLAMA_NUM_PARALLEL=4
   export OLLAMA_MAX_LOADED_MODELS=2
   export OLLAMA_FLASH_ATTENTION=1
   export OLLAMA_NUM_THREADS=16
   ```

c) Modelfile Otimizado:
   ```
   FROM llama3.1:8b-q4_K_M

   PARAMETER num_ctx 4096
   PARAMETER num_gpu 35
   PARAMETER num_thread 8
   PARAMETER temperature 0.7
   PARAMETER top_p 0.9
   PARAMETER repeat_penalty 1.1
   ```

5. QDRANT - OTIMIZAÇÕES:

a) Docker Compose Otimizado:
   ```yaml
   version: '3.8'
   services:
     qdrant:
       image: qdrant/qdrant:latest
       ports:
         - "6333:6333"
       volumes:
         - ./qdrant_data:/qdrant/storage
       environment:
         - QDRANT__SERVICE__GRPC_PORT=6334
       deploy:
         resources:
           limits:
             memory: 4G
   ```

b) Configuração de Collection:
   ```python
   from qdrant_client.models import VectorParams, Distance

   client.create_collection(
       collection_name="knowledge",
       vectors_config=VectorParams(
           size=768,
           distance=Distance.COSINE,
           on_disk=False  # Manter em RAM (mais rápido)
       ),
       optimizers_config={
           "indexing_threshold": 10000,
           "memmap_threshold": 50000
       }
   )
   ```

6. NGINX - REVERSE PROXY (Produção):

```nginx
upstream ollama {
    server localhost:11434;
    keepalive 32;
}

server {
    listen 80;
    server_name ollama.local;

    location / {
        proxy_pass http://ollama;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
    }
}
```

7. MONITORAMENTO:

a) Recursos do Sistema:
   ```bash
   # CPU/RAM
   htop

   # GPU
   nvidia-smi -l 1
   watch -n 1 nvidia-smi

   # Disco
   iotop
   ```

b) Logs do Ollama:
   ```bash
   journalctl -u ollama -f
   ```

c) Python Profiling:
   ```python
   import cProfile
   import pstats

   profiler = cProfile.Profile()
   profiler.enable()
   # ... código ...
   profiler.disable()
   stats = pstats.Stats(profiler)
   stats.sort_stats('cumulative')
   stats.print_stats(20)
   ```

8. DICAS E MACETES:

a) Pré-carregar Modelos:
   ```bash
   # Carregar modelo na inicialização
   ollama pull llama3.1:8b-q4_K_M
   curl http://localhost:11434/api/generate -d '{
     "model": "llama3.1:8b-q4_K_M",
     "prompt": "warmup",
     "stream": false
   }'
   ```

b) Batch Processing:
   ```python
   # Processar múltiplas queries em batch
   async def batch_process(queries):
       tasks = [process_query(q) for q in queries]
       return await asyncio.gather(*tasks)
   ```

c) Connection Pooling:
   ```python
   import httpx

   client = httpx.AsyncClient(
       limits=httpx.Limits(
           max_keepalive_connections=20,
           max_connections=100
       )
   )
   ```

9. TROUBLESHOOTING:

a) Ollama não responde:
   ```bash
   sudo systemctl restart ollama
   sudo journalctl -u ollama -n 50
   ```

b) VRAM insuficiente:
   ```bash
   # Usar modelo menor ou mais quantizado
   ollama pull llama3.1:8b-q4_K_M  # Em vez de Q8
   ```

c) CPU 100%:
   ```bash
   # Reduzir threads
   export OLLAMA_NUM_THREADS=8
   ```

10. CHECKLIST DE OTIMIZAÇÃO:

- [ ] WSL2: Configurar .wslconfig
- [ ] GPU: Instalar CUDA Toolkit
- [ ] Swappiness: Reduzir para 10
- [ ] Ollama: Configurar variáveis de ambiente
- [ ] Python: Usar uvloop
- [ ] Qdrant: on_disk=False
- [ ] Modelos: Usar Q4_K_M
- [ ] Monitoramento: nvidia-smi, htop
- [ ] Logs: journalctl -u ollama
- [ ] Pré-carregar: Warmup de modelos
"""

    worker.add_research(
        topic="Otimizações para Agentes Locais (WSL2/Linux)",
        content=research_3,
        metadata={"category": "optimization", "platform": "wsl2_linux"}
    )

    return worker


if __name__ == "__main__":
    worker = create_research_queue()
    worker.process_queue()
