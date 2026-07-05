"""
P2P Collaborative Learning System for Ziva.

Permite que múltiplos nós Ziva (ex: Ziva e Gabrielle) compartilhem
conhecimento e aprendam uns com os outros.
"""

import logging
import json
import time
import requests
from typing import List, Dict, Optional
from pathlib import Path
import socket
import struct
import msgpack  # Added msgpack import
import sys
from core.database import DatabaseManager
from core.training_data_collector import TrainingDataCollector

logger = logging.getLogger("P2PLearning")


class P2PLearningNode:
    """
    Nó de aprendizado P2P.

    Funcionalidades:
    - Compartilhar dados de treinamento
    - Receber conhecimento de outros nós
    - Sincronizar adaptadores LoRA
    - Aprendizado federado
    """

    def __init__(self, node_name: str = "ziva",
                 peers: Optional[List[str]] = None):
        """
        Inicializa nó P2P.

        Args:
            node_name (str): Nome deste nó
            peers (List[str], optional): Lista de peers (URLs)
        """
        self.node_name = node_name
        self.peers = peers or []
        self.db = DatabaseManager()
        self.collector = TrainingDataCollector()

    def share_knowledge(self, peer_url: str, min_quality: float = 0.8) -> bool:
        """
        Compartilha conhecimento com peer.

        Args:
            peer_url (str): URL do peer
            min_quality (float): Qualidade mínima dos dados

        Returns:
            bool: Sucesso
        """
        logger.info(f"Compartilhando conhecimento com {peer_url}")

        # Coletar dados de alta qualidade
        dataset = self.collector.get_training_dataset(min_quality=min_quality)

        if not dataset:
            logger.warning("Nenhum dado para compartilhar")
            return False

        # Enviar para peer
        try:
            response = requests.post(
                f"{peer_url}/api/p2p/receive_knowledge",
                json={
                    "source_node": self.node_name,
                    "dataset": dataset,
                    "timestamp": time.time()
                },
                timeout=30
            )

            if response.status_code == 200:
                logger.info(
                    f"✅ Conhecimento compartilhado: {len(dataset)} exemplos")
                return True
        except Exception as e:
            logger.error(f"Erro ao compartilhar conhecimento: {e}")

        return False

    def receive_knowledge(self, source_node: str, dataset: List[Dict]) -> int:
        """
        Recebe conhecimento de peer.

        Args:
            source_node (str): Nome do nó fonte
            dataset (List[Dict]): Dataset recebido

        Returns:
            int: Número de exemplos adicionados
        """
        logger.info(
            f"Recebendo conhecimento de {source_node}: {len(dataset)} exemplos")

        conn = self.db._get_conn()
        cursor = conn.cursor()

        added = 0
        for example in dataset:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO training_data
                    (instruction, output, task_type, quality_score, success, created_at, session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    example['instruction'],
                    example['output'],
                    example.get('task_type', 'general'),
                    example.get('quality_score', 0.8),
                    True,
                    time.time(),
                    -1  # Marca como recebido de peer
                ))

                if cursor.rowcount > 0:
                    added += 1
            except Exception as e:
                logger.error(f"Erro ao adicionar exemplo: {e}")

        conn.commit()
        conn.close()

        logger.info(f"✅ Conhecimento recebido: {added} novos exemplos")
        return added

    def sync_with_peers(self):
        """Sincroniza conhecimento com todos os peers"""
        for peer in self.peers:
            logger.info(f"Sincronizando com {peer}...")

            # Enviar nosso conhecimento
            self.share_knowledge(peer)

            # Solicitar conhecimento do peer
            try:
                response = requests.get(
                    f"{peer}/api/p2p/get_knowledge",
                    params={"min_quality": 0.8},
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    self.receive_knowledge(
                        source_node=data.get('node_name', 'unknown'),
                        dataset=data.get('dataset', [])
                    )
            except Exception as e:
                logger.error(f"Erro ao receber de {peer}: {e}")

    def share_adapter(self, peer_url: str, task_type: str,
                      adapter_path: str) -> bool:
        """
        Compartilha adaptador LoRA com peer.

        Args:
            peer_url (str): URL do peer
            task_type (str): Tipo de tarefa
            adapter_path (str): Caminho do adaptador

        Returns:
            bool: Sucesso
        """
        logger.info(f"Compartilhando adaptador {task_type} com {peer_url}")

        # Ler arquivos do adaptador
        adapter_files = {}
        for file in Path(adapter_path).glob("*", "*"):
            if file.is_file():
                with open(file, 'rb') as f:
                    adapter_files[file.name] = f.read().hex()

        # Enviar
        try:
            response = requests.post(
                f"{peer_url}/api/p2p/receive_adapter",
                json={
                    "source_node": self.node_name,
                    "task_type": task_type,
                    "files": adapter_files,
                    "timestamp": time.time()
                },
                timeout=60
            )

            if response.status_code == 200:
                logger.info(f"✅ Adaptador compartilhado")
                return True
        except Exception as e:
            logger.error(f"Erro ao compartilhar adaptador: {e}")

        return False

    def collaborative_training(self, task_type: str) -> str:
        """
        Treinamento colaborativo com peers.

        Combina dados de todos os nós para treinar adaptador melhor.

        Args:
            task_type (str): Tipo de tarefa

        Returns:
            str: Caminho do adaptador treinado
        """
        logger.info(f"Iniciando treinamento colaborativo para {task_type}")

        # 1. Sincronizar conhecimento
        self.sync_with_peers()

        # 2. Coletar dataset combinado
        dataset = self.collector.get_training_dataset(
            task_type=task_type,
            min_quality=0.8
        )

        logger.info(f"Dataset colaborativo: {len(dataset)} exemplos")

        # 3. Treinar adaptador
        from training.lora_trainer import train_ziva_adapter
        from core.dataset_builder import DatasetBuilder

        # Criar dataset temporário
        builder = DatasetBuilder()
        dataset_path = f"data/training/collaborative_{task_type}.json"

        import json
        with open(dataset_path, 'w') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        # Treinar
        adapter_path = train_ziva_adapter(
            dataset_path=dataset_path,
            task_type=f"collaborative_{task_type}"
        )

        # 4. Compartilhar adaptador com peers
        for peer in self.peers:
            self.share_adapter(peer, task_type, adapter_path)

        return adapter_path

    def sync_rag_knowledge(self, peer_url: str) -> bool:
        """
        Sincroniza conhecimento RAG (vetores + texto) com um peer.
        
        Args:
            peer_url (str): URL base do peer
            
        Returns:
            bool: Sucesso total da operação
        """
        logger.info(f"🔄 Iniciando sincronização RAG com {peer_url}...")
        
        try:
            from core.rag_helper import get_rag_helper
            rag = get_rag_helper()
            
            total_sent = 0
            file_count = 0
            
            # Send chunks in batches
            for batch in rag.get_all_documents(batch_size=50):
                payload = {
                    "source_node": self.node_name,
                    "points": batch,
                    "collection_name": "main_knowledge"
                }
                
                try:
                    # Enviar para a API de recepção criada
                    response = requests.post(
                        f"{peer_url}/api/p2p/receive_rag_batch",
                        json=payload,
                        timeout=60 # Vetores são grandes, timeout maior
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        sent = data.get("received", 0)
                        total_sent += sent
                        sys.stdout.write(f"\r📤 Enviados: {total_sent} vetores...")
                        sys.stdout.flush()
                    else:
                        logger.warning(f"Falha no batch: {response.status_code} - {response.text}")
                        
                except Exception as batch_err:
                    logger.error(f"Erro enviando batch RAG: {batch_err}")
            
            print(f"\n✅ Sincronização RAG completa! Total enviado: {total_sent}")
            return True
            
        except Exception as e:
            logger.error(f"Erro geral na sincronização RAG: {e}")
            return False



class GabrielleConnector:
    """
    Conector P2P via Protocolo Binário (Socket 9000).
    """

    def __init__(self, host: str = "100.114.201.84", port: int = 9000):
        self.host = host
        self.port = port
        self.is_connected = False
        self.sock = None
        self._connect()

    def _connect(self):
        """Estabelece conexão e realiza handshake"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Apply network optimizations
            try:
                from core.network_optimizer import NetworkOptimizer
                self.sock = NetworkOptimizer.optimize_socket(self.sock)
                logger.info("🚀 Otimizações de rede aplicadas ao socket P2P")
            except Exception as e:
                logger.warning(f"⚠️ Não foi possível aplicar otimizações: {e}")

            self.sock.settimeout(5)
            self.sock.connect((self.host, self.port))

            # Handshake Protocol
            banner = self.sock.recv(1024)  # Expect AUTH_REQ
            if b"AUTH_REQ" in banner:
                # 1. Determine Identity/Key
                key = b"ziva-trust-key"  # Default

                # Try to find specific key for this host
                try:
                    with open("/home/holloway/ziva/config/peers.json", 'r') as f:
                        data = json.load(f)
                        peers = data.get("peers", {})
                        if self.host in peers:
                            key = peers[self.host]["key"].encode('utf-8')
                            logger.info(
                                f"🔑 Using custom key for peer: {peers[self.host]['name']}")
                except Exception as ex:
                    logger.debug(f"Could not load peer keys: {ex}")

                self.sock.sendall(key)
                response = self.sock.recv(1024)
                if b"AUTH_OK" in response:
                    self.is_connected = True
                    logger.info(
                        f"✅ Conectado e Autenticado com {self.host} (P2P Binary)")
                    return True
                else:
                    logger.warning(f"Falha de Autenticação P2P: {response}")

            self.sock.close()
            self.sock = None
        except Exception as e:
            logger.error(f"Erro de conexão P2P: {e}")
            self.is_connected = False

    def close(self):
        if self.sock:
            self.sock.close()

    def health_check(self) -> bool:
        """Envia PING e espera PONG"""
        if not self.is_connected or not self.sock:
            if not self._connect():
                return False

        try:
            self.sock.sendall(b"PING")
            response = self.sock.recv(1024)
            return b"PONG" in response
        except Exception:
            self.is_connected = False
            return False

    def get_gabrielle_knowledge(self) -> List[Dict]:
        """
        Obtém conhecimento da Gabrielle via Protocolo Binário (REQUEST_DATA).
        """
        if not self.is_connected or not self.sock:
            if not self._connect():
                return []

        try:
            import struct

            # Enviar Comando
            self.sock.sendall(b"REQUEST_DATA\n")

            # Ler Header (Tamanho)
            raw_len = self.sock.recv(4)
            if not raw_len:
                return []

            msg_len = struct.unpack('>I', raw_len)[0]

            # Ler Payload
            data = b''
            while len(data) < msg_len:
                packet = self.sock.recv(msg_len - len(data))
                if not packet:
                    break
                data += packet

            if len(data) == msg_len:
                # Changed from json.loads to msgpack.unpackb
                dataset = msgpack.unpackb(data, raw=False)
                return dataset

        except Exception as e:
            logger.error(f"Erro ao receber conhecimento via binário: {e}")
            self.is_connected = False

        return []

    def teach_gabrielle(self, dataset: List[Dict]) -> bool:
        """
        Ensina Gabrielle via Protocolo Binário.
        """
        if not self.is_connected or not self.sock:
            if not self._connect():
                return False

        try:
            import struct

            # Comando
            self.sock.sendall(b"SYNC_DATA\n")

            # Esperar READY
            resp = self.sock.recv(1024)
            if b"READY" not in resp:
                logger.error(f"Erro: Servidor não pronto: {resp}")
                return False

            # Preparar Payload
            # Changed from json.dumps to msgpack.packb
            payload = msgpack.packb(dataset, use_bin_type=True)
            msg_len = len(payload)

            # Enviar Tamanho (4 bytes Big Endian) + Payload
            header = struct.pack('>I', msg_len)
            self.sock.sendall(header + payload)

            # Esperar ACK
            ack = self.sock.recv(1024)
            if b"ACK" in ack:
                logger.info(f"✅ Sucesso: {ack.decode().strip()}")
                return True
            else:
                logger.warning(f"Resposta inesperada: {ack}")

        except Exception as e:
            logger.error(f"Erro ao ensinar via binário: {e}")
        return False

    def ask_remote_llm(self, prompt: str) -> str:
        """
        Envia um prompt para o LLM remoto via RPC Binário.
        Comando: RPC_LLM
        """
        if not self.is_connected or not self.sock:
            if not self._connect():
                return ""

        try:
            import struct

            # 1. Enviar Comando RPC
            self.sock.sendall(b"RPC_LLM\n")

            # 2. Esperar READY
            resp = self.sock.recv(1024)
            if b"READY" not in resp:
                logger.warning(
                    f"Peer não suporta RPC_LLM ou erro no handshake: {resp}")
                return ""

            # 3. Serializar e Enviar Prompt
            data = {"prompt": prompt}  # Wrap prompt in a dict for msgpack
            # Changed from prompt.encode('utf-8') to msgpack.packb
            payload = msgpack.packb(data, use_bin_type=True)
            msg_len = len(payload)
            header = struct.pack('>I', msg_len)
            self.sock.sendall(header + payload)

            # 4. Receber Resposta (Length + Payload)
            # Aumentar timeout para inferência em hardware modesto (Gabrielle)
            # i3-4005U pode levar ~3-4 min para prompts complexos
            self.sock.settimeout(300.0)
            raw_len = self.sock.recv(4)
            if not raw_len:
                return ""
            resp_len = struct.unpack('>I', raw_len)[0]

            # Ler Resposta em Chunks (pode ser longa)
            data = b''
            while len(data) < resp_len:
                remaining = resp_len - len(data)
                packet = self.sock.recv(min(4096, remaining))
                if not packet:
                    break
                data += packet

            if len(data) == resp_len:
                resp_payload = msgpack.unpackb(data, raw=False)
                return resp_payload.get("response", "")

        except Exception as e:
            logger.error(f"Erro no RPC Remoto: {e}")
            self.is_connected = False
            return ""

    def search_remote_latent(self, embedding: List[float]) -> str:
        """
        Busca contexto remoto enviando apenas o vetor (Latent RAG).
        (Otimização Sprint 42 - Fase 2)
        """
        if not self.is_connected or not self.sock:
            if not self._connect():
                return ""

        try:
            import struct

            # 1. Comando
            self.sock.sendall(b"SEARCH_LATENT\n")

            # 2. Quantizar Vetor (f32 -> i8)
            from core.network_optimizer import NetworkOptimizer
            q_vector, scale = NetworkOptimizer.quantize_int8(embedding)

            # 3. Enviar (Msgpack)
            payload = msgpack.packb(
                {"vector": q_vector, "scale": scale}, use_bin_type=True)
            msg_len = len(payload)
            self.sock.sendall(struct.pack('>I', msg_len) + payload)

            # 4. Receber Resposta
            raw_len = self.sock.recv(4)
            if not raw_len:
                return ""
            resp_len = struct.unpack('>I', raw_len)[0]

            data = b''
            while len(data) < resp_len:
                packet = self.sock.recv(min(4096, resp_len - len(data)))
                if not packet:
                    break
                data += packet

            if len(data) == resp_len:
                resp_payload = msgpack.unpackb(data, raw=False)
                context = resp_payload.get("context", "")
                logger.info(
                    f"✨ Latent RAG context recebido ({len(context)} chars)")
                return context

        except Exception as e:
            logger.error(f"Erro no Latent Search: {e}")
            self.is_connected = False
            return ""


if __name__ == "__main__":
    # Teste
    print("🔗 P2P Collaborative Learning System")

    # Verificar Gabrielle
    gabrielle = GabrielleConnector()
    print(f"Gabrielle conectada: {gabrielle.is_connected}")

    if gabrielle.is_connected:
        # Criar nó P2P
        node = P2PLearningNode(
            node_name="ziva",
            peers=["http://falcon:9000"]
        )

        # Sincronizar
        print("\n🔄 Sincronizando conhecimento...")
        node.sync_with_peers()

        print("✅ Sincronização completa!")
    else:
        print("⚠️  Gabrielle não disponível. Execute Ziva em falcon primeiro.")