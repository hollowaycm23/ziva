import time
import logging
from core.database import DatabaseManager
from network.transfer import TransferManager
import json
import os

logger = logging.getLogger("ZivaMessageDaemon")

from pathlib import Path
INBOX_DIR = Path("/app/inbox")
if not INBOX_DIR.parent.exists():
    INBOX_DIR = Path(__file__).parent.parent / "inbox"

OUTBOX_DIR = Path("/app/outbox")
if not OUTBOX_DIR.parent.exists():
    OUTBOX_DIR = Path(__file__).parent.parent / "outbox"


class MessageDaemon:
    """
    Daemon de Mensageria P2P.

    Monitora diretórios de Inbox/Outbox e sincroniza arquivos com o nó remoto (Gabrielle)
    utilizando o TransferManager.
    """

    def __init__(self):
        """
        Inicializa o daemon, banco de dados e gerenciador de transferências.
        Cria diretórios de Inbox/Outbox se necessário.
        """
        self.db = DatabaseManager()
        remote_host = os.getenv("REMOTE_HOST", "100.114.201.84")
        self.transfer = TransferManager(remote_host=remote_host)

        os.makedirs(INBOX_DIR, exist_ok=True)
        os.makedirs(OUTBOX_DIR, exist_ok=True)

    def run(self):
        """
        Loop principal do daemon.

        Executa ciclos de processamento de saída e verificação de entrada a cada 10 segundos.
        """
        logger.info("Message Daemon iniciado.")
        while True:
            try:
                self.process_outbox()
                self.check_remote_inbox()
                time.sleep(10)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Erro no daemon: {e}")
                time.sleep(10)

    def process_outbox(self):
        """
        Processa mensagens na fila de saída (diretório Outbox).

        Envia cada arquivo encontrado para o nó remoto via SCP e remove o local após sucesso.
        """
        # 1. Pega msgs do DB com status 'new' e direction 'outgoing'
        # Simulação: lê arquivos do dir outbox e envia
        for file_name in os.listdir(OUTBOX_DIR):
            file_path = os.path.join(OUTBOX_DIR, file_name)
            remote_inbox = os.getenv("REMOTE_INBOX_PATH", "/home/holloway/ziva_node08/inbox")
            if self.transfer.send_file(
                    file_path, f"{remote_inbox}/{file_name}"):
                logger.info(f"Mensagem {file_name} enviada para node08.")
                os.remove(file_path)  # Remove após envio com sucesso

    def check_remote_inbox(self):
        """
        Verifica novas mensagens no Inbox local (recebidas do remoto).

        Lê, registra no banco de dados e remove o arquivo processado.
        """
        # Em um sistema real, usariamos rsync ou scp reverso périodico
        # Simplificação: O node remoto deve enviar para nosso inbox via scp dele.
        # Nós apenas monitoramos nosso INBOX local.
        for file_name in os.listdir(INBOX_DIR):
            logger.info(f"Nova mensagem recebida: {file_name}")
            # Processar mensagem... salvar no DB...
            try:
                with open(os.path.join(INBOX_DIR, file_name), 'r') as f:
                    content = f.read()
                    # Salva no DB
                    self.db.add_message(
                        file_name,
                        'incoming',
                        'gabrielle',
                        'ziva',
                        content,
                        time.time())
                # Limpa inbox processada
                os.remove(os.path.join(INBOX_DIR, file_name))
            except Exception as e:
                logger.error(f"Erro ao processar msg {file_name}: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    daemon = MessageDaemon()
    daemon.run()
