from core.agent.graph import build_agent
import sys
import os
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


console = Console()


def benchmark_agent():
    console.print("[bold magenta]🚀 Ziva Knowledge Benchmark[/bold magenta]")

    questions = [
        "Qual é a arquitetura do Ziva RAG?",
        "Quem é Gabrielle e quais seus protocolos de comunicação?",
        "Quais foram os conflitos de bloqueio fundamental identificados na análise?",
        "O que é o LangGraph e por que ele foi escolhido?",
        "Quais lições de Javascript estão disponíveis na memória?"]

    app = build_agent()

    for i, q in enumerate(questions, 1):
        console.print(f"\n[bold yellow]Q{i}: {q}[/bold yellow]")

        state = {"question": q, "documents": [], "generation": ""}
        start_time = time.time()

        final_answer = ""
        retrieved_count = 0

        try:
            for output in app.stream(state):
                for key, value in output.items():
                    if key == "retrieve":
                        retrieved_count = len(value.get("documents", []))
                    elif key == "generate":
                        final_answer = value.get("generation", "")

            elapsed = time.time() - start_time

            console.print(Panel(
                f"[cyan]Retrieved Docs: {retrieved_count}[/cyan]\n"
                f"[green]Time: {elapsed:.2f}s[/green]\n\n"
                f"[white]{final_answer}[/white]",
                title="Agent Response"
            ))

        except Exception as e:
            console.print(f"[bold red]❌ Error: {e}[/bold red]")


if __name__ == "__main__":
    benchmark_agent()
