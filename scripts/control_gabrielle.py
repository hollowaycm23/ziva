#!/usr/bin/env python3
from network.gabrielle_mgr import GabrielleManager
import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(
        description="Ziva: Controle Direto da Gabrielle (falcon)")
    parser.add_argument(
        "action",
        choices=[
            "start",
            "cmd",
            "status"],
        help="Ação a executar")
    parser.add_argument("command", nargs="?", help="Comando para ação 'cmd'")

    args = parser.parse_args()
    mgr = GabrielleManager()

    if args.action == "start":
        print("🚀 Iniciando serviços na Gabrielle...")
        results = mgr.start_core_services()
        for svc, res in results.items():
            status = "✅ OK" if res.get("success") else "❌ Falhou"
            print(f" - {svc.capitalize()}: {status}")

    elif args.action == "status":
        print("📊 Status da Gabrielle:")
        health = mgr.check_health()
        for svc, ok in health.items():
            status = "🟢 ONLINE" if ok else "🔴 OFFLINE"
            print(f" - {svc.upper()}: {status}")

    elif args.action == "cmd":
        if not args.command:
            print("❌ Erro: Ação 'cmd' requer um comando.")
            return
        print(f"💻 Executando: {args.command}")
        res = mgr.send_raw_command(args.command)
        if res.get("success"):
            print(res.get("stdout"))
        else:
            print(
                f"Erro ({
                    res.get('exit_code')}): {
                    res.get('stderr') or res.get('error')}")


if __name__ == "__main__":
    main()
