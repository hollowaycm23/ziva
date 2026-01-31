#!/usr/bin/env python3
"""
Popular Qdrant com Dados Existentes
Importa dados do banco SQLite para o sistema de memória RAG
"""

from pathlib import Path
import sqlite3
import sys
import os
sys.path.insert(0, '/home/holloway/ziva')


print("📦 Importação de Dados para Qdrant")
print("=" * 60)

# Verificar se Qdrant está disponível
try:
    from core.ziva_memory import ZivaMemory
    print("✅ Módulo ZivaMemory carregado")
except ImportError as e:
    print(f"❌ Erro ao importar ZivaMemory: {e}")
    print("\n💡 Instale as dependências:")
    print("   pip install --user qdrant-client sentence-transformers")
    sys.exit(1)

# Conectar ao banco de dados
db_path = "/home/holloway/ziva/training_data.db"
if not Path(db_path).exists():
    print(f"❌ Banco de dados não encontrado: {db_path}")
    sys.exit(1)

print(f"\n📂 Conectando ao banco: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verificar total de dados
cursor.execute("SELECT COUNT(*) FROM training_data")
total = cursor.fetchone()[0]
print(f"   Total de exemplos no banco: {total}")

if total == 0:
    print("⚠️  Banco vazio, nada para importar")
    sys.exit(0)

# Inicializar memória
try:
    print("\n🧠 Conectando ao Qdrant...")
    memory = ZivaMemory()
    print("   ✅ Conectado!")
except Exception as e:
    print(f"   ❌ Erro ao conectar: {e}")
    print("\n💡 Certifique-se que Qdrant está rodando:")
    print("   docker ps | grep qdrant")
    sys.exit(1)

# Importar dados
print(f"\n📥 Importando {total} exemplos...")
print("-" * 60)

# Buscar dados de alta qualidade
cursor.execute("""
    SELECT instruction, output, task_type, quality_score
    FROM training_data
    WHERE quality_score >= 0.7
    ORDER BY quality_score DESC
    LIMIT 500
""")

imported = 0
errors = 0

for row in cursor.fetchall():
    instruction, output, task_type, quality_score = row

    # Determinar quadrante baseado no tipo de tarefa
    quadrant_map = {
        'coding': 'Q5_SKILLS',
        'code-generation': 'Q5_SKILLS',
        'code-execution': 'Q5_SKILLS',
        'shell': 'Q5_SKILLS',
        'general': 'Q2_USER_DATA',
        'information-retrieval': 'Q2_USER_DATA',
    }

    quadrant = quadrant_map.get(task_type, 'Q5_SKILLS')

    # Criar texto combinado
    text = f"Q: {instruction}\nA: {output}"

    try:
        memory.save(
            text=text,
            quadrant=quadrant,
            metadata={
                'task_type': task_type,
                'source': 'training_db',
                'original_score': quality_score
            },
            importance=quality_score
        )
        imported += 1

        if imported % 50 == 0:
            print(f"   Importados: {imported}...")

    except Exception as e:
        errors += 1
        if errors < 5:  # Mostrar apenas primeiros erros
            print(f"   ⚠️  Erro ao importar: {e}")

conn.close()

# Estatísticas finais
print("\n" + "=" * 60)
print("📊 Resultado da Importação")
print("=" * 60)
print(f"   ✅ Importados: {imported}")
print(f"   ❌ Erros: {errors}")

# Mostrar estatísticas do Qdrant
stats = memory.get_statistics()
print(f"\n   Total no Qdrant: {stats['TOTAL']} memórias")
print("\n   Por quadrante:")
for quad, count in stats.items():
    if quad != 'TOTAL' and count > 0:
        desc = memory.quadrants.get(quad, "")
        print(f"     • {quad}: {count} ({desc})")

print("\n✅ Importação concluída!")
print("\n💡 Testar busca:")
print("   from core.ziva_memory import ZivaMemory")
print("   memory = ZivaMemory()")
print("   results = memory.recall('como fazer X?')")
