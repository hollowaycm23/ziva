#!/usr/bin/env python3
"""
Test and Demo Script for Prompt Optimization System
Tests both DSPy and Optimus backends with various prompts.
"""

from rich.syntax import Syntax
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from core.prompt_optimizer import UnifiedPromptOptimizer, OptimizerBackend
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


console = Console()

# Test prompts with different complexities
TEST_PROMPTS = [{"name": "Simple Code Request",
                 "prompt": "write a snake game in python",
                 "strategy": "code"},
                {"name": "Complex Analysis",
                 "prompt": "analyze the performance bottlenecks in my web application and suggest optimizations",
                 "strategy": "general"},
                {"name": "Creative Task",
                 "prompt": "create a story about AI assistants",
                 "strategy": "creative"},
                {"name": "Technical Documentation",
                 "prompt": "document the REST API for user authentication",
                 "strategy": "code"}]


def display_optimization_result(
        name: str, original: str, optimized: str, backend: str):
    """Display a single optimization result"""
    console.print(f"\n[bold cyan]{'=' * 70}[/bold cyan]")
    console.print(Panel(
        f"[bold]{name}[/bold]",
        style="cyan"
    ))

    console.print(f"\n[yellow]Original ({len(original)} chars):[/yellow]")
    console.print(f"  {original}")

    console.print(
        f"\n[green]Optimized with {backend} ({
            len(optimized)} chars, {
            len(optimized) -
            len(original):+d}):[/green]")
    console.print(
        f"  {optimized[:300]}{'...' if len(optimized) > 300 else ''}")


def test_single_backend(backend: OptimizerBackend):
    """Test a single optimization backend"""
    console.print(
        f"\n[bold magenta]Testing {
            backend.value.upper()} Backend[/bold magenta]\n")

    try:
        optimizer = UnifiedPromptOptimizer(backend=backend)

        for test in TEST_PROMPTS:
            result = optimizer.optimize(
                test["prompt"],
                strategy=test["strategy"]
            )

            display_optimization_result(
                test["name"],
                test["prompt"],
                result,
                backend.value
            )

    except Exception as e:
        console.print(f"[red]❌ Error testing {backend.value}: {e}[/red]")


def compare_backends():
    """Compare optimization results from multiple backends"""
    console.print("\n[bold magenta]📊 BACKEND COMPARISON[/bold magenta]\n")

    optimizer = UnifiedPromptOptimizer(backend=OptimizerBackend.AUTO)

    for test in TEST_PROMPTS:
        console.print(f"\n[bold cyan]Test: {test['name']}[/bold cyan]")
        console.print(f"[dim]Original: {test['prompt']}[/dim]\n")

        comparison = optimizer.compare_backends(
            test["prompt"], test["strategy"])

        # Create comparison table
        table = Table(title="Optimization Results")
        table.add_column("Backend", style="cyan")
        table.add_column("Length", justify="right", style="yellow")
        table.add_column("Change", justify="right", style="green")
        table.add_column("Preview", style="white")

        for backend_name, result in comparison["backends"].items():
            change_color = "green" if result["change"] > 0 else "red" if result["change"] < 0 else "yellow"
            table.add_row(
                backend_name.upper(),
                str(result["length"]),
                f"[{change_color}]{result['change']:+d}[/{change_color}]",
                result["prompt"][:80] + "..."
            )

        console.print(table)
        console.print()


def run_interactive_mode():
    """Interactive mode for testing custom prompts"""
    console.print(
        "\n[bold green]🎮 Interactive Prompt Optimization Mode[/bold green]")
    console.print("[dim]Type 'quit' to exit[/dim]\n")

    optimizer = UnifiedPromptOptimizer(backend=OptimizerBackend.AUTO)

    while True:
        try:
            prompt = input("\n[Prompt to optimize] > ")

            if prompt.lower() in ['quit', 'exit', 'q']:
                console.print("\n[yellow]👋 Bye![/yellow]")
                break

            if not prompt.strip():
                continue

            # Ask for strategy
            console.print(
                "[dim]Strategy? (general/code/creative)[/dim] [default: general]")
            strategy = input("> ").strip() or "general"

            if strategy not in ["general", "code", "creative"]:
                console.print("[red]Invalid strategy, using 'general'[/red]")
                strategy = "general"

            # Optimize
            optimized = optimizer.optimize(prompt, strategy=strategy)

            display_optimization_result(
                "Your Prompt",
                prompt,
                optimized,
                optimizer.backend.value
            )

        except KeyboardInterrupt:
            console.print("\n\n[yellow]👋 Interrupted. Bye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def main():
    """Main entry point"""
    console.print(Panel(
        "[bold cyan]Ziva Prompt Optimization System[/bold cyan]\n"
        "[dim]Testing DSPy & Optimus Integration[/dim]",
        border_style="cyan"
    ))

    import argparse
    parser = argparse.ArgumentParser(
        description="Test prompt optimization system")
    parser.add_argument(
        "--backend",
        choices=["optimus", "dspy", "auto", "compare"],
        default="compare",
        help="Backend to test (default: compare)"
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode"
    )

    args = parser.parse_args()

    if args.interactive:
        run_interactive_mode()
    elif args.backend == "compare":
        compare_backends()
    else:
        backend = OptimizerBackend(args.backend)
        test_single_backend(backend)

    console.print(f"\n[bold green]✅ Test completed![/bold green]\n")


if __name__ == "__main__":
    main()
