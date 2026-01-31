
from core.database import DatabaseManager
import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def register_peer(node_id, public_key, trust_level=100):
    print(f"🔐 Registrando Peer: {node_id}...")
    db = DatabaseManager()
    db.add_trusted_peer(node_id, public_key, trust_level)
    print(f"✅ Peer {node_id} adicionado com nível de confiança {trust_level}!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Registrar nó P2P confiável")
    parser.add_argument(
        "--node",
        required=True,
        help="ID do Nó (ex: ziva-node-07)")
    parser.add_argument("--key", required=True, help="Chave Pública/Trust Key")
    parser.add_argument("--trust", type=int, default=100,
                        help="Nível de Confiança (0-100)")

    args = parser.parse_args()
    register_peer(args.node, args.key, args.trust)
