from core.vector_store import VectorStore
import sys
import os
from rich.console import Console
from rich.table import Table

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


console = Console()


def list_sources():
    console.print(
        "[bold cyan]💾 Inspecting Ziva Memory (Qdrant)...[/bold cyan]")

    try:
        vs = VectorStore()

        sources = set()
        total_points = 0

        # Scroll API
        next_page_offset = None
        while True:
            records, next_page_offset = vs.client.scroll(
                collection_name="ziva_knowledge",
                limit=100,
                offset=next_page_offset,
                with_payload=True,
                with_vectors=False
            )

            for r in records:
                if r.payload and "source" in r.payload:
                    sources.add(r.payload["source"])
                total_points += 1

            if next_page_offset is None:
                break

        console.print(
            f"[green]✓ Total Memory Fragments (Chunks): {total_points}[/green]")
        console.print(
            f"[green]✓ Distinct Sources Found: {
                len(sources)}[/green]\n")

        table = Table(title="Ingested Documents")
        table.add_column("Filename", style="magenta")
        table.add_column("Status", style="green")

        for source in sorted(list(sources)):
            table.add_row(source, "Active")

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]❌ Error inspecting memory: {e}[/bold red]")


if __name__ == "__main__":
    list_sources()
