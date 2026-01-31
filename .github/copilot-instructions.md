# Ziva: Autonomous Agent System - AI Development Guide

## Architecture Overview

**Ziva** (Node 07) is a distributed autonomous agent system with multi-node orchestration, vector-based knowledge management (RAG), and a dynamic tool/extension ecosystem.

### Core Components

1. **ZivaAgent** (`agent/ziva.py`): Central orchestrator managing decision-making, job execution, and knowledge coordination
2. **JobDispatcher** (`core/dispatcher.py`): Routes jobs locally to Ziva or remotely to worker nodes (e.g., Gabrielle/Node 08) via Outbox/Inbox pattern
3. **VectorStore** (`core/vector_store.py`): Qdrant-based semantic search for RAG using 768-dim embeddings (nomic-embed-text)
4. **ToolManager** (`agent/tools.py`): Dynamic extension loader from `extensions/` directory using `@ziva_tool` decorator
5. **LLMService** (`core/llm.py`): Wrapper around Ollama API (default: qwen2.5-coder:7b)
6. **SelfLearner** (`core/learning.py`): Auto-learning cycle that analyzes completed jobs, extracts insights, and updates vector memory

### Data Flow

- **Jobs**: Stored in SQLite (`data/ziva.db`), queued with status transitions (pending → assigned → processing → completed/failed)
- **P2P Messaging**: inbox/outbox filesystem pattern + TransferManager (SCP) for node-to-node communication
- **Knowledge**: Completed jobs trigger learning cycles that inject insights into Qdrant for future RAG queries
- **Networking**: Tailscale-based discovery and P2P coordination between distributed nodes

---

## Essential Patterns

### Adding Tools/Extensions

Tools are dynamically loaded Python functions in `extensions/`. Use the `@ziva_tool` decorator:

```python
# extensions/my_feature.py
from agent.tools import ziva_tool

@ziva_tool
def my_action(param: str) -> str:
    """Docstring describing the tool."""
    return f"Result: {param}"
```

Tools are auto-discovered and exposed via `ToolManager.load_tools()` at agent startup. No registration needed.

### Job Submission & Routing

**Via HTTP API:**
```python
# POST http://localhost:8000/jobs
{"type": "analysis", "payload": {"task": "..."}, "compact": false}
```

**Routing Logic:**
- Jobs with `"requirements": "heavy_computation"` → remote worker (Gabrielle)
- Default → local execution (Ziva)

Routing decision made in `JobDispatcher._decide_target()`, then dispatched to Outbox for remote jobs.

### Knowledge Management

**Ingesting Knowledge:**
```python
# In learning.py: analyze_job() uses LLM to extract insights
# Insights auto-persisted to VectorStore (Qdrant)
```

**RAG Queries:**
```python
# Vector similarity search for contextual retrieval
knowledge_store.search(query_embedding, limit=5)
```

---

## Developer Workflows

### Local Development

1. **Start Ziva Agent (core loop):**
   ```bash
   python -m agent.ziva
   ```

2. **Start API Server:**
   ```bash
   python -m api.server  # Runs on http://localhost:8000
   ```

3. **Check dependencies:**
   ```bash
   python -m core.validator  # Validates requirements.txt + Ollama/Tailscale connectivity
   ```

### Running Tests

Tests use unittest (no pytest dependency). Run specific test:
```bash
python -m unittest tests.test_remote.TestRemoteExecution
```

**Key test suites:**
- `tests/test_p2p.py`: P2P messaging and node discovery
- `tests/test_remote.py`: Remote command execution via SSH
- `tests/test_sync.py`: Knowledge synchronization between nodes

### Database Management

SQLite database at `/home/holloway/ziva/data/ziva.db`. **Critical PRAGMAs** in `DatabaseManager._get_conn()`:
- WAL journaling (concurrent reads/writes)
- 64MB cache + memory-mapped I/O for high throughput
- Incremental vacuum to prevent fragmentation

**Viewing schema:**
```bash
sqlite3 /home/holloway/ziva/data/ziva.db ".schema"
```

### Restarting Components

- **Full restart with memory recovery:**
  ```bash
  python scripts/restore_memory.py
  ```
- **Clear specific subsystems:**
  ```bash
  rm /home/holloway/ziva/data/ziva.db  # Clear job queue
  rm -rf /home/holloway/ziva/data/qdrant_storage_fixed/*  # Clear vector store
  ```

---

## Project-Specific Conventions

1. **File Paths**: Always absolute paths (`/home/holloway/ziva/...`). Config uses hardcoded base paths, not environment variables.

2. **Portuguese Comments**: Most docstrings are in Portuguese (original language). Maintain consistency.

3. **Async Patterns**: No async/await used—single-threaded job processing with polling/daemon loops (MessageDaemon, SelfLearner).

4. **Error Handling**: Graceful degradation; e.g., LLMService returns empty string if Ollama unavailable, job marked 'failed' but doesn't crash.

5. **Node Identifiers**: Fixed node IDs (e.g., `"node07"` for Ziva, `"node08"` for Gabrielle). Tailscale discovery populates remote node registry.

6. **Lazy Initialization**: ZivaAgent delays LLM service import until needed to speed up startup.

---

## Critical External Dependencies

- **Ollama** (`http://127.0.0.1:11434`): Required for LLM inference. Check health via `curl http://127.0.0.1:11434`.
- **Qdrant** (`/home/holloway/ziva/data/qdrant_storage_fixed`): Local vector DB. Initialized automatically.
- **Tailscale**: P2P network for node discovery. Agent warns if not connected.
- **SQLite** (bundled): Persists job queue and messages.

---

## Common Debugging Scenarios

### Agent Won't Start
Check:
1. `python -m core.validator` for missing dependencies
2. `ollama serve` running (separate terminal)
3. Tailscale status: `tailscale status`

### Job Stuck in "Pending"
- Verify `JobDispatcher.dispatch_pending_jobs()` is called in main loop
- Check Outbox files reach remote node: `ls /home/holloway/ziva/outbox/`
- Confirm Tailscale IP connectivity: `ping <gabrielle_tailscale_ip>`

### Vector Store Issues
- Qdrant metadata corruption? Rebuild: `rm -rf /home/holloway/ziva/data/qdrant_storage_fixed && python -c "from core.vector_store import VectorStore; VectorStore()"`

### Remote Command Execution Failing
- Verify SSH key trust: check `gabrielle_trust_key.txt` and remote `~/.ssh/authorized_keys`
- Test SSH directly: `ssh -i /path/to/key gabrielle@<tailscale_ip>`

---

## When Adding Features

- **New tool**: Add `@ziva_tool` function to `extensions/`, no restart needed if hot-reload planned
- **New job type**: Define in API request schema (`JobRequest.type`), add routing logic in `JobDispatcher._decide_target()`
- **New knowledge source**: Implement learning pipeline in `SelfLearner`, ensure embeddings use nomic-embed-text for dimension match (768)
- **Cross-node communication**: Use inbox/outbox pattern + `TransferManager` for reliability

---

## References

- **Main agent loop**: `agent/ziva.py:ZivaAgent.__init__()` and dispatcher polling
- **Tool discovery**: `agent/tools.py:ToolManager.load_tools()`
- **Job lifecycle**: `core/database.py:DatabaseManager` schema and `core/dispatcher.py` routing
- **RAG integration**: `core/learning.py:SelfLearner.run_cycle()` and `core/vector_store.py`
