#!/usr/bin/env python3
"""
Worker Node Startup Script
Minimal version for nodes that only run P2P Binary Server
"""
import sys
import os
import json
import threading
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_config():
    config_path = PROJECT_ROOT / "config" / "node_minimal.json"
    if not config_path.exists():
        print(f"❌ Config not found: {config_path}")
        sys.exit(1)

    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    config = load_config()
    node_name = config.get("node_name", "worker")
    p2p_port = config.get("p2p_port", 9000)
    auth_key = config.get("p2p_auth_key", "ziva-trust-key")

    print(f"🚀 Starting Ziva Worker Node: {node_name}")
    print(f"   P2P Port: {p2p_port}")
    print(f"   Auth Key: {'*' * len(auth_key)}")

    # Import and start Binary Server
    try:
        from core.binary_server import BinaryServer

        # Configure auth key
        server = BinaryServer(port=p2p_port, auth_key=auth_key.encode('utf-8'))

        print(f"✅ Binary Server ready on port {p2p_port}")
        print(f"🔗 Master Node: {config.get('master_node', 'N/A')}")
        print("\n⏸️  Press Ctrl+C to stop...\n")

        # Start in main thread (blocking)
        server.start()

    except KeyboardInterrupt:
        print("\n👋 Shutting down worker node...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
