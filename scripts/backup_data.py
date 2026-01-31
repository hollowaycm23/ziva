#!/usr/bin/env python3

import os
import time
from pathlib import Path

SOURCE_DIR = Path("/home/holloway/ziva/data")
BACKUP_DIR = Path("/home/holloway/ziva/backups")
NODES_FILE = Path("/home/holloway/ziva/core/nodes.json")


def perform_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"ziva_backup_{timestamp}.tar.gz"

    # Temporariamente copia nodes.json para a pasta de data para incluir no pack se desejar,
    # ou apenas adiciona manualmente.

    print(f"📦 Criando backup em {backup_path}...")

    # Comando de sistema para garantir compressão eficiente
    os.system(
        f"tar -czf {backup_path} -C /home/holloway/ziva data core/nodes.json")

    # Limpeza: mantém apenas os últimos 5 backups
    backups = sorted(BACKUP_DIR.glob("*.tar.gz"), key=os.path.getmtime)
    while len(backups) > 5:
        old_backup = backups.pop(0)
        old_backup.unlink()
        print(f"🗑️ Removendo backup antigo: {old_backup.name}")

    print("✅ Backup concluído com sucesso.")


if __name__ == "__main__":
    perform_backup()
