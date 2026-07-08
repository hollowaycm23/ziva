"""
P2P Multi-Agent Configuration.
"""

import os

# P2P Server
P2P_HOST = os.getenv("P2P_HOST", "0.0.0.0")
P2P_PORT = int(os.getenv("P2P_PORT", "9876"))

# Discovery
P2P_DISCOVERY_INTERVAL = int(os.getenv("P2P_DISCOVERY_INTERVAL", "30"))
P2P_PEER_TIMEOUT = int(os.getenv("P2P_PEER_TIMEOUT", "120"))

# Known peers (comma-separated IP:port)
P2P_KNOWN_PEERS = os.getenv("P2P_KNOWN_PEERS", "")

# Sync
P2P_SYNC_INTERVAL = int(os.getenv("P2P_SYNC_INTERVAL", "300"))
P2P_SYNC_BATCH_SIZE = int(os.getenv("P2P_SYNC_BATCH_SIZE", "50"))


def parse_known_peers() -> list:
    """Parse P2P_KNOWN_PEERS env var into list of (host, port) tuples."""
    peers = []
    raw = P2P_KNOWN_PEERS
    if raw:
        for entry in raw.split(","):
            entry = entry.strip()
            if ":" in entry:
                host, port_str = entry.rsplit(":", 1)
                try:
                    port = int(port_str)
                    peers.append((host, port))
                except ValueError:
                    continue
    return peers
