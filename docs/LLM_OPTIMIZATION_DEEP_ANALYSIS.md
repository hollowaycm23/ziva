# Otimização de LLM: Análise Profunda para Ziva
## 4 Pilares: Prompt Engineering, RAG, Fine-Tuning e Otimização de Inferência

## 1. Engenharia de Prompt (Prompt Engineering)

### Técnicas Principais

#### 1.1 Clareza e Especificidade
- **Instruções diretas**: Usar verbos de ação ("Generate", "Summarize", "Extract")
- **Evitar ambiguidade**: Ser específico sobre formato e conteúdo desejado
- **Separar instruções de contexto**: Usar delimitadores (`###`, `"""`)

#### 1.2 Chain-of-Thought (CoT)
```
Prompt: "Resolva este problema passo a passo:
1. Identifique os dados fornecidos
2. Determine o que precisa ser calculado
3. Execute os cálculos
4. Verifique o resultado

Problema: [...]"
```

**Variações**:
- **Zero-shot CoT**: "Let's think step by step"
- **Few-shot CoT**: Fornecer exemplos de raciocínio

#### 1.3 Tree-of-Thoughts (ToT)
- Explora múltiplos caminhos de solução
- Útil para planejamento complexo
- Permite backtracking e refinamento

#### 1.4 Role-Playing
```
"Você é um engenheiro de software sênior especializado em Python.
Analise este código e sugira melhorias..."
```

#### 1.5 Few-Shot Learning
```
Exemplo 1:
Input: "Extraia o nome do produto"
Output: {"product": "iPhone 15"}

Exemplo 2:
Input: "Extraia o nome do produto"
Output: {"product": "MacBook Pro"}

Agora extraia: [novo input]
```

### Aplicação no Ziva

**Status Atual**:
- ✅ Perfil de sistema (`perfil.txt`)
- ✅ Assinaturas de funções incluídas
- ✅ Exemplos de uso de ferramentas
- ⚠️ Sem CoT explícito
- ⚠️ Sem few-shot sistemático

**Melhorias Propostas**:
1. **Adicionar CoT ao perfil**:
```python
# perfil.txt
"Ao resolver problemas complexos:
1. Decomponha em etapas menores
2. Execute cada etapa sequencialmente
3. Verifique resultados intermediários
4. Combine para resposta final"
```

2. **Few-Shot para ferramentas**:
```python
# Adicionar exemplos reais de uso bem-sucedido
TOOL_EXAMPLES = {
    "web_search": [
        {"query": "Python tutorials", "result": "..."},
        {"query": "Latest AI news", "result": "..."}
    ]
}
```

3. **Meta-prompting**:
- Usar LLM para gerar prompts otimizados
- Testar e refinar automaticamente

---

## 2. RAG (Retrieval-Augmented Generation)

### Arquiteturas RAG

#### 2.1 Basic RAG (Pipeline)
```
User Query → Embedding → Vector Search → Context + Query → LLM → Response
```

#### 2.2 Advanced RAG
- **Reranking**: Reordena resultados por relevância
- **Hybrid Search**: Dense (semântico) + Sparse (keywords)
- **Query Expansion**: Reformula query para melhor retrieval

#### 2.3 Agentic RAG
- LLM decide quando e como buscar informação
- Multi-hop reasoning
- Iterative refinement

#### 2.4 Self-RAG
- Modelo gera queries de retrieval autonomamente
- Refina busca durante geração

### Componentes Técnicos

**Chunking**:
```python
# Estratégias
- Fixed-size: 500-1000 caracteres
- Semantic: Por parágrafo/seção
- Overlapping: 10-20% overlap entre chunks
```

**Embeddings**:
```python
# Modelos recomendados
- nomic-embed-text (Ollama) - 768 dims
- all-MiniLM-L6-v2 - 384 dims
- text-embedding-ada-002 (OpenAI) - 1536 dims
```

**Vector Stores**:
- Qdrant (atual do Ziva)
- Chroma
- Pinecone
- Weaviate

### Aplicação no Ziva

**Status Atual**:
- ✅ Qdrant vector store
- ✅ Basic RAG implementado
- ✅ Knowledge base (SQLite)
- ⚠️ Sem reranking
- ⚠️ Sem hybrid search
- ⚠️ Chunking simples

**Melhorias Propostas**:

1. **Implementar Hybrid Search**:
```python
# extensions/rag_hybrid.py
def hybrid_search(query: str, top_k: int = 5):
    # Dense retrieval (semântico)
    dense_results = vector_store.search(query, limit=top_k*2)
    
    # Sparse retrieval (BM25)
    sparse_results = bm25_search(query, limit=top_k*2)
    
    # Combine e rerank
    combined = rerank(dense_results + sparse_results, query)
    return combined[:top_k]
```

2. **Reranker com Cross-Encoder**:
```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank(results, query):
    pairs = [[query, r.text] for r in results]
    scores = reranker.predict(pairs)
    return sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
```

3. **Adaptive RAG**:
```python
def adaptive_rag(query: str):
    # Classificar complexidade da query
    complexity = classify_query_complexity(query)
    
    if complexity == "simple":
        return basic_rag(query, top_k=3)
    elif complexity == "medium":
        return hybrid_rag(query, top_k=5)
    else:  # complex
        return agentic_rag(query, max_hops=3)
```

4. **Query Caching**:
```python
# core/rag_cache.py
import hashlib
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_search(query_hash: str):
    return vector_store.search(query)
```

---

## 3. Fine-Tuning (LoRA/QLoRA/PEFT)

### Métodos PEFT

#### 3.1 LoRA (Low-Rank Adaptation)
- Adiciona matrizes de baixo rank às camadas
- Congela pesos originais
- Treina apenas adaptadores pequenos

**Vantagens**:
- 10-100x menos parâmetros treináveis
- Múltiplos adaptadores para diferentes tarefas
- Troca rápida entre tarefas

**Exemplo**:
```python
from peft import LoraConfig, get_peft_model

config = LoraConfig(
    r=8,  # rank
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.1
)

model = get_peft_model(base_model, config)
# Apenas ~0.1% dos parâmetros são treináveis
```

#### 3.2 QLoRA (Quantized LoRA)
- LoRA + Quantização 4-bit
- Modelo base em 4-bit NF4
- Adaptadores em 16-bit

**Vantagens**:
- 4x redução de memória vs LoRA
- Fine-tune de 70B em GPU de 24GB
- Performance comparável a full fine-tuning

**Exemplo**:
```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16
)

model = AutoModelForCausalLM.from_pretrained(
    "model_name",
    quantization_config=bnb_config
)
```

### Aplicação no Ziva

**Status Atual**:
- ✅ Usa Ollama (modelos pré-treinados)
- ❌ Sem fine-tuning customizado
- ❌ Sem adaptadores específicos

**Melhorias Propostas**:

1. **Fine-Tune para Domínio Ziva**:
```python
# Dataset de treinamento
training_data = [
    {
        "instruction": "Execute comando bash",
        "input": "liste arquivos do diretório",
        "output": '{"tool": "local_shell", "args": {"command": "ls -la"}}'
    },
    # ... mais exemplos
]
```

2. **Criar Adaptadores por Tarefa**:
```
ziva-base-model/
├── adapters/
│   ├── code-execution/  # Para executar código
│   ├── web-scraping/    # Para scraping
│   ├── data-analysis/   # Para análise
│   └── conversation/    # Para chat
```

3. **Pipeline de Fine-Tuning**:
```python
# scripts/finetune_ziva.py
def finetune_adapter(task_name: str, dataset_path: str):
    # Carregar modelo base
    base_model = load_ollama_model("qwen2.5-coder:7b")
    
    # Configurar LoRA
    lora_config = LoraConfig(r=16, lora_alpha=32)
    
    # Treinar
    trainer = SFTTrainer(
        model=base_model,
        train_dataset=dataset,
        peft_config=lora_config
    )
    trainer.train()
    
    # Salvar adaptador
    trainer.save_model(f"adapters/{task_name}")
```

---

## 4. Otimização de Inferência e Arquitetura

### 4.1 Quantização

**Tipos**:
- **INT8**: 2x redução, mínima perda
- **INT4**: 4x redução, pequena perda
- **FP8**: Balanceado

**Métodos**:
- **PTQ (Post-Training)**: Sem retreinamento
- **QAT (Quantization-Aware)**: Com retreinamento
- **AWQ**: Protege pesos críticos

**Aplicação no Ziva**:
```python
# Usar modelos quantizados do Ollama
ollama pull qwen2.5-coder:7b-q4_K_M  # 4-bit
ollama pull qwen2.5-coder:7b-q8_0    # 8-bit
```

### 4.2 KV Cache Optimization

**Problema**: Cache cresce linearmente com sequência
**Solução**:
- Quantizar KV cache (FP8)
- Limitar tamanho máximo
- Eviction policies (LRU)

```python
# Configuração Ollama
{
    "num_ctx": 4096,  # Contexto máximo
    "num_gpu": 1,
    "num_thread": 8
}
```

### 4.3 Batching Dinâmico

**Continuous Batching**:
- Agrupa requests dinamicamente
- Maximiza GPU utilization
- Reduz latência média

**Implementação**:
```python
# core/batch_processor.py
class DynamicBatcher:
    def __init__(self, max_batch_size=32):
        self.queue = []
        self.max_batch = max_batch_size
    
    async def process(self):
        while True:
            batch = self.queue[:self.max_batch]
            if batch:
                results = await llm.generate_batch(batch)
                # Distribuir resultados
```

### 4.4 Speculative Decoding

**Conceito**: Modelo pequeno gera tokens, modelo grande valida

```python
def speculative_decode(prompt):
    # Draft model (rápido)
    draft_tokens = small_model.generate(prompt, n=5)
    
    # Verify with main model
    verified = large_model.verify(draft_tokens)
    
    return verified
```

### 4.5 Arquitetura - Multi-Query Attention (MQA)

**Benefício**: Reduz KV cache em 8-10x

```python
# Usar modelos com MQA/GQA
- Falcon (MQA)
- Llama 2 (GQA)
- Mistral (GQA)
```

---

## Plano de Implementação para Ziva

### Prioridade Alta (Curto Prazo)

1. **Melhorar Prompt Engineering**
   - [ ] Adicionar CoT ao perfil
   - [ ] Implementar few-shot examples
   - [ ] Criar biblioteca de prompts testados

2. **Otimizar RAG**
   - [ ] Implementar reranking
   - [ ] Adicionar hybrid search
   - [ ] Query caching

3. **Otimizar Inferência**
   - [ ] Usar modelos quantizados (Q4/Q8)
   - [ ] Configurar KV cache limits
   - [ ] Implementar batching

### Prioridade Média (Médio Prazo)

4. **Fine-Tuning**
   - [ ] Coletar dataset de interações Ziva
   - [ ] Treinar adaptador LoRA para domínio
   - [ ] Criar adaptadores por tarefa

5. **RAG Avançado**
   - [ ] Implementar Adaptive RAG
   - [ ] Self-RAG para queries complexas
   - [ ] Multi-hop reasoning

### Prioridade Baixa (Longo Prazo)

6. **Arquitetura**
   - [ ] Avaliar modelos com MQA/GQA
   - [ ] Speculative decoding
   - [ ] Mixture of Experts (MoE)

---

## Métricas de Sucesso

**Performance**:
- Latência < 2s para respostas simples
- Throughput > 10 req/s
- Uso de memória < 8GB

**Qualidade**:
- Accuracy de ferramentas > 95%
- Relevância RAG > 90%
- Redução de hallucinations > 80%

**Eficiência**:
- Custo de inferência -50%
- Tempo de resposta -30%
- Uso de GPU -40%
