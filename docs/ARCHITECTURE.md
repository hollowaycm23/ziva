# Ziva AI — Arquitetura do Sistema

## Visão Geral

Ziva é um agente IA generativo local, offline-first, com RAG híbrido, autonomia por ferramentas dinâmicas, governança explícita via LangGraph, e execução segura em GPU (≤12GB VRAM).

## Stack Tecnológica

| Componente | Tecnologia |
|---|---|
| LLM | Qwen2.5 7B / Qwen3 14B via Ollama (CUDA) |
| Embeddings | nomic-embed-text via Ollama |
| Vector DB | Qdrant (Docker) |
| RAG | Busca semântica + web search fallback (SearXNG) |
| Orquestrador | LangGraph |
| API | FastAPI (uvicorn) |
| Cache | LRU EmbeddingCache (512 entradas, 1h TTL) |

## Arquitetura em Camadas

```
┌─────────────────────────────────────────────────────────┐
│                     Interface                            │
│          FastAPI (port 8000) / CLI                       │
├─────────────────────────────────────────────────────────┤
│                  LangGraph Agent                         │
│  input → classify → analyze → (tool_exec) → respond     │
│  └─ cognitive nodes (summarization, learning, reflection)│
├─────────────────────────────────────────────────────────┤
│                    Tool System                           │
│  ToolValidator (AST) → ToolRegistry (JSON) → Runtime    │
│  Extensions (.py no extensions/) → DynamicTools         │
├─────────────────────────────────────────────────────────┤
│                      RAG Pipeline                       │
│  Qdrant → Kiwix → SearXNG → ResearchAugmenter           │
│  └─ Governance: TrustScorer + ContentDetector           │
├─────────────────────────────────────────────────────────┤
│                    LLM Layer                             │
│  Ollama (API) → ChatOpenAI (LangChain wrapper)          │
│  └─ EmbeddingCache (LRU)                                │
├─────────────────────────────────────────────────────────┤
│                   Infrastructure                         │
│  Docker: Qdrant, SearXNG, Kiwix, Browserless            │
│  Bare-metal: Ollama, Python venv                         │
└─────────────────────────────────────────────────────────┘
```

## Fluxo de Requisição

1. **input_node**: Recebe texto do usuário, inicializa estado
2. **contextualize_node**: Enriquece com contexto de sessão
3. **classify_node**: Classifica tarefa (greeting, web_search, code, etc.)
4. **analyze_node**: LLM analisa query com RAG context + ferramentas disponíveis
5. **router**: Decide próximo passo (tool_exec, respond, gate)
6. **execute_tool_node**: Executa ferramentas chamadas pelo LLM
7. **respond_node**: LLM gera resposta final com tool output + RAG context
8. **Background**: summarization + learning + metacognition (não bloqueante)

## Ferramentas Dinâmicas

- `create_tool(name, code, description)`: Valida com AST, registra em JSON
- `list_dynamic_tools()`: Lista ferramentas criadas pelo usuário
- `delete_tool(name)`: Remove ferramenta
- Limite: 30 ferramentas por usuário
- Contrato: `def tool_name(input: dict) -> dict:`

## Governança (Seção 9)

- **TrustScorer**: Score 0-100 (mínimo 70) baseado em fonte, autor, data, objetividade, estrutura técnica, consistência local
- **ContentDetector**: Detecta conteúdo gerado por IA (padrões + heurísticas)
- **GovernanceService**: Intercepta toda inserção via `VectorStore.add_text()`
- **Metadata**: Cada documento armazena `trust_score`, `source_domain`, `ingested_at`, `id`

## Observabilidade

- Logs estruturados JSON com `timestamp`, `level`, `logger`, `message`, `request_id`
- `@track_node`: Métricas por nó do LangGraph (count, avg, last)
- `/metrics`: CPU per-core, VRAM, node_metrics
- VRAM monitoring: nvidia-smi a cada 60s (warning >85%, critical >95%)

## Diretórios Principais

```
D:\Stark/
├── api/            # FastAPI server, routes
├── agent/          # ZivaAgent, ToolManager
├── core/           # Núcleo: LLM, VectorStore, Graph, DynamicTools, Governance
├── extensions/     # Ferramentas Ziva (.py auto-descobertas)
├── rag/            # RAG: ingestion, retrieval, trust_scorer
├── tests/          # Testes unitários e de integração
├── data/           # Dados persistentes (dynamic_tools.json)
├── docs/           # Documentação
└── scripts/        # Utilitários e scripts de diagnóstico
```
