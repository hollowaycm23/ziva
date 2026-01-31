#!/usr/bin/env python3
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
    from core.agent.graph import build_agent
except ImportError as e:
    print(f"Error importing Agent: {e}")
    print("Ensure you are running from project root or dependencies are installed.")
    sys.exit(1)

# Configurar histórico de comandos
HISTORY_FILE = os.path.expanduser("~/.ziva_chat_history")
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
    "thought": "dim italic"
})

console = Console(theme=custom_theme)


def print_header():
    header_text = """
    [bold magenta]ZIVA AI[/bold magenta] - [italic]Sistema de Inteligência Autônoma[/italic]
    Agente Local (LangGraph + Qdrant + Ollama)
    [dim]Comandos: 'sair', 'exit' | Ctrl+C: Cancelar/Sair[/dim]
    """
    console.print(
        Panel(
            header_text,
            border_style="magenta",
            title="[bold white]v2.0[/bold white]",
            subtitle="[ziva]Autonomous[/ziva]"))


def main():
    print_header()

    # Initialize Agent
    with console.status("[ziva]Inicializando Agente Neural...[/ziva]", spinner="dots"):
        try:
            agent_app = build_agent()
            console.print("[success]✓ Agente Carregado com Sucesso[/success]")
        except Exception as e:
            console.print(f"[error]Falha ao carregar agente: {e}[/error]")
            return

    # Initialize Chat History and State
    messages = []
    current_mode = "general"

    while True:
        try:
            console.print("\n[user]Você:[/user] ", end="")
            user_input = input()

            if user_input.lower() in ["sair", "exit", "quit", "tchau"]:
                console.print("\n[info]Encerrando conexão. Até breve![/info]")
                break

            if not user_input.strip():
                continue

            # Initial State
            state = {
                "question": user_input,
                "documents": [],
                "generation": "",
                "chat_history": messages,
                "mode": current_mode
            }
            final_response = ""

            # Agent Execution Loop
            console.print()  # spacer
            with console.status("[ziva]Pensando...[/ziva]", spinner="dots") as status:
                try:
                    # Stream steps
                    for output in agent_app.stream(state):
                        for key, value in output.items():
                            # UI Feedback based on Node
                            if key == "retrieve":
                                status.update(
                                    f"[cyan]🔍 Buscando na memória (Qdrant)...[/cyan]")
                                time.sleep(0.5)  # Visual delay for UX
                            elif key == "grade_documents":
                                docs_count = len(value.get("documents", []))
                                status.update(
                                    f"[yellow]⚖️ Avaliando relevância ({docs_count} docs)...[/yellow]")
                                time.sleep(0.5)
                            elif key == "transform_query":
                                status.update(
                                    f"[magenta]🤔 Reformulando pergunta...[/magenta]")
                                time.sleep(0.5)
                            elif key == "generate":
                                status.update(
                                    f"[green]✨ Gerando resposta final ({current_mode})...[/green]")
                                final_response = value.get("generation", "")
                            elif key == "web_search":
                                status.update(
                                    f"[cyan]🌐 Pesquisando na Web (SearXNG + Playwright)...[/cyan]")
                            elif key == "offline_search":
                                status.update(
                                    f"[blue]📚 Pesquisando Offline (Kiwix)...[/blue]")
                            elif key == "set_mode":
                                new_mode = value.get("mode")
                                if new_mode:
                                    current_mode = new_mode
                                status.update(
                                    f"[bold magenta]🔄 Alterando modo para: {
                                        current_mode.upper()}[/bold magenta]")
                                time.sleep(1.0)
                            elif key == "check_weather":
                                status.update(
                                    f"[yellow]🌦️ Verificando clima...[/yellow]")
                            elif key == "sherlock_search":
                                status.update(
                                    f"[red]🕵️ Executing Sherlock OSINT...[/red]")

                except KeyboardInterrupt:
                    status.stop()
                    console.print(
                        "\n[warning]🛑 Pensamento cancelado pelo usuário.[/warning]")
                    continue  # Volta para o input loop

                except Exception as e:
                    console.print(
                        f"[error]Erro na execução do agente: {e}[/error]")
                    continue

            # Display Response
            if final_response:
                md = Markdown(final_response)
                console.print(
                    Panel(
                        md,
                        title="[ziva]Ziva[/ziva]",
                        border_style="magenta",
                        padding=(
                            1,
                            2)))

                # Update History
                messages.append(f"Human: {user_input}")
                messages.append(f"AI: {final_response}")
            else:
                console.print(
                    "[warning]O agente não gerou uma resposta final.[/warning]")

            console.print("[dim]" + "─" * console.width + "[/dim]")

        except KeyboardInterrupt:
            console.print("\n[warning]Interrompido pelo usuário.[/warning]")
            break
        except Exception as e:
            console.print(f"\n[error]Erro Crítico: {e}[/error]")
            break


if __name__ == "__main__":
    main()
