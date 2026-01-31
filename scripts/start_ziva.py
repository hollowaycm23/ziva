#!/usr/bin/env python3
import sys
import os
import time
import subprocess
import logging
import shutil
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.theme import Theme

# 1. Configurar PYTHONPATH para a raiz do projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
os.environ["PYTHONPATH"] = PROJECT_ROOT

# 2. Console Rich
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "ziva": "bold magenta",
})
console = Console(theme=custom_theme)

# 3. Auto-switchTo Virtualenv


def is_venv():
    return sys.prefix != sys.base_prefix or 'VIRTUAL_ENV' in os.environ


def is_env_functional(python_exe):
    """Verifica se o python_exe tem as dependências mínimas."""
    try:
        # Tenta importar rich e requests via subprocess para não afetar o
        # processo atual
        subprocess.run([python_exe,
                        "-c",
                        "import rich, requests"],
                       check=True,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        return True
    except BaseException:
        return False


if not is_venv():
    # Tenta encontrar o venv local ou o global do usuário
    possible_venvs = [
        os.path.join(PROJECT_ROOT, "venv/bin/python3"),
        os.path.join(PROJECT_ROOT, "agent_venv/bin/python3"),
        os.path.expanduser("~/.venv/bin/python3")
    ]

    for venv_path in possible_venvs:
        if os.path.exists(venv_path) and is_env_functional(venv_path):
            console.print(
                f"[info]🔄 Reiniciando via Virtualenv:[/info] [bold white]{venv_path}[/bold white]")
            os.execv(venv_path, [venv_path] + sys.argv)

    console.print(
        "[warning]⚠️ Aviso: Nenhum ambiente virtual FUNCIONAL detectado. Usando Python padrão.[/warning]")

# Configurar diretório de logs
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "ziva_system.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [ZIVA] - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE)
    ]
)
logger = logging.getLogger("Launcher")


def is_port_in_use(port):
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except BaseException:
        return False


def find_available_port(start_port, max_attempts=10):
    import socket
    port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(port):
            return port
        port += 1
    return port
    return start_port


def kill_port_owner(port):
    """Tenta derrubar o processo que está usando a porta usando timeout lsof e kill -9."""
    helper_path = f"{PROJECT_ROOT}/scripts/sudo_helper.sh"
    try:
        # Obter PIDs usando lsof com timeout para evitar hang
        cmd = ["timeout", "2s", "lsof", "-t", f"-i:{port}"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False)
        pids = result.stdout.strip().split("\n")

        for pid in pids:
            if pid and pid.isdigit():
                logger.info(f"Matando processo {pid} na porta {port}...")
                if os.path.exists(helper_path):
                    subprocess.run([helper_path,
                                    "kill",
                                    "-9",
                                    pid],
                                   stderr=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL,
                                   check=False,
                                   timeout=5)
                else:
                    subprocess.run(["kill",
                                    "-9",
                                    pid],
                                   stderr=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL,
                                   check=False,
                                   timeout=5)

        if pids and pids[0]:
            time.sleep(1)
    except Exception as e:
        logger.debug(f"Erro ao limpar porta {port}: {e}")


def start_ollama():
    port = 11434
    if is_port_in_use(port):
        console.print(
            f"[warning]⚠️ Porta {port} (Ollama) em uso. Tentando limpar...[/warning]")
        kill_port_owner(port)

    try:
        subprocess.Popen(["ollama", "serve"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Iniciando..."
    except Exception as e:
        return f"Erro: {e}"


def start_kiwix(port=8081):
    if is_port_in_use(port):
        console.print(
            f"[warning]⚠️ Porta {port} (Kiwix) em uso. Tentando limpar...[/warning]")
        kill_port_owner(port)

    kiwix_dir = f"{PROJECT_ROOT}/data/kiwix"
    kiwix_bin = f"{PROJECT_ROOT}/scripts/kiwix-serve"

    # Dynamic ZIM Loading
    import glob
    zim_files = glob.glob(f"{kiwix_dir}/*.zim")

    if not zim_files or not os.path.exists(kiwix_bin):
        return "Indisponível"

    # Se ainda em uso após kill, buscar outra
    final_port = find_available_port(port)

    cmd = [kiwix_bin, "--port", str(final_port)] + zim_files
    # Add flag to skip invalid ZIMs to be safe
    cmd.append("--skipInvalid")

    console.print(
        f"[info]📚 Kiwix carregando {
            len(zim_files)} arquivos ZIM...[/info]")
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return "Iniciando...", final_port


def create_status_table(services):
    table = Table(
        title="[bold magenta]Ziva Subsystems Health[/bold magenta]",
        border_style="magenta",
        expand=True)
    table.add_column("Serviço", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Porta", justify="center")

    for name, status, port in services:
        color = "green" if "Online" in status else "yellow" if "Iniciando" in status else "red"
        table.add_row(name, f"[{color}]{status}[/{color}]", str(port))
    return table


def main():
    console.print(
        Panel.fit(
            "[bold magenta]ZIVA AI SYSTEM[/bold magenta]\n[italic white]Unified Orchestrator v1.2[/italic white]",
            border_style="magenta"))

    # Limpeza Geral (Portas críticas)
    # critical_ports = [8000, 9000, 8080, 8081, 11434]
    critical_ports = [8000, 9000, 8080, 8081]
    console.print(
        "[info]🔍 Limpando recursos de rede e matando processos fantasmas...[/info]")
    for p in critical_ports:
        kill_port_owner(p)
    time.sleep(1)

    # Iniciar Serviços Background
    console.print("[info]⚙️ Iniciando serviços de background...[/info]")
    # LM Studio é externo (não gerenciado por este script)
    ollama_status = "External (LM Studio)"
    kiwix_res = start_kiwix(8081)
    kiwix_status = kiwix_res[0] if isinstance(kiwix_res, tuple) else kiwix_res
    kiwix_port = kiwix_res[1] if isinstance(kiwix_res, tuple) else 8081

    # Docker Check - Iniciar TODOS os serviços (Qdrant, OpenWebUI, SearxNG, Kiwix)
    docker_status = "Iniciando..." if shutil.which("docker") else "Offline (Docker ausente)"
    
    if docker_status == "Iniciando...":
        console.print("[info]🐳 Iniciando Stack Docker Completa (Qdrant + OpenWebUI + SearxNG + Kiwix)...[/info]")
        compose_path = f"{PROJECT_ROOT}/docker-compose.yml"
        
        if os.path.exists(compose_path):
            # Criar rede se não existir
            subprocess.run(
                ["docker", "network", "create", "ziva-net"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
            
            # Parar containers antigos
            subprocess.run(
                ["docker", "compose", "-f", compose_path, "down"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
                check=False
            )
            
            # Iniciar todos os serviços
            subprocess.Popen(
                ["docker", "compose", "-f", compose_path, "up", "-d"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            docker_status = "Online"
            console.print("[success]✅ Stack Docker iniciada: Qdrant, OpenWebUI, SearxNG, Kiwix[/success]")
        else:
            docker_status = "Erro (docker-compose.yml ausente)"
            console.print(f"[error]❌ Arquivo não encontrado: {compose_path}[/error]")

    # Importações Pesadas (Agente)
    console.print(
        "[ziva]🧠 Carregando Cérebro do Agente e Preparando API...[/ziva]")
    import threading
    import uvicorn
    from api.server import app as fastapi_app
    from core.binary_server import BinaryServer
    from agent.ziva import ZivaAgent
    agent = ZivaAgent()

    # Porta da API (Tenta 8000, se falhar busca outra)
    api_port = find_available_port(8000)
    bin_port = find_available_port(9000)

    # Iniciar Threads
    bin_server = BinaryServer(port=bin_port)
    t_bin = threading.Thread(target=bin_server.start, daemon=True)
    t_bin.start()

    import api.server
    api.server.agent = agent
    t_api = threading.Thread(
        target=uvicorn.run,
        args=(fastapi_app,),
        kwargs={"host": "0.0.0.0", "port": api_port, "log_level": "critical"},
        daemon=True
    )
    t_api.start()

    # Iniciar Message Daemon (P2P Sync)
    console.print("[ziva]📨 Iniciando Message Daemon (P2P Sync)...[/ziva]")
    from network.daemon import MessageDaemon
    msg_daemon = MessageDaemon()

    t_daemon = threading.Thread(target=msg_daemon.run, daemon=True)
    t_daemon.start()

    # Iniciar Overseer (Health Monitor)
    console.print("[ziva]👁️ Iniciando Overseer (Monitoramento Interno)...[/ziva]")
    from scripts.start_overseer import run_background_monitor
    t_overseer = threading.Thread(
        target=run_background_monitor,
        args=(60,), # Check every 60s
        daemon=True
    )
    t_overseer.start()

    time.sleep(2)

    # Mostrar Tabela Final de Status
    p2p_status = "Online" if hasattr(
        agent, 'p2p_node') and agent.p2p_node else "Offline"
    gabrielle_status = "Connected" if hasattr(
        agent,
        'gabrielle') and agent.gabrielle and agent.gabrielle.is_connected else "Scanning..."

    services = [
        ("LM Studio (Backend LLM)", "External", "100.104.242.35:1234"),
        ("Qdrant (Vector DB)", "Online" if is_port_in_use(6333) else "Starting", 6333),
        ("Kiwix (Offline Knowledge)", "Online" if is_port_in_use(kiwix_port) else kiwix_status, kiwix_port),
        ("SearxNG (Web Search)", "Online" if is_port_in_use(8080) else docker_status, 8080),
        ("Ziva Browser (Playwright)", "Online" if is_port_in_use(3001) else "Starting", 3001),
        ("OpenWebUI (Interface)", "Online" if is_port_in_use(3000) else "Starting", 3000),
        ("Ziva API (Rest)", "Online", api_port),
        (f"P2P Node ({p2p_status})", f"{gabrielle_status}", bin_port),
        ("Message Daemon (Sync)", "Active", "Background"),
        ("Overseer (Health)", "Active", "Background")
    ]
    console.print(create_status_table(services))

    console.print("\n[success]✅ SISTEMA UNIFICADO OPERACIONAL[/success]")
    console.print("[dim]Pressione Ctrl+C para encerrar o orquestrador[/dim]\n")

    try:
        agent.run_loop()
    except KeyboardInterrupt:
        console.print(
            "\n[warning]⚠️ Encerrando Ziva AI... Até breve![/warning]")


if __name__ == "__main__":
    main()
