#!/usr/bin/env python3
import json
import os
import argparse
import sys
from pathlib import Path

PEERS_FILE = "/home/holloway/ziva/config/peers.json"


def load_peers():
    if not os.path.exists(PEERS_FILE):
        return {"peers": {}}
    try:
        with open(PEERS_FILE, 'r') as f:
            return json.load(f)
    except BaseException:
        return {"peers": {}}


def save_peers(data):
    with open(PEERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def add_peer(name, host, key, port=9000):
    data = load_peers()

    # Store by Host (IP/Domain) for easy lookup
    data["peers"][host] = {
        "name": name,
        "host": host,
        "port": port,
        "key": key
    }

    save_peers(data)
    print(f"✅ Friend Added: {name} ({host}:{port})")


def list_peers():
    data = load_peers()
    peers = data.get("peers", {})
    if not peers:
        print("No peers configured.")
        return

    print(f"{'NAME':<15} {'HOST':<20} {'PORT':<6}")
    print("-" * 42)
    for host, p in peers.items():
        print(f"{p['name']:<15} {p['host']:<20} {p['port']:<6}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ziva Peer Manager")
    subparsers = parser.add_subparsers(dest="command")

    # Add Command
    add = subparsers.add_parser("add", help="Add a new trusted peer")
    add.add_argument(
        "--name",
        required=True,
        help="Friendly name (e.g. Alice)")
    add.add_argument("--host", required=True, help="IP or Tailscale Hostname")
    add.add_argument("--key", required=True, help="Shared Secret Key (PSK)")
    add.add_argument(
        "--port",
        type=int,
        default=9000,
        help="P2P Port (default 9000)")

    # List Command
    lst = subparsers.add_parser("list", help="List known peers")

    args = parser.parse_args()

    if args.command == "add":
        add_peer(args.name, args.host, args.key, args.port)
    elif args.command == "list":
        list_peers()
    else:
        parser.print_help()
