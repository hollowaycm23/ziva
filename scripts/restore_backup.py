#!/usr/bin/env python3
"""
Restaurar Backup ziva_memory.tar.gz para Qdrant
Extrai e importa dados do backup para o sistema de memória
"""

import sys
import os
import tarfile
import json
import shutil
from pathlib import Path

sys.path.insert(0, '/home/holloway/ziva')

print("📦 Restauração de Backup - Ziva Memory")
print("=" * 60)

# Caminhos
backup_file = "/home/holloway/ziva/ziva_memory.tar.gz"
temp_dir = "/tmp/ziva_restore"

# Verificar backup
if not Path(backup_file).exists():
    print(f"❌ Backup não encontrado: {backup_file}")
    sys.exit(1)

backup_size = Path(backup_file).stat().st_size / (1024 * 1024)
print(f"\n📂 Backup encontrado: {backup_size:.2f} MB")

# Extrair
print(f"\n📤 Extraindo para {temp_dir}...")
if Path(temp_dir).exists():
    shutil.rmtree(temp_dir)
Path(temp_dir).mkdir(parents=True)

with tarfile.open(backup_file, 'r:gz') as tar:
    tar.extractall(temp_dir)
    members = tar.getmembers()
    print(f"   ✅ {len(members)} arquivos extraídos")

# Listar conteúdo
print("\n📋 Conteúdo do backup:")
for item in Path(temp_dir).rglob('*'):
    if item.is_file():
        size = item.stat().st_size
        rel_path = item.relative_to(temp_dir)
        print(f"   • {rel_path} ({size} bytes)")

# Verificar se tem dados Qdrant
qdrant_data = Path(temp_dir) / "qdrant_storage"
if qdrant_data.exists():
    print("\n🧠 Dados Qdrant encontrados!")
    print(f"   Localização: {qdrant_data}")

    # Opção 1: Copiar diretamente para storage do Qdrant
    target_storage = "/home/holloway/ziva/qdrant_storage"

    print(f"\n🔄 Opções de restauração:")
    print(f"   1. Copiar para: {target_storage}")
    print(f"   2. Usar docker volume mount")

    print("\n💡 Para restaurar:")
    print(f"   # Parar Qdrant")
    print(f"   docker stop ziva-qdrant")
    print(f"   ")
    print(f"   # Copiar dados")
    print(f"   rm -rf {target_storage}")
    print(f"   cp -r {qdrant_data} {target_storage}")
    print(f"   ")
    print(f"   # Reiniciar Qdrant")
    print(f"   docker start ziva-qdrant")

# Verificar se tem JSONs ou outros dados
json_files = list(Path(temp_dir).rglob('*.json'))
if json_files:
    print(f"\n📄 {len(json_files)} arquivos JSON encontrados")

    # Tentar importar
    try:
        from core.ziva_memory import ZivaMemory

        print("\n🔄 Importando dados JSON...")
        memory = ZivaMemory()

        imported = 0
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)

                if isinstance(data, list):
                    for item in data:
                        if 'text' in item:
                            memory.save(
                                text=item['text'],
                                quadrant=item.get('quadrant', 'Q2_USER_DATA'),
                                metadata=item.get('metadata', {}),
                                importance=item.get('importance', 0.5)
                            )
                            imported += 1
            except Exception as e:
                print(f"   ⚠️  Erro em {json_file.name}: {e}")

        print(f"   ✅ {imported} memórias importadas")

        # Estatísticas
        stats = memory.get_statistics()
        print(f"\n   Total no Qdrant: {stats['TOTAL']}")

    except ImportError:
        print("\n⚠️  ZivaMemory não disponível (instale dependências)")

print("\n" + "=" * 60)
print("✅ Análise de backup concluída!")
print(f"\nDados extraídos em: {temp_dir}")
