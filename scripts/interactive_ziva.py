#!/usr/bin/env python3
from agent.ziva import ZivaAgent
import sys
import os
import logging
import time

# Adiciona raiz do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Silencia logs chatty durante interacao
logging.getLogger("Ziva").setLevel(logging.WARNING)
logging.getLogger("ZivaLauncher").setLevel(logging.WARNING)
logging.getLogger("RemoteExecutor").setLevel(logging.WARNING)


def main():
    print("""
    ╔══════════════════════════════════════╗
    ║        ZIVA INTERACTIVE REPL         ║
    ║   Digite 'sair' para encerrar        ║
    ╚══════════════════════════════════════╝
    """)

    agent = ZivaAgent()
    # agent._init_llm() # Pre-load LLM (Removed: method does not exist, lazy
    # loading used instead)

    # Inicia Sessao no DB
    conn = agent.db._get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (start_time) VALUES (?)", (time.time(),))
    session_id = cursor.lastrowid
    conn.commit()
    # # conn.close()

    # Check for CLI args as initial input
    initial_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None

    while True:
        try:
            # Input do usuário
            if initial_query:
                print(f"\033[1;34mVocê (CLI)>\033[0m {initial_query}")
                user_input = initial_query
                initial_query = None  # Clear after first use
            else:
                user_input = input("\033[1;34mVocê>\033[0m ").strip()

            # Gatilho de Hibernação solicitado pelo usuário
            if "vamos parar por hoje" in user_input.lower():
                print(
                    "\033[1;33mZiva>\033[0m Entendido. Salvando estado, consolidando memórias e descarregando processos...")

                # 1. Finaliza Sessão no DB
                conn = agent.db._get_conn()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE sessions SET end_time = ?, status = 'completed' WHERE id = ?",
                    (time.time(),
                     session_id))
                conn.commit()
                # conn.close()

                # 2. Gera Documentação de Aprendizado Imediata
                try:
                    from core.knowledge_gen import KnowledgeGenerator
                    kgen = KnowledgeGenerator()
                    kgen.process_completed_sessions()
                except BaseException:
                    pass

                # 3. Dispara Cleanup de Processos
                from scripts.cleanup_system import hibernate_ziva
                hibernate_ziva()

                print("✅ Sistema hibernado com sucesso. Até a próxima!")
                break

            if user_input.lower() in ["sair", "exit", "quit"]:
                print("Encerrando sessão interativa...")
                # Marca fim da sessao
                conn = agent.db._get_conn()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE sessions SET end_time = ?, status = 'completed' WHERE id = ?",
                    (time.time(),
                     session_id))
                conn.commit()
                # conn.close()
                break

            if not user_input:
                continue

            # Log User Interaction
            conn = agent.db._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO interactions (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id,
                 "user",
                 user_input,
                 time.time()))
            conn.commit()

            # --- EXECUÇÃO VIA LANGGRAPH (NOVO) ---
            try:
                from core.graph.ziva_graph import app as graph_app

                print("\033[90m[Ziva processando via Graph...]\033[0m")

                # Retrieve minimal history for context
                cursor.execute(
                    "SELECT role, content FROM interactions WHERE session_id = ? ORDER BY timestamp DESC LIMIT 3",
                    (session_id,
                     ))
                history_rows = cursor.fetchall()
                history_text = "\n".join(
                    [f"{row[0].upper()}: {row[1]}" for row in reversed(history_rows)])

                # Run Graph
                # History implicitly handled by persistent state in advanced
                # version, or manually injected if needed.
                final_state = graph_app.invoke({"input": user_input})

                response = final_state.get("response", "...")
                tool_output = final_state.get("tool_output")

                # Mostrar Resposta Principal
                print("\033[1;32mZiva>\033[0m ", end="", flush=True)
                print(response)

                # Se houve uso de ferramenta, mostrar resultado
                if tool_output:
                    print(f"\n\033[1;36m[Tool Output]:\033[0m {tool_output}")
                    # Log Tool Output
                    cursor.execute(
                        "INSERT INTO interactions (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                        (session_id,
                         "system",
                         f"Tool Output: {
                             str(tool_output)}",
                            time.time()))

            except Exception as e:
                print(f"\n\033[1;31m❌ Erro no Grafo:\033[0m {e}")
                response = f"Erro sistêmico: {e}"
            # ------------------------------------

            # Log Assistant Interaction
            cursor.execute(
                "INSERT INTO interactions (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id,
                 "assistant",
                 response,
                 time.time()))
            conn.commit()
            # # conn.close()

            # --- MANTER SINCRONIA P2P ---
            # Processa mensagens de outros nós (ex: Gabrielle) sem bloquear
            # muito
            try:
                print("\033[90m[Sincronizando com a Colmeia...]\033[0m")
                agent.process_incoming_messages()
                # Opcional: Executar ciclo de aprendizado rápido se ocioso?
                # agent.learner.run_cycle()
            except Exception as e:
                pass  # Não interromper o chat
            # ----------------------------

            print("-" * 50)

        except KeyboardInterrupt:
            print("\nSaindo...")
            break
        except EOFError:
            print("\nEOF detectado. Encerrando sessão.")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}")


if __name__ == "__main__":
    main()
