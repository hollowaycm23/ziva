import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from core.vector_store import VectorStore
from core.database import DatabaseManager

print("=" * 60)
print("   ANÁLISE DOS DADOS ARMAZENADOS")
print("=" * 60)

# QDRANT
print("\n--- QDRANT (main_knowledge) ---")
vs = VectorStore()
stats = vs.get_stats()
print(f"Total de vetores: {stats['vectors_count']}")

# Scroll via direct Qdrant client
from qdrant_client import QdrantClient
client = QdrantClient("http://localhost:6333")
offset = None
all_points = []
while True:
    records, offset = client.scroll(
        collection_name="main_knowledge",
        limit=100,
        offset=offset,
        with_payload=True,
        with_vectors=False
    )
    all_points.extend(records)
    if offset is None:
        break

print(f"Documentos recuperados: {len(all_points)}")

sources = collections.Counter()
roles = collections.Counter()
types = collections.Counter()
sessions_set = set()
all_texts = []

for point in all_points:
    payload = point.payload or {}
    text = payload.get("text", "")
    source = payload.get("source", "unknown")
    role = payload.get("role", "unknown")
    dtype = payload.get("type", "unknown")
    session_id = payload.get("session_id")

    sources[source] += 1
    roles[role] += 1
    types[dtype] += 1
    if session_id:
        sessions_set.add(session_id)
    if text:
        all_texts.append(text)

print(f"\n📊 Por ORIGEM:")
for s, count in sources.most_common():
    print(f"   {s}: {count}")

print(f"\n📊 Por TIPO:")
for t, count in types.most_common():
    print(f"   {t}: {count}")

print(f"\n📊 Por ROLE:")
for r, count in roles.most_common():
    print(f"   {r}: {count}")

print(f"\n📊 Sessões únicas: {len(sessions_set)}")

# Amostras de conteúdo
print(f"\n📝 AMOSTRAS DE CONTEÚDO (15 primeiras):")
for i, text in enumerate(all_texts[:15]):
    short = text[:120].replace("\n", " ")
    print(f"  {i+1}. {short}...")

# Amostras diversas (últimas)
print(f"\n📝 AMOSTRAS DIVERSAS (últimas 10):")
for text in all_texts[-10:]:
    short = text[:120].replace("\n", " ")
    print(f"  - {short}...")


# SQLITE
print(f"\n\n--- SQLITE (ziva.db) ---")
db = DatabaseManager()
conn = db._get_conn()
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM sessions")
print(f"Sessions: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM interactions")
print(f"Interactions: {cursor.fetchone()[0]}")

# Últimas interações
cursor.execute("SELECT i.role, i.content FROM interactions i ORDER BY i.id DESC LIMIT 10")
print(f"\n📝 ÚLTIMAS INTERAÇÕES:")
for role, content in cursor.fetchall():
    short = content[:120].replace("\n", " ")
    print(f"  [{role}] {short}")

# Contagem por role
cursor.execute("SELECT role, COUNT(*) FROM interactions GROUP BY role")
print(f"\n📊 Interações por role:")
for role, count in cursor.fetchall():
    print(f"  {role}: {count}")

conn.close()
print("\n" + "=" * 60)
print("   ANÁLISE CONCLUÍDA")
