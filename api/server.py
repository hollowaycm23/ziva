from typing import List
from core.sync_manager import SyncManager
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from core.autonomic import autonomic_system
from fastapi.middleware.cors import CORSMiddleware
from core.security import verify_api_key, verify_dashboard_access
from agent.ziva import ZivaAgent
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import sys
import os
import logging
import time
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from core.llm import LLMService

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Init Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ZivaAPI")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Ziva API Starting up...")
    autonomic_system.start()
    yield
    # Shutdown
    logger.info("🛑 Ziva API Shutting down...")
    autonomic_system.stop()


app = FastAPI(
    title="Ziva API",
    description="Interface HTTP para o Agente Autônomo Ziva",
    version="2.8",
    lifespan=lifespan
)

# Enable CORS for VS Code Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In development, allow all. Could be restricted.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton Agent (Lazy Load or Injected)
agent = None


def get_agent():
    global agent
    if agent is None:
        agent = ZivaAgent()
    return agent


class JobRequest(BaseModel):
    type: str
    payload: Dict[str, Any]
    compact: Optional[bool] = False


class MemoryQuery(BaseModel):
    query: str
    limit: Optional[int] = 5




@app.post("/jobs", dependencies=[Depends(verify_api_key)])
def submit_job(job: JobRequest):
    """Submits a new job to the agent's queue."""
    try:
        current_agent = get_agent()
        job_id = current_agent.db.add_job(job.type, job.payload)
        return {"status": "submitted", "job_id": job_id}
    except Exception as e:
        logger.error(f"Error submitting job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}")
def get_job_status(job_id: int):
    """Checks the status of a specific job."""
    current_agent = get_agent()
    conn = current_agent.db._get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        job = current_agent.db._row_to_job(row)
        return job
    raise HTTPException(status_code=404, detail="Job not found")


@app.post("/memory/search", dependencies=[Depends(verify_api_key)])
def search_memory(query: MemoryQuery):
    """Semantic search in Ziva's knowledge base."""
    current_agent = get_agent()
    
    # Initialize LLM/Embedder if not already set
    if not current_agent.llm:
        from core.config import config
        emb_config = config.get_llm_provider("agent.embedding_model")
        model_name = emb_config["model_name"] if emb_config else "text-embedding-qwen2.5-0.5b-instruct"
        current_agent.llm = LLMService(model=model_name)
    
    # Generate embedding using the default model configured in LLMService
    embedding = current_agent.llm.embedding(query.query)

    if not embedding:
        logger.error(f"Failed to generate embedding for query: {query.query}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate embedding")

    results = current_agent.knowledge.search(embedding, limit=query.limit)
    return {"results": results}


class ChatMessage(BaseModel):
    session_id: Optional[int] = None
    message: str
    images: Optional[list[str]] = None
    compact: Optional[bool] = True
    mode: Optional[str] = "standard"


# --- OpenAI Compatibility Layer ---
class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7


class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Dict[str, int]
# ----------------------------------


@app.post("/chat", dependencies=[Depends(verify_api_key)])
def chat(payload: ChatMessage):
    """Interactive chat with Ziva through the API."""
    try:
        current_agent = get_agent()
        conn = current_agent.db._get_conn()
        cursor = conn.cursor()

        session_id = payload.session_id
        if not session_id:
            cursor.execute(
                "INSERT INTO sessions (start_time) VALUES (?)", (time.time(),)
            )
            session_id = cursor.lastrowid
            conn.commit()

        if payload.images and len(payload.images) > 0:
            try:
                from core.vision import get_vision_handler
                vision = get_vision_handler()

                if not current_agent.llm:
                    current_agent.llm = LLMService(model="llava:7b")

                response = vision.process_image_query(
                    payload.message, payload.images, current_agent.llm
                )

                cursor.execute(
                    "INSERT INTO interactions (session_id, role, content, "
                    "timestamp) VALUES (?, ?, ?, ?)",
                    (session_id, "user", f"[IMAGE] {payload.message}",
                     time.time())
                )
                cursor.execute(
                    "INSERT INTO interactions (session_id, role, content, "
                    "timestamp) VALUES (?, ?, ?, ?)",
                    (session_id, "assistant", response, time.time())
                )
                conn.commit()

                return {
                    "response": response,
                    "session_id": session_id,
                    "task_type": "vision",
                    "model_used": "llava:7b",
                    "context_used": 0
                }
            except Exception as e:
                logger.error(f"Vision error: {e}")
                return {"error": f"Vision processing failed: {str(e)}"}

        cursor.execute(
            "INSERT INTO interactions (session_id, role, content, timestamp) "
            "VALUES (?, ?, ?, ?)",
            (session_id, "user", payload.message, time.time())
        )
        conn.commit()

        try:
            if payload.mode == "supervisor":
                from core.graph.supervisor import supervisor_app
                from langchain_core.messages import HumanMessage, AIMessage

                cursor.execute(
                    "SELECT role, content FROM interactions WHERE session_id = ? "
                    "ORDER BY timestamp DESC LIMIT 10", (session_id,))
                history_rows = cursor.fetchall()

                messages = []
                for row in reversed(history_rows):
                    role, content = row
                    if role == "user":
                        messages.append(HumanMessage(content=content))
                    elif role == "assistant":
                        messages.append(AIMessage(content=content))

                final_state = supervisor_app.invoke(
                    {"messages": messages}, config={"recursion_limit": 50}
                )

                last_network_msg = final_state["messages"][-1]
                response = last_network_msg.content
                tool_output = {}

                logger.info(
                    f"Supervisor execution complete. Response len: {len(response)}"
                )

            else:
                from core.graph.ziva_graph import app as graph_app

                cursor.execute(
                    "SELECT role, content FROM interactions WHERE session_id = ? "
                    "ORDER BY timestamp DESC LIMIT 5", (session_id,))
                history_rows = cursor.fetchall()
                conversation_history = "\n".join(
                    [f"{row[0].capitalize()}: {row[1]}"
                     for row in reversed(history_rows)]
                )

                full_input = (
                    f"History:\n{conversation_history}\n\nUser Request: "
                    f"{payload.message}" if conversation_history
                    else payload.message
                )

                initial_state = {"input": full_input}

                final_state = graph_app.invoke(
                    initial_state, config={"recursion_limit": 100}
                )

                response = final_state.get(
                    "response", "No response generated.")
                tool_output = final_state.get("tool_output", {})

                logger.info(
                    f"Graph execution complete. Response len: {len(response)}"
                )

        except ConnectionError:
            logger.exception("Graph connection error")
            response = "Erro de conexão temporário. Tente novamente."
            tool_output = {}
        except Exception as e:
            logger.exception("Graph execution error")
            response = f"I encountered an internal error: {e}"
            tool_output = {}

        cursor.execute(
            "INSERT INTO interactions (session_id, role, content, timestamp) "
            "VALUES (?, ?, ?, ?)",
            (session_id, "assistant", response, time.time())
        )

        if tool_output and not tool_output.get("error"):
            cursor.execute(
                "INSERT INTO interactions (session_id, role, content, "
                "timestamp) VALUES (?, ?, ?, ?)",
                (session_id, "system", f"Tool Output: {str(tool_output)}",
                 time.time())
            )

        conn.commit()

        return {
            "response": response,
            "session_id": session_id,
            "task_type": "graph_execution",
            "model_used": "qwen2.5-coder:7b",
            "context_used": 1
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chat endpoint error")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/v1/openapi.json", include_in_schema=False)
async def get_openapi_v1():
    return app.openapi()


@app.get("/v1/models", dependencies=[Depends(verify_api_key)])
async def list_models():
    """List available models (OpenAI Compatible)."""
    import time
    return {
        "object": "list",
        "data": [
            {
                "id": "ziva-agent",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "ziva-local"
            }
        ]
    }


@app.get("/v1/health")
async def health_check():
    """Health check endpoint with service status (public, no auth)."""
    import socket
    import os
    
    def check_port(host, port, timeout=1):
        """Check if a port is open."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    # Check services
    services = {
        "lm_studio": {
            "status": "external",
            "host": "100.104.242.35",
            "port": 1234,
            "healthy": check_port("100.104.242.35", 1234, timeout=2)
        },
        "qdrant": {
            "status": "running" if check_port("ziva-qdrant", 6333) else "down",
            "host": "ziva-qdrant",
            "port": 6333,
            "healthy": check_port("ziva-qdrant", 6333)
        },
        "searxng": {
            "status": "running" if check_port("ziva-searxng", 8080) else "down",
            "host": "ziva-searxng",
            "port": 8080,
            "healthy": check_port("ziva-searxng", 8080)
        },
        "kiwix": {
            "status": "running" if check_port("ziva-kiwix", 8080) else "down",
            "host": "ziva-kiwix",
            "port": 8080,
            "healthy": check_port("ziva-kiwix", 8080)
        },
        "openwebui": {
            "status": "running" if check_port("ziva-openwebui", 8080) else "down", # OpenWebUI interno usa 8080
            "host": "ziva-openwebui",
            "port": 8080,
            "healthy": check_port("ziva-openwebui", 8080)
        },
        "message_daemon": {
            "status": "running",
            "inbox": len([f for f in os.listdir("/app/inbox") if f.endswith('.json')]) if os.path.exists("/app/inbox") else 0,
            "outbox": len([f for f in os.listdir("/app/outbox") if f.endswith('.json')]) if os.path.exists("/app/outbox") else 0,
            "healthy": True
        }
    }
    
    # Overall health
    all_healthy = all(s.get("healthy", False) for s in services.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": services,
        "timestamp": int(time.time())
    }


@app.post("/v1/chat/completions")
async def openai_chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible endpoint for Ziva Agent."""
    import uuid
    import time
    from core.graph.ziva_graph import app as graph_app
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

    # 1. Convert Messages to Ziva Input
    # Simple strategy: Concatenate history into a string prompt for the graph
    # OR if graph supports 'messages' list input (checked: analyze_router uses messages), we pass list.
    
    # We need to construct a "full inputs" dictionary for the graph
    # The 'analyze_node' expects state["input"] or state["messages"]
    
    # Reconstruct history
    langchain_messages = []
    
    # Check for system prompt override
    system_prompt = "You are Ziva." 
    
    for msg in request.messages:
        if msg.role == "system":
            system_prompt = msg.content
            # We don't append system message to history if graph doesn't support it well, 
            # but usually AnalyzeNode has its own system prompt. 
            # If we pass 'input', the graph handles it.
            
        elif msg.role == "user":
            langchain_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            langchain_messages.append(AIMessage(content=msg.content))
            
    # Extract the last user message as the primary input
    last_user_input = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            last_user_input = msg.content
            break
            
    # If using pure graph invocation
    if not last_user_input:
         raise HTTPException(status_code=400, detail="No user message found")

    # Construct Input for Graph
    # We pass 'messages' to allow the graph to see history
    graph_input = {
        "messages": langchain_messages,
        "input": last_user_input # Redundant but safe for legacy nodes
    }
    
    try:
        # Execute Graph
        # Note: Non-streaming for now to ensure stability with tools
        final_state = await graph_app.ainvoke(graph_input, config={"recursion_limit": 50})
        
        # Extract Response
        # The final answer is usually the last AIMessage in 'messages' or 'response' key
        
        final_response_text = ""
        if "response" in final_state and final_state["response"]:
             final_response_text = final_state["response"]
        elif "messages" in final_state and final_state["messages"]:
             last_msg = final_state["messages"][-1]
             final_response_text = last_msg.content
        else:
             final_response_text = "No response generated."

        # Construct OpenAI Response
        resp_id = f"chatcmpl-{uuid.uuid4()}"
        
        choice = Choice(
            index=0,
            message=Message(role="assistant", content=final_response_text),
            finish_reason="stop"
        )
        
        return ChatCompletionResponse(
            id=resp_id,
            created=int(time.time()),
            model=request.model,
            choices=[choice],
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0} # Placeholder
        )

    except Exception as e:
        logger.exception("OpenAI Adapter Error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats", dependencies=[Depends(verify_dashboard_access)])
def get_stats():
    """Returns system stats for the dashboard."""
    import psutil
    import shutil

    total, used, free = shutil.disk_usage("/")

    return {
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
        "disk": (used / total) * 100,
        "models_loaded": ["ziva-base"]
    }


@app.get("/api/memory", dependencies=[Depends(verify_dashboard_access)])
def get_memory(limit: int = 10):
    return {
        "items": [
            {"id": 1, "text": "Ziva System Architecture...", "score": 0.95,
             "type": "doc"},
            {"id": 2, "text": "Python Optimization Strategies...",
             "score": 0.88, "type": "code"},
            {"id": 3, "text": "Task Classification Logic...", "score": 0.76,
             "type": "doc"}
        ]
    }


try:
    app.mount("/static", StaticFiles(directory="api/static"), name="static")
except Exception:
    pass


@app.get("/", response_class=HTMLResponse,
         dependencies=[Depends(verify_dashboard_access)])
async def read_root_ui():
    index_path = os.path.join(os.path.dirname(__file__),
                              "templates", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return f.read()
    return "<h1>Ziva API is Online</h1><p>Dashboard files not found.</p>"


class KnowledgePayload(BaseModel):
    source_node: str
    dataset: list
    timestamp: float


@app.post("/api/p2p/receive_knowledge")
def receive_knowledge(payload: KnowledgePayload):
    """endpoint to receive knowledge from peers."""
    try:
        current_agent = get_agent()
        if not hasattr(current_agent, 'p2p_node'):
            from core.p2p_learning import P2PLearningNode
            current_agent.p2p_node = P2PLearningNode(node_name="node_07")

        count = current_agent.p2p_node.receive_knowledge(
            payload.source_node, payload.dataset
        )
        return {"status": "success", "added_examples": count}
    except Exception as e:
        logger.error(f"P2P Receive Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/p2p/get_knowledge")
def get_knowledge(min_quality: float = 0.8):
    """endpoint to share knowledge with peers."""
    try:
        current_agent = get_agent()
        if not hasattr(current_agent, 'p2p_node'):
            from core.p2p_learning import P2PLearningNode
            current_agent.p2p_node = P2PLearningNode(node_name="node_07")

        dataset = current_agent.p2p_node.collector.get_training_dataset(
            min_quality=min_quality
        )
        return {
            "node_name": current_agent.p2p_node.node_name,
            "dataset": dataset}
    except Exception as e:
        logger.error(f"P2P Share Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class RAGBatchPayload(BaseModel):
    source_node: str
    points: List[Dict[str, Any]]  # List of points (vectors + payloads)
    collection_name: Optional[str] = "main_knowledge"


@app.post("/api/p2p/receive_rag_batch")
def receive_rag_batch(payload: RAGBatchPayload):
    """Endpoint to receive RAG vectors/documents from peers."""
    try:
        current_agent = get_agent()
        # Initialize RAG Helper if needed
        if not hasattr(current_agent, 'rag'):
            from core.rag_helper import get_rag_helper
            current_agent.rag = get_rag_helper()
            
        count = 0
        from qdrant_client.http.models import PointStruct
        
        points_to_upsert = []
        for point in payload.points:
             # Reconstruct PointStruct
             # Note: Vectors might be quantized or raw lists
             points_to_upsert.append(
                 PointStruct(
                     id=point.get("id"),
                     vector=point.get("vector"),
                     payload=point.get("payload")
                 )
             )
             count += 1
             
        if points_to_upsert:
             current_agent.rag.vector_store.client.upsert(
                 collection_name=payload.collection_name,
                 points=points_to_upsert
             )
             
        logger.info(f"✅ Received RAG Batch from {payload.source_node}: {count} points")
        return {"status": "success", "received": count}
        
    except Exception as e:
        logger.error(f"P2P RAG Receive Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/vitals", dependencies=[Depends(verify_dashboard_access)])
def get_system_vitals():
    """Returns detailed ECLSS Health Report from Overseer."""
    try:
        from core.overseer import Overseer
        overseer = Overseer()
        report = overseer.analyze_telemetry(last_n_lines=100)
        return {
            "status": report.status,
            "vitals": report.vitals,
            "tool_performance": {
                "success_rates": report.tool_success_rate,
                "avg_latencies": report.avg_latency_ms
            },
            "recent_errors": report.critical_errors
        }
    except Exception as e:
        logger.error(f"Error getting vitals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
def get_metrics():
    """Returns real-time system metrics for the dashboard."""
    import psutil
    import subprocess

    metrics = {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "gpu": None,
        "gpu_temp": None,
        "services": {
            "api": "Online",
            "ollama": "Check..."
        }
    }

    try:
        gpu_stats = subprocess.check_output(
            ["nvidia-smi",
             "--query-gpu=utilization.gpu,temperature.gpu",
             "--format=csv,noheader,nounits"],
            encoding="utf-8"
        ).strip().split(",")
        metrics["gpu"] = float(gpu_stats[0])
        metrics["gpu_temp"] = float(gpu_stats[1])
    except Exception:
        pass

    return metrics


@app.delete("/api/admin/clear_inbox", dependencies=[Depends(verify_api_key)])
def clear_inbox():
    """Limpa todas as mensagens pendentes na inbox."""
    try:
        inbox_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "inbox"
        )

        if not os.path.exists(inbox_dir):
            return {"status": "success",
                    "message": "Inbox directory does not exist", "deleted": 0}

        files = [f for f in os.listdir(inbox_dir) if f.endswith('.json')]
        count = len(files)

        for file in files:
            os.remove(os.path.join(inbox_dir, file))

        logger.info(f"Inbox cleared: {count} messages deleted")
        return {
            "status": "success",
            "message": "Inbox cleared successfully",
            "deleted": count
        }
    except Exception as e:
        logger.error(f"Error clearing inbox: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/admin/clear_outbox", dependencies=[Depends(verify_api_key)])
def clear_outbox():
    """Limpa todas as mensagens pendentes na outbox."""
    try:
        outbox_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "outbox"
        )

        if not os.path.exists(outbox_dir):
            return {"status": "success",
                    "message": "Outbox directory does not exist", "deleted": 0}

        files = [f for f in os.listdir(outbox_dir) if f.endswith('.json')]
        count = len(files)

        for file in files:
            os.remove(os.path.join(outbox_dir, file))

        logger.info(f"Outbox cleared: {count} messages deleted")
        return {
            "status": "success",
            "message": "Outbox cleared successfully",
            "deleted": count,
            "warning": "These insights will not be synced with Gabrielle"
        }
    except Exception as e:
        logger.error(f"Error clearing outbox: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/admin/clear_jobs", dependencies=[Depends(verify_api_key)])
def clear_jobs(status: Optional[str] = None):
    """
    Limpa jobs da fila.

    Args:
        status (optional): Filtro por status (pending, processing, completed,
                                            failed).
                          Se não especificado, limpa apenas 'completed' e
                          'failed'.
    """
    import sqlite3

    try:
        current_agent = get_agent()
        conn = current_agent.db._get_conn()
        cursor = conn.cursor()

        if status:
            valid_statuses = ['pending', 'processing', 'completed', 'failed']
            if status not in valid_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Must be one of: {valid_statuses}"
                )

            cursor.execute(
                "SELECT COUNT(*) FROM jobs WHERE status = ?", (status,))
            count = cursor.fetchone()[0]

            cursor.execute("DELETE FROM jobs WHERE status = ?", (status,))
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM jobs WHERE status IN ('completed', 'failed')"
            )
            count = cursor.fetchone()[0]

            cursor.execute(
                "DELETE FROM jobs WHERE status IN ('completed', 'failed')"
            )

        conn.commit()
        conn.close()

        logger.info(
            f"Jobs cleared: {count} jobs deleted (status: "
            f"{status or 'completed/failed'})")
        return {
            "status": "success",
            "message": "Jobs cleared successfully",
            "deleted": count,
            "filter": status or "completed, failed"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class RPCLLMRequest(BaseModel):
    prompt: str
    model: Optional[str] = "qwen2.5-coder:7b"
    temperature: Optional[float] = 0.7


@app.post("/api/rpc/llm", dependencies=[Depends(verify_api_key)])
def rpc_llm(request: RPCLLMRequest):
    """
    Remote LLM execution - Allows Gabrielle to execute LLM queries on Ziva.
    """
    try:
        current_agent = get_agent()

        if not current_agent.llm:
            current_agent.llm = LLMService(model=request.model)

        response = current_agent.llm.completion(
            request.prompt,
            temperature=request.temperature,
            model=request.model
        )

        logger.info(
            f"RPC_LLM executed: {request.prompt[:50]}... -> {len(response)} chars"
        )

        return {
            "status": "success",
            "response": response,
            "model": request.model,
            "prompt_length": len(request.prompt),
            "response_length": len(response)
        }
    except Exception as e:
        logger.error(f"RPC_LLM error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SearchLatentRequest(BaseModel):
    query: str
    limit: Optional[int] = 5


@app.post("/api/rpc/search_latent", dependencies=[Depends(verify_api_key)])
def rpc_search_latent(request: SearchLatentRequest):
    """
    Remote latent space search - Allows Gabrielle to search Ziva's RAG.
    """
    try:
        current_agent = get_agent()

        if not current_agent.llm:
            current_agent.llm = LLMService(model="nomic-embed-text")

        embedding = current_agent.llm.embedding(request.query)

        if not embedding:
            raise HTTPException(
                status_code=500, detail="Failed to generate embedding"
            )

        results = current_agent.knowledge.search(
            embedding, limit=request.limit)

        logger.info(
            f"SEARCH_LATENT executed: {request.query[:50]}... -> "
            f"{len(results)} results"
        )

        return {
            "status": "success",
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"SEARCH_LATENT error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/gabrielle/start_services",
          dependencies=[Depends(verify_api_key)])
def start_gabrielle_services():
    """
    Starts core services on Gabrielle (Ollama, SearxNG, Kiwix).
    """
    try:
        from network.gabrielle_mgr import GabrielleManager

        mgr = GabrielleManager(hostname="falcon")
        results = mgr.start_core_services()

        logger.info(f"Gabrielle services started: {results}")

        return {
            "status": "success",
            "message": "Services start commands sent",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error starting Gabrielle services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/gabrielle/health",
         dependencies=[Depends(verify_dashboard_access)])
def check_gabrielle_health():
    """
    Checks health status of Gabrielle services.
    """
    try:
        from network.gabrielle_mgr import GabrielleManager

        mgr = GabrielleManager(hostname="falcon")
        health = mgr.check_health()

        logger.info(f"Gabrielle health check: {health}")

        return {
            "status": "success",
            "health": health,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error checking Gabrielle health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class GabrielleCommandRequest(BaseModel):
    command: str


@app.post("/api/admin/gabrielle/command",
          dependencies=[Depends(verify_api_key)])
def send_gabrielle_command(request: GabrielleCommandRequest):
    """
    Sends a raw command to Gabrielle via SSH.
    """
    try:
        from network.gabrielle_mgr import GabrielleManager

        mgr = GabrielleManager(hostname="falcon")
        result = mgr.send_raw_command(request.command)

        logger.info(f"Command sent to Gabrielle: {request.command}")

        return {
            "status": "success",
            "command": request.command,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error sending command to Gabrielle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class MultiAgentRequest(BaseModel):
    """Request model for multi-agent task delegation."""
    task: str
    preferred_role: Optional[str] = None
    use_multi_agent: bool = True


class AgentSpawnRequest(BaseModel):
    """Request model for spawning a new agent."""
    role: str
    agent_id: Optional[str] = None


@app.post("/api/v1/multi_agent/task", dependencies=[Depends(verify_api_key)])
def delegate_multi_agent_task(request: MultiAgentRequest):
    """
    Delegate a task to the multi-agent system.

    Args:
        request: Task delegation request with task description and optional
                 role preference

    Returns:
        dict: Task delegation result with assigned agent info

    Raises:
        HTTPException: If multi-agent system is not initialized or
                       delegation fails
    """
    try:
        current_agent = get_agent()

        if not hasattr(current_agent, 'agent_manager') or \
           current_agent.agent_manager is None:
            from core.multi_agent_init import initialize_multi_agent_system
            current_agent.agent_manager = initialize_multi_agent_system()
            logger.info("Multi-agent system initialized")

        task_data = {
            "type": "user_task",
            "description": request.task,
            "input": request.task
        }

        agent_id = current_agent.agent_manager.delegate_task(
            task_data,
            preferred_role=request.preferred_role
        )

        if not agent_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to delegate task")

        return {
            "status": "success",
            "message": "Task delegated successfully",
            "agent_id": agent_id,
            "agent_role":
                current_agent.agent_manager.active_agents[agent_id].role
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multi-agent task delegation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/agents/spawn", dependencies=[Depends(verify_api_key)])
def spawn_agent(request: AgentSpawnRequest):
    """
    Spawn a new specialized agent.

    Args:
        request: Agent spawn request with role and optional ID

    Returns:
        dict: Spawned agent information

    Raises:
        HTTPException: If agent spawning fails or resources unavailable
    """
    try:
        current_agent = get_agent()

        if not hasattr(current_agent, 'agent_manager') or \
           current_agent.agent_manager is None:
            from core.multi_agent_init import initialize_multi_agent_system
            current_agent.agent_manager = initialize_multi_agent_system()

        agent_id = current_agent.agent_manager.spawn_agent(
            role=request.role,
            agent_id=request.agent_id
        )

        if not agent_id:
            raise HTTPException(
                status_code=503,
                detail="Cannot spawn agent: resource constraints"
            )

        agent_status = current_agent.agent_manager.get_agent_status(agent_id)

        return {
            "status": "success",
            "message": f"Agent {agent_id} spawned successfully",
            "agent": agent_status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent spawn error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/agents/status")
def get_agents_status():
    """
    Get status of all active agents and resource usage.

    Returns:
        dict: Comprehensive agent and resource status
    """
    try:
        current_agent = get_agent()

        if not hasattr(current_agent, 'agent_manager') or \
           current_agent.agent_manager is None:
            return {
                "multi_agent_enabled": False,
                "message": "Multi-agent system not initialized"
            }

        agents = current_agent.agent_manager.list_agents()
        resources = current_agent.agent_manager.get_resource_usage()

        return {
            "multi_agent_enabled": True,
            "active_agents": len(agents),
            "max_agents": current_agent.agent_manager.max_concurrent_agents,
            "agents": agents,
            "resources": resources
        }

    except Exception as e:
        logger.error(f"Get agents status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/agents/{agent_id}",
            dependencies=[Depends(verify_api_key)])
def terminate_agent(agent_id: str):
    """
    Terminate a specific agent.

    Args:
        agent_id: ID of agent to terminate

    Returns:
        dict: Termination confirmation

    Raises:
        HTTPException: If agent not found or termination fails
    """
    try:
        current_agent = get_agent()

        if not hasattr(current_agent, 'agent_manager') or \
           current_agent.agent_manager is None:
            raise HTTPException(
                status_code=400,
                detail="Multi-agent system not initialized"
            )

        if agent_id not in current_agent.agent_manager.active_agents:
            raise HTTPException(
                status_code=404, detail=f"Agent {agent_id} not found"
            )

        current_agent.agent_manager.terminate_agent(agent_id)

        return {
            "status": "success",
            "message": f"Agent {agent_id} terminated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent termination error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/resources")
def get_resource_usage():
    """
    Get current hardware resource usage.

    Returns:
        dict: RAM, VRAM, CPU usage and availability
    """
    try:
        from core.resource_monitor import get_monitor
        monitor = get_monitor()

        return {
            "status": "success",
            "resources": monitor.get_summary()
        }

    except Exception as e:
        logger.error(f"Get resources error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


sync_manager = SyncManager(qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"))


class MarkSyncedRequest(BaseModel):
    point_ids: List[str]


@app.get("/sync/pending")
async def get_pending_sync(limit: int = 100):
    """
    Retorna documentos pendentes de sincronização.
    Gabrielle chama este endpoint para buscar novos documentos.
    """
    try:
        docs = sync_manager.get_pending_sync(limit=limit)
        return {
            "status": "success",
            "count": len(docs),
            "documents": docs
        }
    except Exception as e:
        logger.error(f"Get pending sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sync/mark_synced")
async def mark_synced(request: MarkSyncedRequest):
    """
    Marca documentos como sincronizados.
    Gabrielle chama após sync bem-sucedido.
    """
    try:
        sync_manager.mark_as_synced(request.point_ids)
        return {
            "status": "success",
            "count": len(request.point_ids)
        }
    except Exception as e:
        logger.error(f"Mark synced error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sync/cleanup")
async def cleanup_staging():
    """
    Remove documentos já sincronizados do staging.
    """
    try:
        count = sync_manager.clear_synced_staging()
        return {
            "status": "success",
            "removed": count
        }
    except Exception as e:
        logger.error(f"Cleanup staging error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sync/stats")
async def get_sync_stats():
    """
    Estatísticas de sincronização.
    """
    try:
        stats = sync_manager.get_stats()
        return {
            "status": "success",
            **stats
        }
    except Exception as e:
        logger.error(f"Get sync stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
class MessageReceivePayload(BaseModel):
    id: str
    from_agent: str
    to_agent: str
    type: str
    subject: Optional[str] = ""
    content: str
    metadata: Optional[Dict[str, Any]] = {}
    created_at: str
    status: str

@app.post("/messages/receive")
@app.post("/v1/messages/receive")
def receive_message_from_peer(msg: MessageReceivePayload):
    try:
        current_agent = get_agent()
        current_agent.db.add_message(
            msg.id, 
            "inbox", 
            msg.from_agent, 
            msg.to_agent, 
            msg.content, 
            msg.created_at
        )
        return {"status": "received", "message_id": msg.id}
    except Exception as e:
        logger.error(f"Error receiving message: {e}")
        raise HTTPException(status_code=500, detail=str(e))
