#!/usr/bin/env python3
"""
Script para injetar conhecimento de indentação Python na Ziva.
Roda independentemente do orquestrador.
"""

from core.database import DatabaseManager
from core.llm import LLMService
import sys
import time
sys.path.insert(0, '/home/holloway/ziva')


# Dados de treinamento
training_data = [
    "REGRA CRÍTICA: Python usa SEMPRE 4 espaços por nível de indentação. Nunca use 1, 2, 3 espaços ou tabs.",
    "Exemplo CORRETO:\ndef calcular(x):\n    resultado = x * 2\n    return resultado",
    "Exemplo INCORRETO (1 espaço):\ndef calcular(x):\n resultado = x * 2\n return resultado\nERRO: IndentationError",
    "Estrutura if-else CORRETA:\nif condicao:\n    fazer_algo()\nelse:\n    alternativa()",
    "Loop for CORRETO:\nfor item in lista:\n    processar(item)\n    print(item)",
    "Classe CORRETA:\nclass MinhaClasse:\n    def __init__(self):\n        self.valor = 0",
    "Try-except CORRETO:\ntry:\n    operacao()\nexcept Exception as e:\n    print(f'Erro: {e}')",
    "NUNCA misture tabs e espaços. Use SEMPRE 4 espaços.",
    "Cada bloco (def, if, for, while, class, with, try) adiciona exatamente 4 espaços.",
    "PEP 8 recomenda: Use 4 espaços por nível de indentação."]


def inject_via_database():
    """Injeta diretamente no banco de dados"""
    print("🧠 Injetando conhecimento de indentação...")

    db = DatabaseManager()
    llm = LLMService()

    conn = db._get_conn()
    cursor = conn.cursor()

    # Criar tabela de conhecimento se não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            topic TEXT,
            priority TEXT,
            created_at REAL NOT NULL,
            UNIQUE(content)
        )
    ''')

    injected = 0
    for text in training_data:
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO knowledge_base (content, topic, priority, created_at) VALUES (?, ?, ?, ?)",
                (text, "indentation", "high", time.time())
            )
            if cursor.rowcount > 0:
                injected += 1
                print(f"✅ {text[:60]}...")
        except Exception as e:
            print(f"❌ Erro: {e}")

    conn.commit()
    conn.close()

    print(f"\n📊 Injetados: {injected}/{len(training_data)}")
    print("✅ Conhecimento armazenado no banco de dados!")


if __name__ == "__main__":
    inject_via_database()
