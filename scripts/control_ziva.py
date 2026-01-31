#!/usr/bin/env python3
import sys
import argparse
import logging
import json
from network.ziva_mgr import ZivaManager

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ZivaControl")

def main():
    parser = argparse.ArgumentParser(description="Ziva Control CLI")
    subparsers = parser.add_subparsers(dest="command", help="Comando a executar")

    # Start
    subparsers.add_parser("start", help="Inicia todos os serviços")
    
    # Stop
    subparsers.add_parser("stop", help="Para todos os serviços")
    
    # Restart
    subparsers.add_parser("restart", help="Reinicia todos os serviços")
    
    # Status
    subparsers.add_parser("status", help="Exibe status dos serviços")
    
    # Logs
    logs_parser = subparsers.add_parser("logs", help="Exibe logs de um serviço")
    logs_parser.add_argument("service", nargs="?", default="ziva-core", help="Nome do serviço (default: ziva-core)")
    logs_parser.add_argument("--lines", type=int, default=50, help="Número de linhas (default: 50)")

    args = parser.parse_args()
    
    mgr = ZivaManager()

    if args.command == "start":
        mgr.start_services()
    elif args.command == "stop":
        mgr.stop_services()
    elif args.command == "restart":
        mgr.restart_services()
    elif args.command == "status":
        status = mgr.check_health()
        print(json.dumps(status, indent=2))
    elif args.command == "logs":
        logs = mgr.get_logs(service=args.service, lines=args.lines)
        if logs["success"]:
            print(logs["stdout"])
        else:
            print(f"Erro ao obter logs: {logs['stderr']}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
