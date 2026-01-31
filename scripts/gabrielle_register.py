#!/usr/bin/env python3
"""
Script para Gabrielle se auto-registrar no banco da Ziva master
Executar na Gabrielle via cron ou manualmente
"""
import sqlite3
import sys

ZIVA_DB = "/home/holloway/ziva/data/ziva.db"
NODE_ID = "gabrielle"
PUBLIC_KEY = "ziva-trust-key"

try:
    conn = sqlite3.connect(ZIVA_DB)
    cursor = conn.cursor()

    # Criar tabela se não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS peers (
            node_id TEXT PRIMARY KEY,
            public_key TEXT,
            trust_level INTEGER DEFAULT 50,
            last_seen TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Inserir/atualizar registro
    cursor.execute('''
        INSERT OR REPLACE INTO peers (node_id, public_key, trust_level, last_seen)
        VALUES (?, ?, 100, datetime('now'))
    ''', (NODE_ID, PUBLIC_KEY))

    conn.commit()
    print(f"✅ Gabrielle registrada no master (trust_level: 100)")

    # Verificar
    cursor.execute("SELECT * FROM peers WHERE node_id = ?", (NODE_ID,))
    print(f"   Registro: {cursor.fetchone()}")

    conn.close()
    sys.exit(0)

except Exception as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)
