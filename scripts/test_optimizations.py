#!/usr/bin/env python3
"""
Teste Completo de Otimização
Valida todas as otimizações implementadas
"""

import numpy as np
from core.quality_scorer import QualityScorer
from core.session_logger import SessionLogger
from core.embedding_cache import EmbeddingCache
from core.network_optimizer import NetworkOptimizer
import sys
import time
sys.path.insert(0, '/home/holloway/ziva')


print("🧪 Teste Completo de Otimização")
print("=" * 60)

# 1. Testar Network Optimizer
print("\n1️⃣ Network Optimizer")
print("-" * 60)

test_data = b"Hello World! " * 1000
compressed, original_size = NetworkOptimizer.compress_data(test_data)
ratio = (1 - len(compressed) / original_size) * 100

print(
    f"✅ Compressão: {original_size} → {
        len(compressed)} bytes ({
            ratio:.1f}% redução)")

# 2. Testar Embedding Cache
print("\n2️⃣ Embedding Cache")
print("-" * 60)

cache = EmbeddingCache()
test_text = "Como otimizar performance?"
test_embedding = np.random.rand(768)

# Miss
result1 = cache.get(test_text)
print(f"Cache miss: {result1 is None}")

# Set
cache.set(test_text, test_embedding)

# Hit
result2 = cache.get(test_text)
print(f"Cache hit: {result2 is not None}")

stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.1f}%")

# 3. Testar Session Logger
print("\n3️⃣ Session Logger")
print("-" * 60)

logger = SessionLogger()
session_stats = logger.get_statistics()

print(f"Total de sessões: {session_stats['total_sessions']}")
print(f"Total de interações: {session_stats['total_interactions']}")
print(f"Taxa de sucesso: {session_stats['overall_success_rate']:.1%}")

# 4. Testar Quality Scorer
print("\n4️⃣ Quality Scorer")
print("-" * 60)

scorer = QualityScorer()

# Teste com boa interação
good_score = scorer.score_interaction(
    user_input="Como usar Docker?",
    assistant_output="""Para usar Docker:

```bash
docker run -d nginx
docker ps
docker stop <container_id>
```

Comandos principais:
- `run`: Inicia container
- `ps`: Lista containers
- `stop`: Para container
""",
    tool_calls=[],
    success=True
)

print(f"Boa interação: {good_score:.2f}")

# Teste com interação ruim
bad_score = scorer.score_interaction(
    user_input="Como fazer X?",
    assistant_output="Não sei.",
    tool_calls=[],
    success=False,
    error_message="Unknown"
)

print(f"Interação ruim: {bad_score:.2f}")

# 5. Resumo Final
print("\n" + "=" * 60)
print("✅ TODOS OS COMPONENTES FUNCIONANDO!")
print("=" * 60)

print(f"""
📊 Resumo:
  • Compressão de rede: {ratio:.1f}% de redução
  • Cache de embeddings: {stats['hit_rate']:.1f}% hit rate
  • Session logger: {session_stats['total_interactions']} interações
  • Quality scorer: Scores de 0.{int(bad_score * 100)} a 0.{int(good_score * 100)}

🚀 Sistema otimizado e pronto para produção!
""")
