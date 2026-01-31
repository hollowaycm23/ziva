from core.llm import LLMService
from core.vector_store import VectorStore
import sys
import os
from rich.console import Console
from rich.table import Table

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


console = Console()


def diagnose_retrieval():
    console.print("[bold cyan]🕵️ Diagnosing Retrieval System...[/bold cyan]")

    # 1. Check Connection
    try:
        vs = VectorStore()
        count = vs.client.count(collection_name="ziva_knowledge").count
        console.print(
            f"[green]✓ Connected to Qdrant. Collection 'ziva_knowledge' has {count} points.[/green]")

        if count == 0:
            console.print(
                "[bold red]❌ Database is empty! Run ingest_docs.py again.[/bold red]")
            return

    except Exception as e:
        console.print(f"[bold red]❌ Connection Error: {e}[/bold red]")
        return

    # 2. Check Embedding Generation
    llm = LLMService(model="nomic-embed-text:latest")
    test_query = "Qual é a arquitetura do Ziva?"
    console.print(
        f"\n[yellow]Generating embedding for: '{test_query}'...[/yellow]")

    vec = llm.embedding(test_query)
    if not vec or len(vec) == 0:
        console.print(
            "[bold red]❌ Failed to generate embedding from Ollama.[/bold red]")
        return
    else:
        console.print(
            f"[green]✓ Embedding generated (dim: {
                len(vec)})[/green]")

    # 3. Perform Raw Search
    console.print("\n[yellow]Performing Raw Search (Limit 5)...[/yellow]")
    results = vs.search(embedding=vec, limit=5)

    if not results:
        console.print("[bold red]❌ Search returned no results.[/bold red]")
    else:
        table = Table(title="Search Results")
        table.add_column("Score", justify="right", style="cyan")
        table.add_column("Source", style="magenta")
        table.add_column("Preview", style="white")

        for r in results:
            meta = r.get("metadata", {})
            source = meta.get("source", "Unknown")
            preview = r["text"][:100].replace("\n", " ") + "..."
            table.add_row(str(round(r["score"], 4)), source, preview)

        console.print(table)


if __name__ == "__main__":
    diagnose_retrieval()
