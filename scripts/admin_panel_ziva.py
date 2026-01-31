#!/usr/bin/env python3
"""
Ziva Admin Panel
Painel de controle CLI para gerenciar os serviços do sistema Ziva via terminal.
"""

import os
import sys
import subprocess
import time


# Definição de Cores
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Caminhos
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
START_SCRIPT = os.path.join(PROJECT_ROOT, "start.sh")
STOP_SCRIPT = os.path.join(PROJECT_ROOT, "stop.sh")
RESTART_SCRIPT = os.path.join(PROJECT_ROOT, "restart.sh")


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    clear_screen()
    print(f"{CYAN}{BOLD}╔════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}{BOLD}║                ZIVA AI SYSTEM - ADMIN PANEL                ║{RESET}")
    print(f"{CYAN}{BOLD}╚════════════════════════════════════════════════════════════╝{RESET}")
    print(f"{CYAN}Projeto: {PROJECT_ROOT}{RESET}")
    print("")


def check_service_status(process_name, display_name):
    """Verifica se um processo está rodando via pgrep"""
    try:
        subprocess.check_output(["pgrep", "-f", process_name])
        print(f"  {GREEN}●{RESET} {display_name:<20} {GREEN}RODANDO{RESET}")
        return True
    except subprocess.CalledProcessError:
        print(f"  {RED}●{RESET} {display_name:<20} {RED}PARADO{RESET}")
        return False


def check_docker_status(container_name, display_name):
    """Verifica se um container docker está rodando"""
    try:
        output = subprocess.check_output(["docker",
                                          "ps",
                                          "--filter",
                                          f"name={container_name}",
                                          "--format",
                                          "{{.Names}}"]).decode().strip()
        if container_name in output:
            print(
                f"  {GREEN}●{RESET} {
                    display_name:<20} {GREEN}RODANDO{RESET}")
            return True
        else:
            print(f"  {RED}●{RESET} {display_name:<20} {RED}PARADO{RESET}")
            return False
    except FileNotFoundError:
        print(
            f"  {YELLOW}?{RESET} {
                display_name:<20} {YELLOW}DOCKER NÃO ENCONTRADO{RESET}")
        return False
    except subprocess.CalledProcessError:
        print(
            f"  {RED}●{RESET} {
                display_name:<20} {RED}ERRO AO VERIFICAR{RESET}")
        return False


def show_status():
    print(f"{BOLD}Status dos Serviços:{RESET}")
    check_docker_status("ziva-qdrant", "Qdrant DB")
    check_docker_status("ziva-pihole", "Pi-hole (Ad Block)")
    check_docker_status("searxng", "SearXNG (Search)")
    check_service_status("binary_server", "Servidor P2P")
    check_service_status("uvicorn.*server:app", "FastAPI Server")
    check_service_status("ollama serve", "Ollama")
    print("-" * 60)
    # Check Auto-Sync status
    last_sync = "Nunca"
    if os.path.exists("auto_sync.log"):
        try:
            with open("auto_sync.log", "r") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if "concluído com sucesso" in line:
                        last_sync = line.split(" - ")[0]
                        break
        except:
            pass
    print(f"  {CYAN}🔄 Último Backup:{RESET} {YELLOW}{last_sync}{RESET}")
    print("-" * 60)
    print(f"{CYAN}ℹ️  Pi-hole Web UI: http://localhost:8053/admin{RESET}")
    print(f"{CYAN}ℹ️  FastAPI Docs: http://localhost:8000/docs{RESET}")


def run_script(script_path, description):
    print(f"\n{YELLOW}⏩ {description}...{RESET}")
    try:
        # Usa bash explicitamente para garantir compatibilidade
        subprocess.call(["bash", script_path], cwd=PROJECT_ROOT)
    except KeyboardInterrupt:
        print(f"\n{RED}❌ Operação cancelada pelo usuário.{RESET}")
    except Exception as e:
        print(f"\n{RED}❌ Erro ao executar script: {e}{RESET}")

    input(f"\n{BOLD}Pressione ENTER para continuar...{RESET}")


def start_service(service_name):
    """Inicia um serviço específico"""
    print(f"\n{YELLOW}🚀 Iniciando {service_name}...{RESET}")

    if service_name == "p2p":
        subprocess.Popen(
            ["python3", "-m", "core.binary_server"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "PYTHONPATH": PROJECT_ROOT}
        )
    elif service_name == "api":
        subprocess.Popen(
            ["bash", "-c", "source agent_venv/bin/activate && uvicorn api.server:app --host 0.0.0.0 --port 8000"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True
        )
    elif service_name == "pihole":
        subprocess.call(["docker", "start", "ziva-pihole"])
    elif service_name == "searxng":
        subprocess.call(["docker", "start", "searxng"])
    elif service_name == "qdrant":
        subprocess.call(["docker", "start", "ziva-qdrant"])

    time.sleep(2)
    print(f"{GREEN}✅ Comando de inicialização enviado{RESET}")
    input(f"\n{BOLD}Pressione ENTER para continuar...{RESET}")


def stop_service(service_name):
    """Para um serviço específico"""
    print(f"\n{YELLOW}🛑 Parando {service_name}...{RESET}")

    if service_name == "p2p":
        subprocess.call(["pkill", "-f", "binary_server"])
    elif service_name == "api":
        subprocess.call(["pkill", "-f", "uvicorn.*server:app"])
    elif service_name == "pihole":
        subprocess.call(["docker", "stop", "ziva-pihole"])
    elif service_name == "searxng":
        subprocess.call(["docker", "stop", "searxng"])
    elif service_name == "qdrant":
        subprocess.call(["docker", "stop", "ziva-qdrant"])

    time.sleep(1)
    print(f"{GREEN}✅ Serviço parado{RESET}")
    input(f"\n{BOLD}Pressione ENTER para continuar...{RESET}")


def main_menu():
    while True:
        print_header()
        show_status()

        print(f"{BOLD}Controles Gerais:{RESET}")
        print(f"  {CYAN}[1]{RESET} 🚀 Iniciar Sistema    (Start All)")
        print(f"  {CYAN}[2]{RESET} 🛑 Parar Sistema      (Stop All)")
        print(f"  {CYAN}[3]{RESET} 🔄 Reiniciar Sistema  (Restart All)")
        print(f"  {CYAN}[4]{RESET} 🔍 Atualizar Status")
        print("")
        print(f"{BOLD}Controles Individuais:{RESET}")
        print(f"  {CYAN}[5]{RESET} 🔧 Gerenciar P2P Server")
        print(f"  {CYAN}[6]{RESET} 🔧 Gerenciar FastAPI")
        print(f"  {CYAN}[7]{RESET} 🔧 Gerenciar Pi-hole")
        print(f"  {CYAN}[8]{RESET} 🔧 Gerenciar SearXNG")
        print(f"  {CYAN}[9]{RESET} 🔧 Gerenciar Qdrant")
        print(f"  {CYAN}[S]{RESET} 🔄 Ver Logs de Backup (Auto-Sync)")
        print("")
        print(f"  {CYAN}[0]{RESET} 🚪 Sair")
        print("")

        choice = input(f"{YELLOW}Opção > {RESET}")

        if choice == "1":
            run_script(START_SCRIPT, "Iniciando todos os serviços")
        elif choice == "2":
            run_script(STOP_SCRIPT, "Parando todos os serviços")
        elif choice == "3":
            run_script(RESTART_SCRIPT, "Reiniciando sistema")
        elif choice == "4":
            continue  # Loop will refresh status
        elif choice == "5":
            manage_service("P2P Server", "p2p")
        elif choice == "6":
            manage_service("FastAPI", "api")
        elif choice == "7":
            manage_service("Pi-hole", "pihole")
        elif choice == "8":
            manage_service("SearXNG", "searxng")
        elif choice == "9":
            manage_service("Qdrant DB", "qdrant")
        elif choice.lower() == "s":
            view_logs("auto_sync.log")
        elif choice == "0":
            print(f"\n{GREEN}👋 Até logo!{RESET}")
            sys.exit(0)
        else:
            print(f"\n{RED}❌ Opção inválida!{RESET}")
            time.sleep(1)


def manage_service(service_display_name, service_id):
    """Submenu para gerenciar serviço individual"""
    while True:
        clear_screen()
        print(f"{BOLD}{MAGENTA}Gerenciar: {service_display_name}{RESET}")
        print("-" * 40)
        print(f"  {CYAN}[1]{RESET} 🚀 Iniciar")
        print(f"  {CYAN}[2]{RESET} 🛑 Parar")
        print(f"  {CYAN}[3]{RESET} 🔄 Reiniciar")
        print(f"  {CYAN}[0]{RESET} ⬅️  Voltar")
        print("")

        choice = input(f"{YELLOW}Opção > {RESET}")

        if choice == "1":
            start_service(service_id)
        elif choice == "2":
            stop_service(service_id)
        elif choice == "3":
            stop_service(service_id)
            time.sleep(1)
            start_service(service_id)
        elif choice == "0":
            break
        else:
            print(f"\n{RED}❌ Opção inválida!{RESET}")
            time.sleep(1)


def view_logs(log_file):
    """Exibe as últimas linhas de um log"""
    print(f"\n{BOLD}Logs de {log_file}:{RESET}")
    print("-" * 60)
    if os.path.exists(log_file):
        subprocess.call(["tail", "-n", "20", log_file])
    else:
        print(f"{RED}Arquivo de log não encontrado.{RESET}")
    input(f"\n{BOLD}Pressione ENTER para continuar...{RESET}")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{GREEN}👋 Sair forçado. Até logo!{RESET}")
        sys.exit(0)
