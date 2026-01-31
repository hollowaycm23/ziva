#!/usr/bin/env python3
"""
Teste do Sistema RAG de Memória da Ziva
Demonstra uso do Qdrant com quadrantes
"""

from core.ziva_memory import ZivaMemory
import sys
sys.path.insert(0, '/home/holloway/ziva')


print("🧠 Sistema RAG de Memória - Ziva")
print("=" * 60)

try:
    # Inicializar sistema de memória
    print("\n📡 Conectando ao Qdrant...")
    memory = ZivaMemory()

    # Verificar estatísticas
    print("\n📊 Estatísticas Atuais:")
    stats = memory.get_statistics()

    total = stats.get('TOTAL', 0)
    print(f"\n   Total de memórias: {total}")

    if total > 0:
        print("\n   Por quadrante:")
        for quad, count in stats.items():
            if quad != 'TOTAL' and count > 0:
                desc = memory.quadrants.get(quad, "")
                print(f"     • {quad}: {count} ({desc})")
    else:
        print("\n   ℹ️  Sistema vazio - pronto para receber memórias")

    # Exemplo de uso
    if total == 0:
        print("\n💡 Exemplo de Uso:")
        print("-" * 60)

        # Salvar algumas memórias de exemplo
        print("\n   Salvando memórias de exemplo...")

        memory.save(
            "Ziva foi treinada com LoRA na RTX 4070",
            quadrant="Q3_PROJECTS",
            metadata={"project": "ziva", "component": "training"},
            importance=0.9
        )

        memory.save(
            "Para otimizar rede use: gradient_checkpointing=True",
            quadrant="Q5_SKILLS",
            metadata={"skill": "optimization", "topic": "training"},
            importance=0.8
        )

        memory.save(
            "Usuário prefere Python para automação",
            quadrant="Q2_USER_DATA",
            metadata={"category": "preference"},
            importance=0.7
        )

        print("   ✅ 3 memórias salvas!")

        # Buscar
        print("\n   Buscando: 'como otimizar treinamento?'")
        results = memory.recall("como otimizar treinamento?", limit=2)

        print(f"\n   Encontradas {len(results)} memórias relevantes:")
        for i, mem in enumerate(results, 1):
            print(f"\n   {i}. [{mem.quadrant}] Score: {mem.score:.3f}")
            print(f"      {mem.text[:80]}...")

        # Atualizar estatísticas
        stats = memory.get_statistics()
        print(f"\n   Total agora: {stats['TOTAL']} memórias")

    print("\n" + "=" * 60)
    print("✅ Sistema RAG funcionando!")
    print("\nPara usar:")
    print("  from core.ziva_memory import ZivaMemory")
    print("  memory = ZivaMemory()")
    print("  memory.save('texto', quadrant='Q2_USER_DATA')")
    print("  results = memory.recall('busca')")

except Exception as e:
    print(f"\n❌ Erro: {e}")
    print("\n💡 Certifique-se que Qdrant está rodando:")
    print("   docker run -d -p 6333:6333 qdrant/qdrant")
    print("\nOu instale dependências:")
    print("   pip install qdrant-client sentence-transformers")
