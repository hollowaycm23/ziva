# Guia Rápido: Sistema de Aprendizado da Ziva

## 🚀 Início Rápido

### 1. Coletar Dados de Treinamento
```bash
python -c "from core.training_data_collector import TrainingDataCollector; c = TrainingDataCollector(); print(f'Coletados: {c.collect_from_sessions()} exemplos')"
```

### 2. Criar Datasets
```bash
python -c "from core.dataset_builder import DatasetBuilder; b = DatasetBuilder(); print(f'Dataset: {b.build_alpaca_dataset()} exemplos')"
```

### 3. Verificar Gabrielle
```bash
python -c "from core.p2p_learning import GabrielleConnector; g = GabrielleConnector(); print(f'Conectada: {g.is_connected}')"
```

### 4. Executar Pipeline Completo (Requer GPU)
```bash
python scripts/run_finetuning_pipeline.py
```

## 📚 Componentes

### Data Collection
- **Arquivo**: `core/training_data_collector.py`
- **Função**: Extrai interações bem-sucedidas
- **Quality Score**: 0-1 (baseado em JSON válido, clareza, sem erros)

### Dataset Builder
- **Arquivo**: `core/dataset_builder.py`
- **Formatos**: Alpaca, ShareGPT
- **Output**: `data/training/*.json`

### LoRA Trainer
- **Arquivo**: `training/lora_trainer.py`
- **Técnica**: QLoRA (4-bit quantization)
- **Hardware**: GPU 8GB+ VRAM

### Teacher-Student
- **Arquivo**: `training/teacher_student.py`
- **Teacher**: LLM maior (70B+)
- **Função**: Gera dados sintéticos de alta qualidade

### P2P Learning
- **Arquivo**: `core/p2p_learning.py`
- **Função**: Compartilha conhecimento com Gabrielle
- **Protocolo**: HTTP/JSON

## 🎯 Workflows

### Workflow 1: Aprendizado Local
```python
# 1. Coletar dados
collector = TrainingDataCollector()
count = collector.collect_from_sessions(min_quality=0.8)

# 2. Criar dataset
builder = DatasetBuilder()
builder.build_alpaca_dataset()

# 3. Treinar (requer GPU)
from training.lora_trainer import train_ziva_adapter
adapter = train_ziva_adapter("data/training/alpaca_dataset.json", "general")
```

### Workflow 2: Aprendizado com Teacher
```python
# 1. Inicializar teacher
from training.teacher_student import TeacherLLM, StudentTrainer
teacher = TeacherLLM(provider="ollama", model="qwen2.5-coder:32b")
trainer = StudentTrainer(teacher)

# 2. Gerar dados sintéticos
dataset = trainer.create_synthetic_dataset(
    tasks=["web scraping", "data processing"],
    examples_per_task=50
)

# 3. Treinar com dados sintéticos
adapter = train_ziva_adapter(dataset, "synthetic")
```

### Workflow 3: Aprendizado Colaborativo (P2P)
```python
# 1. Conectar com Gabrielle
from core.p2p_learning import P2PLearningNode
node = P2PLearningNode(node_name="ziva", peers=["http://falcon:9000"])

# 2. Sincronizar conhecimento
node.sync_with_peers()

# 3. Treinamento colaborativo
adapter = node.collaborative_training(task_type="code-execution")
```

## 🔧 Configuração

### Requisitos de Hardware
- **Mínimo**: GPU 8GB, RAM 16GB, Storage 50GB
- **Recomendado**: GPU 12GB+, RAM 32GB, Storage 100GB

### Dependências
```bash
pip install transformers peft bitsandbytes datasets accelerate trl
```

### Modelos Teacher Recomendados
- `qwen2.5-coder:32b` (local via Ollama)
- `llama3.1:70b` (local via Ollama)
- `gpt-4` (OpenAI - requer API key)

## 📊 Monitoramento

### Verificar Dados Coletados
```sql
sqlite3 data/ziva.db "SELECT COUNT(*) FROM training_data WHERE quality_score > 0.8"
```

### Listar Adaptadores
```python
from core.adapter_manager import AdapterManager
manager = AdapterManager()
for adapter in manager.list_adapters():
    print(f"{adapter['id']}: {adapter['version']}")
```

### Status P2P
```python
from core.p2p_learning import GabrielleConnector
g = GabrielleConnector()
print(f"Gabrielle: {'Online' if g.is_connected else 'Offline'}")
```

## 🐛 Troubleshooting

### GPU Out of Memory
- Reduzir `per_device_train_batch_size` em `ZivaTrainingConfig`
- Aumentar `gradient_accumulation_steps`
- Usar QLoRA (4-bit) em vez de LoRA

### Gabrielle Não Conecta
```bash
# Verificar Tailscale
ping falcon

# Verificar porta
curl http://falcon:9000/health

# Iniciar Ziva em falcon
ssh falcon "cd /home/holloway/ziva && bash start.sh"
```

### Dataset Vazio
- Verificar se há sessões no banco: `SELECT COUNT(*) FROM interactions`
- Reduzir `min_quality` para 0.6
- Executar mais interações com Ziva primeiro

## 📖 Documentação Completa
- **Walkthrough**: `.gemini/antigravity/brain/.../walkthrough.md`
- **Implementation Plan**: `.gemini/antigravity/brain/.../implementation_plan.md`
- **LLM Optimization**: `docs/LLM_OPTIMIZATION_DEEP_ANALYSIS.md`
