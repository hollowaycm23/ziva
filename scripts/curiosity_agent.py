#!/usr/bin/env python3
"""
Ziva Curiosity Agent
Agente proativo que identifica lacunas de conhecimento e sugere aprendizados.
"""

from extensions.search_connector import get_search_connector
from core.topic_explorer import get_topic_explorer
import sys
import os
import logging
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)


# Silenciar logs internos para este script de UI
logging.basicConfig(level=logging.ERROR)
console = Console()


def main():
    console.print(
        Panel(
            "[bold magenta]🧠 ZIVA SCHOLAR - CURIOSITY AGENT[/bold magenta]",
            border_style="magenta"))

    explorer = get_topic_explorer()
    search = get_search_connector()

    with console.status("[bold cyan]🔍 Analisando base de conhecimento (Clusterização)...[/bold cyan]"):
        analysis = explorer.analyze_knowledge_space(n_clusters=5)

    if 'error' in analysis:
        console.print(f"[red]Erro na análise: {analysis['error']}[/red]")
        return

    # Mostrar Clusters
    table = Table(title="🗺️ Mapa de Conhecimento")
    table.add_column("Cluster", style="cyan")
    table.add_column("Tamanho", justify="right")
    table.add_column("Amostra de Conteúdo", style="dim")

    clusters = analysis.get('clusters', {})
    for name, data in clusters.items():
        table.add_row(name, str(data['size']), data['sample'][:60] + "...")

    console.print(table)
    console.print(
        f"\n[bold green]Total de Memórias:[/bold green] {analysis.get('total_points', 0)}")

    # Gerar Curiosidade
    console.print(
        "\n[bold yellow]🤔 Gerando Perguntas de Curiosidade...[/bold yellow]")
    questions = explorer.generate_curiosity_questions()

    for i, q in enumerate(questions, 1):
        console.print(f"{i}. [italic]{q}[/italic]")

        # Opcional: Auto-pesquisa
        # console.print("   [dim]Pesquisando na web...[/dim]")
        # res = search.search_web(q, limit=1)
        # if res:
        #     console.print(f"   💡 Encontrado: {res[0].title} - {res[0].url}")

    console.print("\n[bold blue]Próximos Passos:[/bold blue]")
    console.print(
        "Para expandir o conhecimento, execute o crawler em novos diretórios ou converse sobre estes tópicos.")


if __name__ == "__main__":
    main()
