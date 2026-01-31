#!/usr/bin/env python3
import time
import subprocess
import sys
import os
from datetime import datetime


def check_ping(host):
    try:
        # -c 1: count 1, -W 1: timeout 1 sec
        subprocess.check_call(["ping", "-c", "1", "-W", "1", host],
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def check_tailscale(ip):
    try:
        # Check if tailscale sees it as active (not offline)
        output = subprocess.check_output(["tailscale", "status"], text=True)
        for line in output.splitlines():
            if ip in line and "active" in line and "offline" not in line:
                return True
        return False
    except BaseException:
        return False


def alert_online(host):
    print("\n" * 3)
    print("=" * 60)
    print(f"🚀🚀🚀 PEER {host} ESTÁ ONLINE! 🚀🚀🚀")
    print("=" * 60)
    print("\a")  # Bell sound
    # Send system notification if available
    try:
        subprocess.call(["notify-send", "Ziva Monitor",
                        f"Peer {host} is ONLINE!"])
    except BaseException:
        pass


def monitor(host, interval=30):
    print(
        f"🔍 [{
            datetime.now().strftime('%H:%M:%S')}] Iniciando monitoramento de {host}...")
    print(f"   Intervalo: {interval}s")

    while True:
        is_ping = check_ping(host)
        is_ts = check_tailscale(host)

        timestamp = datetime.now().strftime('%H:%M:%S')

        if is_ping or is_ts:
            alert_online(host)
            break
        else:
            sys.stdout.write(
                f"\r⏳ [{timestamp}] Aguardando... (Ping: {
                    'OK' if is_ping else 'NO'}, TS: {
                    'OK' if is_ts else 'NO'})")
            sys.stdout.flush()

        time.sleep(interval)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 monitor_peer.py <IP>")
        sys.exit(1)

    target_ip = sys.argv[1]
    try:
        monitor(target_ip)
    except KeyboardInterrupt:
        print("\n🛑 Monitoramento cancelado.")
