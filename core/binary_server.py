import socket
import threading
import logging
import time
import msgpack
import struct
import hashlib
from core.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BinaryServer")


class BinaryServer:
    """
    Servidor TCP "Always On" para canal binário Ziva <-> Gabrielle.
    Porta Padrão: 9000
    """

    def __init__(self, host='0.0.0.0', port=9000):
        self.host = host
        self.port = port
        self.db = DatabaseManager()
        self.running = False
        self.clients = {}

    def start(self):
        self.running = True
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_sock.bind((self.host, self.port))
            self.server_sock.listen(5)
            logger.info(f"Binary Channel OUVINDO em {self.host}:{self.port}")

            while self.running:
                client, addr = self.server_sock.accept()
                logger.info(f"Conexão recebida de {addr}")
                t = threading.Thread(
                    target=self._handle_client, args=(
                        client, addr))
                t.daemon = True
                t.start()

        except Exception as e:
            logger.error(f"Erro no servidor binário: {e}")
        finally:
            self.server_sock.close()

    def _handle_client(self, client_sock, addr):
        try:
            client_sock.sendall(b"AUTH_REQ\n")
            client_sock.settimeout(10)
            key_data = client_sock.recv(1024).decode().strip().strip('\x00')

            if not key_data:
                logger.debug(f"Conexão encerrada sem Auth de {addr}")
                client_sock.close()
                return

            if self._validate_key(key_data, addr):
                client_sock.sendall(b"AUTH_OK\n")
                client_sock.settimeout(None)
                self._client_loop(client_sock, addr)
            else:
                logger.warning(
                    f"Auth Falhou de {addr}. Key: '{key_data}' (Hex: {key_data.encode().hex()})")
                client_sock.sendall(b"AUTH_FAIL\n")
                client_sock.close()

        except Exception as e:
            logger.error(f"Erro no handling de {addr}: {e}")
            client_sock.close()

    def _validate_key(self, provided_key, addr):
        """Verifica se a chave bate com algum peer confiável (Gabrielle)."""
        conn = self.db._get_conn()
        cursor = conn.cursor()
        hashed_key = hashlib.sha256(provided_key.encode()).hexdigest()
        logger.info(f"Validando conexão de {addr}")
        cursor.execute(
            "SELECT node_id, public_key FROM peers WHERE public_key = ?",
            (hashed_key,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            logger.info(f"Autenticado: Nó {row[0]} ({addr})")
            return True
        logger.warning(f"Chave não encontrada no DB (Hash: {hashed_key})")
        return False

    def _client_loop(self, sock, addr):
        self.clients[addr] = sock
        try:
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                msg = data.decode('utf-8', errors='ignore').strip()
                if msg == "PING":
                    sock.sendall(b"PONG\n")
                elif msg == "STATUS":
                    sock.sendall(b"OK\n")
                elif msg == "SYNC_DATA":
                    sock.sendall(b"READY\n")
                    raw_len = self._recv_exact(sock, 4)
                    if not raw_len:
                        break
                    msg_len = struct.unpack('>I', raw_len)[0]
                    dataset_data = self._recv_exact(sock, msg_len)
                    if dataset_data:
                        try:
                            dataset = msgpack.unpackb(dataset_data, raw=False)
                            added = self._process_dataset(dataset)
                            sock.sendall(f"ACK {added}\n".encode())
                            logger.info(
                                f"[{addr}] Recebido dataset com {len(dataset)} itens")
                        except Exception as e:
                            logger.error(
                                f"Erro processando dataset msgpack: {e}")
                            sock.sendall(b"ERR_PROCESSING\n")
                elif msg == "REQUEST_DATA":
                    try:
                        dataset = self._fetch_dataset(limit=50)
                        payload = msgpack.packb(dataset, use_bin_type=True)
                        header = struct.pack('>I', len(payload))
                        sock.sendall(header + payload)
                        logger.info(
                            f"[{addr}] Enviado dataset com {len(dataset)} itens")
                    except Exception as e:
                        logger.error(f"Erro enviando dataset: {e}")
                        sock.sendall(b"ERR_FETCH\n")
                elif msg == "RPC_LLM":
                    try:
                        sock.sendall(b"READY\n")
                        raw_len = self._recv_exact(sock, 4)
                        if not raw_len:
                            break
                        prompt_len = struct.unpack('>I', raw_len)[0]
                        prompt_data = self._recv_exact(sock, prompt_len)
                        if not prompt_data:
                            break
                        payload = msgpack.unpackb(prompt_data, raw=False)
                        prompt = payload.get("prompt", "")
                        logger.info(
                            f"[{addr}] RPC_LLM Query: {prompt[:50]}...")
                        from core.llm import LLMService
                        llm = LLMService()
                        response = llm.completion(prompt)
                        resp_data = {"response": response}
                        resp_bytes = msgpack.packb(
                            resp_data, use_bin_type=True)
                        sock.sendall(struct.pack('>I', len(resp_bytes)))
                        sock.sendall(resp_bytes)
                        logger.info(
                            f"[{addr}] RPC_LLM Resposta enviada")
                    except Exception as e:
                        logger.error(f"Erro no RPC_LLM: {e}")
                        sock.sendall(b"ERR_RPC\n")
                elif msg == "SEARCH_LATENT":
                    try:
                        raw_len = self._recv_exact(sock, 4)
                        if not raw_len:
                            break
                        msg_len = struct.unpack('>I', raw_len)[0]
                        data = self._recv_exact(sock, msg_len)
                        payload = msgpack.unpackb(data, raw=False)
                        q_vector = payload.get("vector")
                        scale = payload.get("scale")
                        from core.network_optimizer import NetworkOptimizer
                        embedding = NetworkOptimizer.dequantize_int8(
                            q_vector, scale)
                        from core.rag_helper import get_rag_helper
                        rag = get_rag_helper()
                        memories = rag.search_memories(
                            embedding=embedding, limit=3)
                        context = rag.format_context(memories)
                        resp_data = {
                            "context": context, "count": len(memories)}
                        resp_bytes = msgpack.packb(
                            resp_data, use_bin_type=True)
                        sock.sendall(struct.pack('>I', len(resp_bytes)))
                        sock.sendall(resp_bytes)
                        logger.info(
                            f"[{addr}] SEARCH_LATENT concluído")
                    except Exception as e:
                        logger.error(f"Erro no SEARCH_LATENT: {e}")
                        sock.sendall(b"ERR_LATENT\n")
                else:
                    logger.warning(f"[{addr}] Comando desconhecido: {msg}")
                    break
        except ConnectionResetError:
            pass
        except Exception as e:
            logger.error(f"Erro no loop do cliente {addr}: {e}")
        finally:
            logger.info(f"Conexão encerrada com {addr}")
            if addr in self.clients:
                del self.clients[addr]
            sock.close()

    def _recv_exact(self, sock, n):
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def _fetch_dataset(self, limit=50):
        """Busca exemplos de treino do DB local"""
        conn = self.db._get_conn()
        conn.row_factory = lambda c, r: dict(
            zip([col[0] for col in c.description], r))
        cursor = conn.cursor()
        cursor.execute('''
            SELECT instruction, output, task_type, quality_score
            FROM training_data
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def _process_dataset(self, dataset):
        conn = self.db._get_conn()
        cursor = conn.cursor()
        added = 0
        try:
            from core.rag_helper import get_rag_helper
            rag = get_rag_helper()
        except Exception as e:
            logger.error(f"Erro ao inicializar RAG para indexação: {e}")
            rag = None
        for example in dataset:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO training_data
                    (instruction, output, task_type, quality_score, success,
                     created_at, session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    example['instruction'], example['output'],
                    example.get('task_type', 'general'),
                    example.get('quality_score', 0.8),
                    True, time.time(), -1
                ))
                if cursor.rowcount > 0:
                    added += 1
                    if rag:
                        text_to_index = (
                            f"Instruction: {example['instruction']}\n"
                            f"Output: {example['output']}")
                        emb = rag.get_embedding(text_to_index)
                        if emb:
                            rag.store.add_text(text_to_index, emb, metadata={"source": "p2p_sync"})
            except Exception as e:
                logger.error(f"Erro ao processar exemplo: {e}")
        conn.commit()
        conn.close()
        return added


def run_server():
    server = BinaryServer()
    server.start()


if __name__ == "__main__":
    run_server()
