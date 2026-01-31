from core.llm import LLMService
from core.vector_store import VectorStore
import sys
import os
from rich.console import Console
from rich.table import Table
import argparse

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


console = Console()


def search_knowledge(query):
    console.print(
        f"[bold cyan]🔍 Searching Memory for: '{query}'...[/bold cyan]")

    try:
        vs = VectorStore()
        llm = LLMService(model="nomic-embed-text:latest")

        # Generate embedding
        vec = llm.embedding(query)
        if not vec:
            console.print(
                "[bold red]❌ Failed to generate embedding.[/bold red]")
            return

        # Perform Search
        results = vs.search(embedding=vec, limit=10)

        if not results:
            console.print("[yellow]⚠️ No results found.[/yellow]")
        else:
            table = Table(title=f"Search Results: {query}")
            table.add_column("Score", justify="right", style="cyan")
            table.add_column("Source", style="magenta")
            table.add_column("Content", style="white")

            for r in results:
                meta = r.get("metadata", {})
                source = meta.get("source", "Unknown")
                # Show more content
                preview = r["text"][:200].replace("\n", " ") + "..."
                table.add_row(str(round(r["score"], 4)), source, preview)

            console.print(table)

    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/bold red]")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        search_knowledge(query)
    else:
        print("Usage: python3 scripts/search_knowledge.py <query>")
