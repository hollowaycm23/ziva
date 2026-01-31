import json
import logging
from pathlib import Path

logger = logging.getLogger("NodeRegistry")

REGISTRY_FILE = Path("/home/holloway/ziva/data/nodes.json")


class NodeRegistry:
    """
    Mantém o registro dos nós conhecidos na bateria/rede e suas capacidades.
    """

    def __init__(self):
        self.nodes = self._load_registry()

    def _load_registry(self):
        if REGISTRY_FILE.exists():
            try:
                with open(REGISTRY_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar registro de nós: {e}")

        return {
            "node07": {
                "id": "node07",
                "name": "Ziva",
                "role": "orchestrator",
                "capabilities": [
                    "inference", "rag", "coding", "orchestration"],
                "status": "active"},
            "falcon": {
                "id": "falcon",
                "name": "Gabrielle",
                "role": "worker",
                "capabilities": [
                    "inference", "heavy_computation"],
                "status": "active"}}

    def save_registry(self):
        try:
            with open(REGISTRY_FILE, 'w') as f:
                json.dump(self.nodes, f, indent=4)
        except Exception as e:
            logger.error(f"Erro ao salvar registro: {e}")

    def get_node(self, node_id):
        return self.nodes.get(node_id)

    def list_workers(self):
        return [n for n in self.nodes.values() if n.get("role") == "worker"]

    def scan_tailscale_network(self):
        """
        Executa 'tailscale status --json' para descobrir nós ativos na rede.
        """
        import subprocess
        import shutil

        tailscale_cmd = shutil.which("tailscale")
        if not tailscale_cmd:
            logger.warning(
                "Binário 'tailscale' não encontrado. Discovery desativado.")
            return self.nodes

        try:
            cmd = [tailscale_cmd, "status", "--json"]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                data = json.loads(result.stdout)
                peers = data.get("Peer", {})

                updates = 0
                for peer_id, info in peers.items():
                    hostname = info.get("HostName")
                    ip_list = info.get("TailscaleIPs", [])
                    online = info.get("Online", False)
                    cur_addr = info.get("CurAddr", "")
                    physical_ip = None
                    if cur_addr:
                        physical_ip = cur_addr.split(":")[0]

                    node_key = hostname.lower()

                    if node_key not in self.nodes:
                        logger.info(
                            f"Novo nó descoberto via Tailscale: {hostname}")
                        self.nodes[node_key] = {
                            "id": node_key,
                            "name": hostname,
                            "role": "worker",
                            "capabilities": ["inference"],
                            "ips": ip_list,
                            "physical_ip": physical_ip,
                            "status": "active" if online else "offline"
                        }
                        updates += 1
                    else:
                        node = self.nodes[node_key]
                        old_status = node.get("status")
                        new_status = "active" if online else "offline"

                        changed = False
                        if old_status != new_status:
                            node["status"] = new_status
                            changed = True

                        if physical_ip and node.get(
                                "physical_ip") != physical_ip:
                            node["physical_ip"] = physical_ip
                            changed = True

                        if changed:
                            updates += 1

                if updates > 0:
                    self.save_registry()
                    logger.info(
                        f"Registro de nós atualizado: {updates} alterações.")

            else:
                logger.error(
                    f"Erro ao executar tailscale status: {result.stderr}")

        except Exception as e:
            logger.error(f"Falha no discovery Tailscale: {e}")

        return self.nodes

    def update_status(self, node_id, status):
        if node_id in self.nodes:
            self.nodes[node_id]["status"] = status
            self.save_registry()
            return True
        return False