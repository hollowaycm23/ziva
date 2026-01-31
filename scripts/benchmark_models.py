#!/usr/bin/env python3
"""
Benchmark Models - Avalia performance de múltiplos LLMs
Mede Latência (TTFT) e Throughput (Tokens/s)
"""

from core.model_manager import get_model_manager
import sys
import os
import time
import requests
import json
import statistics
from rich.console import Console
from rich.table import Table

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


console = Console()

TEST_PROMPTS = {
    "coding": "Write a Python function to calculate Fibonacci series recursively with memoization.",
    "reasoning": "If I have 3 apples and you take 2, but then give me 1 back, how many apples do I have? Explain step by step.",
    "general": "Explain the concept of entropy in simple terms."}


def benchmark_model(model_name: str, prompts: dict, iterations: int = 2):
    """Roda benchmark em um modelo"""
    console.print(f"\n[bold cyan]🧪 Benchmarking {model_name}...[/bold cyan]")

    url = "http://localhost:11434/api/generate"
    results = {}

    # Preload
    try:
        requests.post(url, json={"model": model_name})
    except BaseException:
        console.print("[red]Erro ao conectar Ollama[/red]")
        return None

    for category, prompt in prompts.items():
        latencies = []
        throughputs = []

        for i in range(iterations):
            start_time = time.time()
            first_token_time = None
            token_count = 0

            try:
                with requests.post(url, json={"model": model_name, "prompt": prompt}, stream=True) as resp:
                    for line in resp.iter_lines():
                        if not line:
                            continue

                        if first_token_time is None:
                            first_token_time = time.time()

                        try:
                            data = json.loads(line)
                            if not data.get('done'):
                                token_count += 1
                        except BaseException:
                            pass

                end_time = time.time()

                # Metrics
                ttft = (
                    first_token_time -
                    start_time) if first_token_time else 0
                total_time = end_time - start_time
                tps = token_count / total_time if total_time > 0 else 0

                latencies.append(ttft)
                throughputs.append(tps)

            except Exception as e:
                console.print(f"[red]Erro na iteração {i}: {e}[/red]")

        results[category] = {
            "avg_latency_ms": statistics.mean(latencies) * 1000,
            "avg_tps": statistics.mean(throughputs)
        }
        console.print(
            f"   - {category}: {
                results[category]['avg_latency_ms']:.1f}ms TTFT | {
                results[category]['avg_tps']:.1f} tok/s")

    return results


def main():
    mgr = get_model_manager()
    models = mgr.list_models()

    if not models:
        console.print("[red]Nenhum modelo encontrado![/red]")
        return

    # Tabela final
    table = Table(title="🏆 LLM Benchmark Results")
    table.add_column("Model/Task", style="bold")
    table.add_column("Latency (ms)", justify="right")
    table.add_column("Speed (tok/s)", justify="right")

    for model in models:
        res = benchmark_model(model.name, TEST_PROMPTS)
        if res:
            table.add_row(f"[bold]{model.name}[/bold]", "", "")
            for cat, metrics in res.items():
                table.add_row(
                    f"  {cat}",
                    f"{metrics['avg_latency_ms']:.1f}",
                    f"{metrics['avg_tps']:.1f}"
                )
            table.add_section()

    console.print(table)


if __name__ == "__main__":
    main()
