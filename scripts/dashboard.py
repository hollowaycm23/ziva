#!/home/holloway/ziva/agent_venv/bin/python3
"""
Ziva Monitoring Dashboard (TUI)
Monitora serviços, memória e recursos do sistema em tempo real.
"""

import os as _os
from datetime import datetime
import socket
import requests
import psutil
import sys
import os
import time

# --- Auto-switch to Virtual Environment ---


def check_venv():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_python = os.path.join(project_root, "agent_venv", "bin", "python3")

    # Se não estivermos usando o python do venv e ele existir, re-executamos
    if os.path.exists(venv_python) and os.path.abspath(
            sys.executable) != os.path.abspath(venv_python):
        os.execv(venv_python, [venv_python] + sys.argv)


check_venv()
# ------------------------------------------


try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    from rich import box
    from qdrant_client import QdrantClient
    import pynvml  # GPU Telemetry
except ImportError as e:
    import sys
    print(f"\n❌ Erro de Dependência: {e}")
    print("⚠️  Por favor, execute usando o ambiente virtual configurado:")
    print("   source ../agent_venv/bin/activate && python3 dashboard.py")
    print("   OU")
    print("   ../agent_venv/bin/python3 dashboard.py\n")
    sys.exit(1)

# Configurações
# Configurações
SERVICES = {
    "API Backend": ("127.0.0.1", 8000),
    "P2P Node": ("127.0.0.1", 9000),
    "Qdrant DB": ("127.0.0.1", 6333),
    "Ollama LLM": ("127.0.0.1", 11434),
    "Kiwix Server": ("127.0.0.1", 8081),
    "SearXNG": ("127.0.0.1", 8080)
}

QDRANT_URL = "http://127.0.0.1:6333"
COLLECTION_NAME = "ziva_knowledge"

# Paths
PROJECT_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
INBOX_DIR = _os.path.join(PROJECT_ROOT, "inbox")
OUTBOX_DIR = _os.path.join(PROJECT_ROOT, "outbox")
NODES_FILE = _os.path.join(PROJECT_ROOT, "data", "nodes.json")
DB_FILE = _os.path.join(PROJECT_ROOT, "data", "ziva.db")

console = Console()


class ZivaDashboard:
    def __init__(self):
        self.qdrant = QdrantClient(url=QDRANT_URL)
        self.start_time = time.time()
        self.layout = self.make_layout()

        # Initialize NVIDIA NVML
        self.gpu_available = False
        try:
            pynvml.nvmlInit()
            self.gpu_available = True
        except Exception:
            self.gpu_available = False

    def make_layout(self) -> Layout:
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="center", ratio=1),
            Layout(name="right", ratio=1)
        )
        layout["left"].split(
            Layout(name="services", ratio=1),
            Layout(name="memory", ratio=1)
        )
        layout["center"].split(
            Layout(name="network", ratio=1),
            Layout(name="queue", ratio=1)
        )
        layout["right"].split(
            Layout(name="resources", ratio=1),
            Layout(name="activity", ratio=1)
        )
        return layout

    def check_port(self, host, port):
        try:
            with socket.create_connection((host, port), timeout=0.1):
                return True
        except (socket.timeout, ConnectionRefusedError):
            return False

    def get_services_panel(self) -> Panel:
        table = Table(box=box.SIMPLE, expand=True)
        table.add_column("Serviço", style="cyan")
        table.add_column("Porta", style="magenta")
        table.add_column("Status", justify="right")

        all_up = True
        for name, (host, port) in SERVICES.items():
            is_up = self.check_port(host, port)
            status = "🟢 ON" if is_up else "🔴 OFF"
            style = "green" if is_up else "red"
            if not is_up:
                all_up = False
            table.add_row(name, str(port), Text(status, style=style))

        border_style = "green" if all_up else "yellow"
        return Panel(
            table,
            title="[b]Status dos Serviços[/b]",
            border_style=border_style)

    def get_memory_panel(self) -> Panel:
        try:
            # Get all collections
            collections_response = self.qdrant.get_collections()
            collections = collections_response.collections

            if not collections:
                content = "[yellow]Nenhuma coleção encontrada no Qdrant[/yellow]"
            else:
                table = Table(box=box.SIMPLE, expand=True, show_header=True)
                table.add_column("Coleção", style="cyan")
                table.add_column("Pontos", justify="right", style="green")

                total_points = 0
                for collection in collections:
                    try:
                        info = self.qdrant.get_collection(collection.name)
                        count = info.points_count
                        total_points += count
                        table.add_row(collection.name, str(count))
                    except BaseException:
                        table.add_row(collection.name, "[dim]?[/dim]")

                # Add separator and total
                table.add_row("─" * 20, "─" * 10)
                table.add_row(
                    "[bold]TOTAL[/bold]",
                    f"[bold]{total_points}[/bold]")

                return Panel(
                    table,
                    title="[b]Memória Neural (RAG)[/b]",
                    border_style="blue")

        except Exception as e:
            content = f"[red]Erro ao conectar ao Qdrant:[/red]\n{
                str(e)[
                    :50]}..."
            return Panel(
                content.strip(),
                title="[b]Memória Neural (RAG)[/b]",
                border_style="red")

    def get_resources_panel(self) -> Panel:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory()

        # GPU Telemetry
        gpu_info = []
        if self.gpu_available:
            try:
                device_count = pynvml.nvmlDeviceGetCount()
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle)
                    # Handle bytes vs str return from pynvml
                    if isinstance(name, bytes):
                        name = name.decode('utf-8')

                    mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    temp = pynvml.nvmlDeviceGetTemperature(
                        handle, pynvml.NVML_TEMPERATURE_GPU)

                    used_gb = mem.used / (1024**3)
                    total_gb = mem.total / (1024**3)
                    gpu_info.append({
                        "id": i,
                        "name": name,
                        "temp": temp,
                        "vram_used": used_gb,
                        "vram_total": total_gb,
                        "gpu_util": util.gpu
                    })
            except Exception as e:
                gpu_info = []

        table = Table(box=box.SIMPLE, expand=True)
        table.add_column("Recurso")
        table.add_column("Uso", justify="right")

        cpu_color = "green" if cpu < 50 else "yellow" if cpu < 80 else "red"
        ram_color = "green" if ram.percent < 60 else "yellow" if ram.percent < 85 else "red"

        table.add_row("CPU", Text(f"{cpu}%", style=cpu_color))
        table.add_row("RAM", Text(
            f"{ram.percent}% ({ram.used // (1024**3)}GB used)", style=ram_color))

        # Add GPU Rows
        if gpu_info:
            for gpu in gpu_info:
                temp_color = "green" if gpu["temp"] < 70 else "yellow" if gpu["temp"] < 85 else "red"
                util_color = "green" if gpu["gpu_util"] < 60 else "yellow" if gpu["gpu_util"] < 90 else "red"

                table.add_row(
                    f"GPU {gpu['id']}",
                    Text(f"{gpu['gpu_util']}% | {gpu['temp']}°C",
                         style=util_color)
                )
                table.add_row(
                    "VRAM",
                    Text(
                        f"{gpu['vram_used']:.1f}/{gpu['vram_total']:.1f} GB", style="cyan")
                )
        else:
            table.add_row("GPU", Text("N/A", style="dim"))

        uptime = time.time() - self.start_time
        hours, rem = divmod(uptime, 3600)
        minutes, seconds = divmod(rem, 60)
        table.add_row(
            "Uptime Dashboard", f"{
                int(hours):02}:{
                int(minutes):02}:{
                int(seconds):02}")

        return Panel(
            table, title="[b]Recursos do Sistema[/b]", border_style="magenta")

    def get_logs(self, num_lines=10):
        # Resolve log path relative to project root (assuming script is in scripts/)
        # Or just use absolute path since we know the structure
        import os
        project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        log_file = os.path.join(project_root, "logs", "ziva_system.log")

        try:
            with open(log_file, "r") as f:
                # Ler últimas N linhas de forma eficiente
                lines = f.readlines()
                return [l.strip() for l in lines[-num_lines:]]
        except FileNotFoundError:
            return [
                "[yellow]Aguardando logs (arquivo não encontrado)...[/yellow]"]
        except Exception as e:
            return [f"[red]Erro ao ler logs: {e}[/red]"]

    def get_activity_panel(self) -> Panel:
        logs = self.get_logs(15)
        content = "\n".join(
            logs) if logs else "[dim]Sem atividade recente[/dim]"
        return Panel(
            content,
            title="[b]Atividade do Sistema (Real-time)[/b]",
            border_style="white")

    def get_network_panel(self) -> Panel:
        """Mostra status dos nós da rede P2P."""
        import json

        table = Table(box=box.SIMPLE, expand=True, show_header=True)
        table.add_column("Nó", style="cyan")
        table.add_column("Role", style="yellow")
        table.add_column("Status", justify="right")

        try:
            with open(NODES_FILE, 'r') as f:
                nodes = json.load(f)

            for node_id, node_info in nodes.items():
                name = node_info.get('name', node_id)
                role = node_info.get('role', 'unknown')
                status = node_info.get('status', 'unknown')

                # Active Check (Real-time)
                ips = node_info.get('ips', [])
                is_reachable = False

                # Special case for local node (optional, but good for
                # self-check)
                if node_id == "node07" or node_info.get(
                        "role") == "orchestrator":
                    if self.check_port("127.0.0.1", 9000):
                        is_reachable = True

                if not is_reachable and ips:
                    for ip in ips:
                        if self.check_port(ip, 9000):
                            is_reachable = True
                            break

                # Color coding based on Real Connectivity
                if is_reachable:
                    status_text = Text("🟢 Active", style="green")
                else:
                    # If it was marked active in JSON but is unreachable, show
                    # as Offline
                    status_text = Text("🔴 Offline", style="red")

                table.add_row(name, role.capitalize(), status_text)
        except Exception as e:
            return Panel(f"[red]Erro ao ler nodes.json: {str(e)[:50]}[/red]",
                         title="[b]Network Nodes[/b]", border_style="red")

        return Panel(
            table, title="[b]Network Nodes (P2P)[/b]", border_style="cyan")

    def get_queue_panel(self) -> Panel:
        """Mostra estatísticas da fila de jobs e mensagens."""
        import sqlite3

        table = Table(box=box.SIMPLE, expand=True)
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right", style="yellow")

        try:
            # Contar mensagens inbox/outbox
            inbox_count = len([f for f in os.listdir(INBOX_DIR) if f.endswith(
                '.json')]) if os.path.exists(INBOX_DIR) else 0
            outbox_count = len([f for f in os.listdir(OUTBOX_DIR) if f.endswith(
                '.json')]) if os.path.exists(OUTBOX_DIR) else 0

            # Contar jobs no SQLite
            # Use Read-Only mode and timeout to prevent locking ziva.db
            try:
                db_uri = f"file:{DB_FILE}?mode=ro"
                conn = sqlite3.connect(db_uri, uri=True, timeout=20)
            except sqlite3.OperationalError:
                # Fallback if RO not supported or file locked hard
                conn = sqlite3.connect(DB_FILE, timeout=20)

            cursor = conn.cursor()

            cursor.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
            job_stats = dict(cursor.fetchall())

            cursor.execute("SELECT COUNT(*) FROM training_data")
            training_count = cursor.fetchone()[0]

            conn.close()

            # Adicionar linhas
            table.add_row("📥 Inbox (Pendente)", str(inbox_count))
            table.add_row("📤 Outbox (Aguardando)", str(outbox_count))
            table.add_row("─" * 20, "─" * 10)

            for status in ['pending', 'processing', 'completed', 'failed']:
                count = job_stats.get(status, 0)
                if count > 0:
                    emoji = {
                        "pending": "⏳",
                        "processing": "⚙️",
                        "completed": "✅",
                        "failed": "❌"}.get(
                        status,
                        "")
                    table.add_row(
                        f"{emoji} Jobs {
                            status.capitalize()}",
                        str(count))

            table.add_row("─" * 20, "─" * 10)
            table.add_row("🧠 Training Data", str(training_count))

        except Exception as e:
            return Panel(f"[red]Erro: {str(e)[:50]}[/red]",
                         title="[b]Queue & Sync[/b]", border_style="red")

        border_color = "yellow" if outbox_count > 100 else "green"
        return Panel(
            table,
            title="[b]Queue & Sync Status[/b]",
            border_style=border_color)

    def get_alerts_panel(self) -> Panel:
        alerts = []
        # Check services
        for name, (host, port) in SERVICES.items():
            if not self.check_port(host, port):
                alerts.append(
                    f"[bold red]❌ ALERTA: {name} ({port}) está OFFLINE![/bold red]")

        # Check resources (thresholds simples)
        if psutil.cpu_percent() > 90:
            alerts.append(
                "[bold red]❌ ALERTA: Alta Carga de CPU (>90%)![/bold red]")

        mem = psutil.virtual_memory()
        if mem.percent > 90:
            alerts.append(
                "[bold red]❌ ALERTA: Memória Crítica (>90%)![/bold red]")

        if not alerts:
            return Panel(
                "[green]✅ Todos os sistemas operacionais. Sem alertas.[/green]",
                title="[b]Alertas do Sistema[/b]",
                border_style="green")

        return Panel(
            "\n".join(alerts),
            title="[bold red]⚠️  ALERTAS ATIVOS[/bold red]",
            border_style="bold red")

    def update(self):
        self.layout["header"].update(
            Panel(
                Text(
                    "ZIVA - ADVANCED AGENTIC SYSTEM MONITOR",
                    justify="center",
                    style="bold white on blue"),
                box=box.HEAVY))

        self.layout["left"]["services"].update(self.get_services_panel())
        self.layout["left"]["memory"].update(self.get_memory_panel())

        self.layout["center"]["network"].update(self.get_network_panel())
        self.layout["center"]["queue"].update(self.get_queue_panel())

        self.layout["right"]["resources"].update(self.get_resources_panel())
        self.layout["right"]["activity"].update(self.get_activity_panel())

        alerts_panel = self.get_alerts_panel()
        if "❌" in str(alerts_panel.renderable):
            self.layout["footer"].update(alerts_panel)
        else:
            self.layout["footer"].update(
                Panel(
                    Text(
                        "Status Normal | Pressione Ctrl+C para sair",
                        justify="center",
                        style="dim"),
                    box=box.SIMPLE))

    def run(self):
        with Live(self.layout, refresh_per_second=1, screen=True):
            while True:
                self.update()
                time.sleep(2)


if __name__ == "__main__":
    try:
        dashboard = ZivaDashboard()
        dashboard.run()
    except KeyboardInterrupt:
        print("\nMonitoramento encerrado.")
