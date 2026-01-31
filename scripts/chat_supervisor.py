#!/usr/bin/env python3
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import sys
import os
import time
import readline
import atexit
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.status import Status
from rich.theme import Theme

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Import Agent
try:
    from core.graph.supervisor import supervisor_app
except ImportError as e:
    print(f"Error importing Supervisor: {e}")
    sys.exit(1)

# Configurar histórico de comandos
HISTORY_FILE = os.path.expanduser("~/.ziva_chat_supervisor_history")
if os.path.exists(HISTORY_FILE):
    try:
        readline.read_history_file(HISTORY_FILE)
    except BaseException:
        pass
readline.set_history_length(1000)
atexit.register(readline.write_history_file, HISTORY_FILE)

# Configuração de Tema Premium
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "ziva": "bold magenta",
    "user": "bold blue",
    "worker": "green"
})

console = Console(theme=custom_theme)


def print_header():
    header_text = """
    [bold magenta]ZIVA AI - SUPERVISOR MODE[/bold magenta]
    Multi-Agent System (Supervisor -> Researcher/Coder)
    [dim]Comandos: 'sair', 'exit' | Ctrl+C: Cancelar[/dim]
    """
    console.print(
        Panel(
            header_text,
            border_style="magenta",
            title="[bold white]v3.0[/bold white]"))


def main():
    print_header()

    messages_history = []

    while True:
        try:
            console.print("\n[user]Você:[/user] ", end="")
            user_input = input()

            if user_input.lower() in ["sair", "exit", "quit"]:
                console.print("\n[info]Até breve![/info]")
                break

            if not user_input.strip():
                continue

            # Prepare Input
            # Supervisor expects 'messages' list. We should append history.
            messages_history.append(HumanMessage(content=user_input))

            inputs = {"messages": messages_history}

            final_response = ""

            # Agent Execution Loop
            console.print()
            with console.status("[ziva]Orquestrando Agentes...[/ziva]", spinner="dots") as status:
                try:
                    # Stream steps
                    # Config recursion limit high for multi-turn agent loops
                    for output in supervisor_app.stream(
                            inputs, config={"recursion_limit": 50}):
                        for node_name, value in output.items():

                            # Update UI based on Node
                            if node_name == "Supervisor":
                                next_step = value.get("next", "Unknown")
                                status.update(
                                    f"[magenta]🧠 Supervisor decidiu: {next_step}[/magenta]")
                                time.sleep(0.5)

                            elif node_name == "Researcher":
                                # Extract content from the last message added
                                # by Researcher
                                if "messages" in value and value["messages"]:
                                    last_msg = value["messages"][-1]
                                    preview = last_msg.content[:50].replace(
                                        "\n", " ") + "..."
                                    status.update(
                                        f"[green]🔍 Researcher: {preview}[/green]")
                                else:
                                    status.update(
                                        f"[green]🔍 Researcher trabalhando...[/green]")
                                time.sleep(0.5)

                            elif node_name == "Coder":
                                if "messages" in value and value["messages"]:
                                    last_msg = value["messages"][-1]
                                    preview = last_msg.content[:50].replace(
                                        "\n", " ") + "..."
                                    status.update(
                                        f"[green]💻 Coder: {preview}[/green]")
                                else:
                                    status.update(
                                        f"[green]💻 Coder trabalhando...[/green]")
                                time.sleep(0.5)

                            # Keep state updated?
                            # Supervisor app stream returns the update.
                            # We don't manually update 'messages_history' here because
                            # we will grab the final state at the end OR trust the stream updates.
                            # LangGraph stream output is the diff.
                            # BUT, to maintain history for NEXT turn, we need the full list.
                            # We can re-invoke or manually append.
                            # Easiest: Just capture the final response for display,
                            # and let the variable 'messages_history' be
                            # updated with result.

                            # Actually, getting the final state from stream is tricky if we just read diffs.
                            # Let's perform a full invoke for state-of-truth? No, that runs twice.
                            # We should accumulate the messages from the
                            # 'value'.

                            if "messages" in value:
                                for m in value["messages"]:
                                    if isinstance(m, BaseMessage):
                                        # Deduplicate? LangGraph returns new messages.
                                        # We just append them to our local history tracking for the next loop.
                                        # Wait, 'messages_history' needs to be exact.
                                        # Let's rely on the fact that we can just query the graph?
                                        # Or just append the AI response at the
                                        # end.

                                        # For the loop, we just print.
                                        pass

                    # After stream ends, we need the final response to print.
                    # We can pick it from the last node output in the loop?
                    # Or simpler: The last message in the conversation is the
                    # response.

                    # To be robust, let's run a final invoke (or updated stream logic)
                    # Actually, stream allows accessing the accumulated state if we use `stream_mode="values"`.
                    # But standard stream is "updates".

                    # Let's just grab the last message from the last update.
                    # 'value["messages"][-1]' from the logic component.

                    # Issue: The last update might be from Supervisor saying "FINISH".
                    # Supervisor output is {"next": "FINISH"}. It doesn't yield a message.
                    # The actual answer came from the previous node
                    # (Researcher/Coder).

                    # We need to track the last "AIMessage" seen.

                except KeyboardInterrupt:
                    status.stop()
                    console.print("\n[warning]🛑 Cancelado.[/warning]")
                    continue
                except Exception as e:
                    console.print(f"[error]Erro: {e}[/error]")
                    continue

            # Need to fetch the final answer content.
            # We can re-invoke with the history we built? No.
            # We need to extract the added messages from the graph run.

            # Since we can't easily extract full state from simple stream loop without refactoring,
            # Let's use `invoke` for the user interaction to get simple final state,
            # OR just trust the last AI message in our manual tracking.

            # BETTER APPROACH:
            # Use `invoke` to get the final state. Using stream just for fancy UI is hard if we don't handle state.
            # Let's use `invoke` for simplicity and correctness of history.
            # We lose the "streaming progress" (Brain -> Researcher...), but we can simulate/log it if we use callbacks.
            # Or just use stream processing correctly.

            # Let's stick to invoke for robustness in this script v1.
            with console.status("[ziva]Processando (Supervisor)...[/ziva]", spinner="dots"):
                final_state = supervisor_app.invoke(
                    inputs, config={"recursion_limit": 50})

                # Update history with EVERYTHING that happened
                messages_history = final_state["messages"]

                # Get last message
                last_msg = messages_history[-1]
                final_response = last_msg.content

            # Display
            md = Markdown(final_response)
            console.print(
                Panel(
                    md,
                    title="[ziva]Ziva[/ziva]",
                    border_style="magenta",
                    padding=(
                        1,
                        2)))

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"\n[error]Erro Crítico: {e}[/error]")
            break


if __name__ == "__main__":
    main()
