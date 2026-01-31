# Sistema Multi-Agente Ziva - Guia de Uso

## Visão Geral

Sistema de orquestração multi-agente inspirado no AutoGen, otimizado para hardware local com gestão inteligente de recursos.

## Especificações de Hardware

- **RAM:** 32GB total → 24GB disponível para agentes
- **CPU:** i7-12700KF (12 cores) → 10 cores disponíveis
- **GPU:** RTX 4070 12GB VRAM → 10GB disponível
- **Limite:** Máximo 3 agentes ativos simultaneamente

## Agentes Especializados

### 1. CodingAgent
- **Modelo:** `deepseek-coder:6.7b` ou `qwen2.5-coder:7b`
- **Recursos:** 6GB RAM, 5GB VRAM, 2 CPU cores
- **Funções:**
  - Geração de código
  - Refatoração
  - Documentação
  - Code review

### 2. ResearchAgent
- **Modelo:** `llama3.2:3b`
- **Recursos:** 4GB RAM, 2GB VRAM, 1 CPU core
- **Funções:**
  - Busca web
  - Lookup de documentação
  - Verificação de versões de pacotes

### 3. DebugAgent
- **Modelo:** `qwen2.5:7b`
- **Recursos:** 6GB RAM, 5GB VRAM, 2 CPU cores
- **Funções:**
  - Análise de erros
  - Geração de testes
  - Validação de código
  - Profiling

### 4. PlannerAgent
- **Modelo:** `llama3.2:3b`
- **Recursos:** 4GB RAM, 2GB VRAM, 1 CPU core
- **Funções:**
  - Decomposição de tarefas
  - Delegação de agentes
  - Otimização de workflows

## Uso via API

### 1. Inicializar Sistema Multi-Agente

```python
from core.multi_agent_init import initialize_multi_agent_system

# Inicializa com limites de hardware
manager = initialize_multi_agent_system(
    max_concurrent_agents=3,
    max_ram_gb=24.0,
    max_vram_gb=10.0
)
```

### 2. Delegar Tarefa via API REST

```bash
curl -X POST http://localhost:8000/api/v1/multi_agent/task \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "task": "Create a REST API for user authentication with JWT",
    "preferred_role": "coding"
  }'
```

**Resposta:**
```json
{
  "status": "success",
  "message": "Task delegated successfully",
  "agent_id": "coding_1704297600000",
  "agent_role": "coding"
}
```

### 3. Verificar Status dos Agentes

```bash
curl http://localhost:8000/api/v1/agents/status
```

**Resposta:**
```json
{
  "multi_agent_enabled": true,
  "active_agents": 2,
  "max_agents": 3,
  "agents": [
    {
      "agent_id": "coding_1704297600000",
      "role": "coding",
      "state": "busy",
      "model_loaded": "deepseek-coder:6.7b",
      "memory_usage_mb": 5832
    }
  ],
  "resources": {
    "ram": {
      "agents_total_gb": 10.2,
      "available_gb": 13.8
    },
    "vram": {
      "used_gb": 4.8,
      "available_gb": 5.2
    }
  }
}
```

### 4. Spawnar Agente Específico

```bash
curl -X POST http://localhost:8000/api/v1/agents/spawn \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "role": "research",
    "agent_id": "my_researcher"
  }'
```

### 5. Terminar Agente

```bash
curl -X DELETE http://localhost:8000/api/v1/agents/my_researcher \
  -H "X-API-Key: your-api-key"
```

### 6. Monitorar Recursos

```bash
curl http://localhost:8000/api/v1/resources
```

## Uso Programático

### Exemplo 1: Workflow de Desenvolvimento

```python
from core.multi_agent_init import initialize_multi_agent_system

# Inicializar
manager = initialize_multi_agent_system()

# 1. Planner decompõe tarefa
planner_id = manager.spawn_agent("planner")
task = {
    "type": "task_decomposition",
    "description": "Build a microservice for image processing"
}
manager.delegate_task(task, preferred_role="planner")

# 2. Research busca bibliotecas
research_id = manager.spawn_agent("research")
research_task = {
    "type": "documentation",
    "library": "Pillow",
    "topic": "image manipulation"
}

# 3. Coding implementa
coding_id = manager.spawn_agent("coding")
code_task = {
    "type": "code_generation",
    "specification": "Create image resizing endpoint using FastAPI and Pillow"
}

# 4. Debug valida
debug_id = manager.spawn_agent("debug")
debug_task = {
    "type": "test_generation",
    "code": generated_code,
    "framework": "pytest"
}

# Cleanup
manager.shutdown()
```

### Exemplo 2: Colaboração entre Agentes

```python
from core.agent_manager import get_manager
from core.base_agent import Message

manager = get_manager()

# Spawnar agentes
research_id = manager.spawn_agent("research")
coding_id = manager.spawn_agent("coding")

# Research envia resultado para Coding
research_agent = manager.active_agents[research_id]
coding_agent = manager.active_agents[coding_id]

# Enviar mensagem
research_agent.send_message(
    to_agent=coding_id,
    content={
        "type": "research_result",
        "library": "FastAPI",
        "best_practices": "Use dependency injection for database connections"
    },
    priority=8
)
```

## Comunicação Binária com LLMs

O sistema utiliza comunicação binária eficiente via Ollama API para otimizar latência:

```python
# ModelLoader usa requests direto para Ollama
import requests

response = requests.post(
    "http://127.0.0.1:11434/api/generate",
    json={
        "model": "deepseek-coder:6.7b",
        "prompt": prompt,
        "stream": False  # Binário não-streaming para baixa latência
    },
    timeout=60
)
```

## Gestão de Recursos

### Monitoramento Automático

O `ResourceMonitor` rastreia em tempo real:

```python
from core.resource_monitor import get_monitor

monitor = get_monitor()
summary = monitor.get_summary()

print(f"RAM: {summary['ram']['agents_total_gb']:.2f}GB / 24GB")
print(f"VRAM: {summary['vram']['used_gb']:.2f}GB / 10GB")
print(f"Agentes ativos: {summary['agents']['active']} / 3")
```

### Política de Modelo Único

Apenas **1 modelo LLM carregado em VRAM** por vez:

```python
from core.model_loader import get_loader

loader = get_loader()

# Carrega modelo para agente
loader.load_model("deepseek-coder:6.7b", "coding_agent_1")

# Ao carregar outro modelo, o anterior é descarregado automaticamente
loader.load_model("llama3.2:3b", "research_agent_1")
# deepseek-coder:6.7b foi descarregado
```

### Unload Automático por Inatividade

Modelos são descarregados após 30s de inatividade:

```python
# ModelLoader verifica idle timeout
loader.check_idle_unload()  # Chamado automaticamente pelo maintenance thread
```

## Testes

### Executar Suite de Testes

```bash
cd /home/holloway/ziva
source agent_venv/bin/activate
pytest tests/test_multi_agent.py -v
```

### Testes Disponíveis

- `test_initialization` - Inicialização do ResourceMonitor
- `test_resource_allocation` - Alocação de recursos
- `test_max_agents_limit` - Limite de 3 agentes
- `test_agent_registration` - Registro de agentes
- `test_agent_spawning` - Spawn de agentes
- `test_task_delegation` - Delegação de tarefas

## Troubleshooting

### Erro: "Max concurrent agents reached"

**Solução:** Termine um agente inativo antes de spawnar novo:

```python
# Verificar agentes ativos
agents = manager.list_agents()
idle_agents = [a for a in agents if a['state'] == 'idle']

# Terminar agente idle
if idle_agents:
    manager.terminate_agent(idle_agents[0]['agent_id'])
```

### Erro: "Insufficient VRAM"

**Solução:** Use modelos menores ou aguarde unload automático:

```python
# Forçar unload de modelo atual
loader = get_loader()
loader.unload_model(current_agent_id)

# Ou usar modelo menor
manager.spawn_agent("research")  # Usa llama3.2:3b (1.9GB)
```

### Erro: "Ollama not available"

**Solução:** Iniciar Ollama:

```bash
ollama serve
```

## Próximos Passos

1. **Otimização de Performance:** Benchmark de latência entre agentes
2. **Persistência:** Salvar estado de agentes no banco de dados
3. **Observabilidade:** Dashboard em tempo real de recursos
4. **Auto-scaling:** Ajuste dinâmico de recursos baseado em carga

## Referências

- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [pynvml Documentation](https://pypi.org/project/pynvml/)
