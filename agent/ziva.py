import time
import os
from datetime import datetime
import json
import logging
from pathlib import Path
from core.database import DatabaseManager
from core.vector_store import VectorStore
from core.conversation_context import ConversationContext
from core.backup_system import backup_system

# from core.llm import LLMService # Delay import to allow setup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Ziva")


class ZivaAgent:
    """
    Agente Autônomo Ziva (Nó 07).

    Centraliza a lógica de tomara de decisão, execução de jobs e
    gerenciamento de conhecimento (RAG).
    """

    def __init__(self, profile_path=None,
                 compact_profile_path=None):
        profile_path = profile_path or os.getenv("ZIVA_PROFILE_PATH", "/app/perfil.txt")
        compact_profile_path = compact_profile_path or os.getenv("ZIVA_COMPACT_PROFILE_PATH", "/app/perfil_compact.txt")
        """
        Inicializa o agente carregando perfil e subsistemas.

        Args:
            profile_path (str): Caminho para o perfil completo.
            compact_profile_path (str): Caminho para o perfil compacto.
        """
        self.profile = self._load_profile(profile_path)
        self.profile_compact = self._load_profile(compact_profile_path)
        self.db = DatabaseManager()
        self.knowledge = VectorStore()
        self.llm = None  # Lazy load
        self.tools = {}
        self.p2p_node = None  # Init placeholder
        self.gabrielle = None  # Init placeholder

        # Contextos de conversação por sessão
        self.conversation_contexts = {}

        # Subsistema de Orquestração
        from core.dispatcher import JobDispatcher
        self.dispatcher = JobDispatcher()

        # Subsistema de Auto-Aprendizado
        from core.learning import SelfLearner
        self.learner = SelfLearner(knowledge_client=self.knowledge)

        # Subsistema de Ferramentas (Agência)
        from agent.tools import ToolManager
        self.tool_manager = ToolManager()
        self.tool_manager.load_tools()
        self.tools = self.tool_manager.loaded_tools

        # Validação de Sistema (Startup Check)
        from core.validator import SystemValidator
        req_path = os.getenv("ZIVA_REQUIREMENTS_PATH", "/app/requirements.txt")
        missing_deps = SystemValidator.check_dependencies(req_path)
        if missing_deps:
            logger.critical(
                f"Dependências ausentes/conflitantes: {missing_deps}")
        else:
            logger.info("Validação de dependências: OK.")

        # Check Ollama (Skipped for LM Studio Migration)
        # logger.info("Verificando Ollama...")


        # Check Tailscale
        from core.tailscale import TailscaleManager
        if not TailscaleManager.ensure_connected():
            logger.warning(
                "Tailscale não conectado. Recursos P2P podem falhar."
            )
        else:
            logger.info("Rede Tailscale: OK.")

        # Discovery Inicial
        logger.info("Executando discovery de rede (Tailscale)...")
        self.dispatcher.registry.scan_tailscale_network()

        # Recuperação de Dados Pós-Crash
        self.db.recover_stale_sessions()

        # P2P System (Initialized on Startup)
        try:
            from core.p2p_learning import P2PLearningNode, GabrielleConnector
            self.p2p_node = P2PLearningNode(node_name="node_07")
            self.gabrielle = GabrielleConnector()  # Direct binary link
        except Exception as e:
            logging.warning(f"Failed to init P2P: {e}")
            self.p2p_node = None
            self.gabrielle = None

        # Start Backup System
        backup_system.start(interval_seconds=300)  # 5 minutes

        logger.info("Agente Ziva inicializado.")

    # ... (omit methods) ...

    def _load_profile(self, path):
        """
        Lê o arquivo de perfil do disco.
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Perfil não encontrado em {path}.")
            return "Você é Ziva, uma IA assistente."

    def run_loop(self):
        """Main Agent Loop - Processes jobs, events, and P2P signals."""
        logger.info("🚀 Ziva Main Loop Started. Waiting for jobs...")

        import signal
        self._running = True

        def _handle_stop(signum, frame):
            logger.info("Shutdown signal received, stopping main loop...")
            self._running = False

        signal.signal(signal.SIGTERM, _handle_stop)
        signal.signal(signal.SIGINT, _handle_stop)

        while self._running:
            try:
                # 1. P2P Sync Check (Opportunistic)
                if self.p2p_node and int(
                        time.time()) % 300 == 0:  # Every 5 mins
                    try:
                        self.p2p_node.sync_with_peers()
                    except Exception:
                        pass

                # 2. Self-Learning Check (Periodic: Every 1 hour)
                if int(time.time()) % 3600 == 0:
                    try:
                        logger.info("Executing periodic self-learning cycle...")
                        new_knowledge = self.learner.run_cycle()
                        if new_knowledge:
                            logger.info(f"Auto-learned {len(new_knowledge)} new insights!")
                            self.broadcast_knowledge(new_knowledge)
                    except Exception as e:
                        logger.error(f"Error in self-learning cycle: {e}")

                # 2. Check for Jobs in Queue
                job = self.dispatcher.get_next_job()

                if job:
                    logger.info(f"Processing Job {job['id']}: {job['type']}")
                    result = self.process_job(job)
                    self.dispatcher.complete_job(job['id'], result)
                else:
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(5)

        logger.info("Ziva Main Loop stopped gracefully.")

    def process_incoming_messages(self):
        """
        Lê mensagens 'new' do banco de dados e processa.
        """
        conn = self.db._get_conn()
        cursor = conn.cursor()
        # Busca novas mensagens tipo incoming
        # Schema: id, filename, direction, source, target, content,
        # timestamp, status
        cursor.execute(
            "SELECT * FROM messages WHERE direction='incoming' AND status='new'"
        )
        rows = cursor.fetchall()

        for row in rows:
            msg_id = row[0]
            content = row[5]
            try:
                data = json.loads(content)
                msg_type = data.get("type")

                if msg_type == "knowledge_sync":
                    payload = data.get("payload", {})
                    insight_text = payload.get("content")
                    origin = payload.get("origin_node")
                    if insight_text:
                        logger.info(f"Recebendo conhecimento de {origin}...")
                        # Injeta memoria
                        embedding = self.llm.embedding(insight_text)
                        if embedding:
                            self.knowledge.add_text(insight_text, embedding, {
                                "source": f"p2p_sync_{origin}",
                                "type": "insight"
                            })
                            logger.info("Conhecimento remoto assimilado.")

                # Marca como processada
                cursor.execute(
                    "UPDATE messages SET status='processed' WHERE id=?", (
                        msg_id,)
                )
                conn.commit()

            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar mensagem {msg_id}")
                cursor.execute(
                    "UPDATE messages SET status='error' WHERE id=?", (msg_id,)
                )
                conn.commit()
            except Exception as e:
                logger.error(f"Erro ao processar mensagem {msg_id}: {e}")

        conn.close()

    def process_job(self, job):
        """
        Executes a specific job from the queue using LangGraph.

        Args:
            job (dict): Job data (id, type, payload).
        """
        logger.info(f"Processing job {job['id']} ({job['type']})")
        self.db.update_job_status(job['id'], 'processing')

        try:
            # Import the compiled graph
            from core.graph.ziva_graph import app

            # Prepare input state
            user_input = job['payload'].get('input') or str(job['payload'])
            initial_state = {"input": user_input}

            # Run the graph
            final_state = app.invoke(initial_state)

            # Extract response
            response = final_state.get("response", "No response.")

            result = {"response": response}
            self.db.update_job_status(job['id'], 'completed', result)
            logger.info(
                f"Job completed via Graph. Resp length: {len(response)}"
            )

        except Exception as e:
            logger.error(f"Job failed in Graph execution: {e}")
            result = {"error": str(e)}
            self.db.update_job_status(job['id'], 'failed', result)
        
        return result

    def execute_tool(self, tool_call_str):
        """
        Analisa uma string de chamada de ferramenta e a executa.
        Formato esperado: {"tool": "name", "args": {...}}
        """
        try:
            call = json.loads(tool_call_str)
            tool_name = call.get("tool")
            args = call.get("args", {})

            tool_func = self.tool_manager.get_tool(tool_name)
            if tool_func:
                logger.info(
                    f"Executando ferramenta: {tool_name} com args {args}")
                return tool_func(**args)
            return f"Erro: Ferramenta '{tool_name}' não encontrada."
        except Exception as e:
            return f"Erro ao executar ferramenta: {e}"

    def construct_prompt(self, payload, compact=False):
        """
        Constrói o prompt final para o LLM.
        Inclui definições de ferramentas com assinaturas reais.
        Enriquece com contexto conversacional.
        """
        import inspect

        active_profile = self.profile_compact if compact else self.profile

        session_id = payload.get('session_id')
        if session_id:
            if session_id not in self.conversation_contexts:
                self.conversation_contexts[session_id] = ConversationContext(
                    session_id
                )
            context = self.conversation_contexts[session_id]
        else:
            context = None

        user_input = payload.get('input', '')

        if context:
            resolved_input = context.resolve_anaphora(user_input)
            if resolved_input != user_input:
                logger.info(
                    f"Ref resolvida: '{user_input}' → '{resolved_input}'")
                user_input = resolved_input

            context.detect_intent(user_input)
            context.extract_entities(user_input)
            context.add_message("user", user_input)

        tools_desc = ""
        for name, func in self.tools.items():
            try:
                sig = inspect.signature(func)
                params_str = str(sig)
                doc = func.__doc__ or "Sem descrição."

                if compact:
                    doc = doc.strip().split("\n")[0]

                tools_desc += f"- {name}{params_str}: {doc.strip()}\n"
            except Exception:
                doc = func.__doc__ or "Sem descrição."
                if compact:
                    doc = doc.strip().split("\n")[0]
                tools_desc += f"- {name}: {doc.strip()}\n"

        context_info = (
            context.get_context_summary() if context else "Sem contexto."
        )

        if compact:
            prompt = f"""{active_profile}

DATA ATUAL: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

FERRAMENTAS:
{tools_desc}

CONTEXTO:
{payload.get('context', '')}
"""
        else:
            prompt = f"""
{active_profile}

DATA ATUAL: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

FERRAMENTAS DISPONÍVEIS:
{tools_desc}

CONTEXTO CONVERSACIONAL:
{context_info}

REGRAS CRÍTICAS DE COMPORTAMENTO:
1. VOCÊ É UM AGENTE AUTÔNOMO - Sua função é EXECUTAR, não explicar.
2. USE AS FERRAMENTAS imediatamente quando o usuário pedir para fazer algo.
3. NÃO explique como fazer - FAÇA diretamente usando as ferramentas.
4. NÃO mostre comandos para o usuário - EXECUTE você mesmo.
5. Responda SEMPRE em Português do Brasil.
6. USE O CONTEXTO para entender referências e manter continuidade.
7. **VERIFIQUE A DATA ATUAL**: Se o usuário perguntar sobre fatos que podem
ter mudado, você DEVE usar `web_search`.
8. **SÍNTESE DE PESQUISA**: Ao responder com base em múltiplos resultados,
ignore repetições e ruído. Escreva uma resposta única e fluida. Se houver
dados conflitantes, DESTAQUE a discrepância.

FORMATO DE EXECUÇÃO DE FERRAMENTAS:
Quando precisar executar uma ferramenta, retorne APENAS o JSON:
```json
{{"tool": "nome_da_ferramenta", "args": {{"arg1": "valor1"}}}}
```

CONTEXTO ADICIONAL:
{payload.get('context', 'Nenhum contexto adicional.')}

LEMBRE-SE: Você é um EXECUTOR, não um professor. Aja imediatamente!
"""
        return f"{prompt}\n\nUsuário: {user_input}\nZiva:"


    def broadcast_knowledge(self, insights):
        """
        Transmite insights para outros workers via Outbox.
        """
        if not insights:
            return

        workers = self.dispatcher.registry.list_workers()
        targets = [
            w['id'] for w in workers
            if w['id'] != "node07" and w.get('status') == 'active'
        ]

        if not targets:
            logger.debug("Nenhum worker ativo para broadcast.")
            return

        for insight in insights:
            for target in targets:
                filename = (
                    f"knowledge_{insight.get('origin_job', 'sync')}_{int(time.time())}.json"
                )
                # Salva para Outbox
                outbox_dir = os.getenv("ZIVA_OUTBOX_DIR", "/app/outbox")
                outbox_path = Path(f"{outbox_dir}/{filename}")
                outbox_path.parent.mkdir(parents=True, exist_ok=True)

                packet = {
                    "type": "knowledge_sync",
                    "target": target,
                    "payload": insight
                }

                try:
                    with open(outbox_path, 'w') as f:
                        json.dump(packet, f)
                    logger.info(
                        f"Insight extraído e enviado para {target}: {filename}"
                    )
                except Exception as e:
                    logger.error(f"Erro ao salvar broadcast na outbox: {e}")


if __name__ == "__main__":
    agent = ZivaAgent()
    agent.run_loop()