# ADICIONE ESTA CÉLULA NO FINAL DO NOTEBOOK KAGGLE
# Para facilitar o download dos adapters

import shutil
import os

# Criar arquivo zip dos adapters
shutil.make_archive('ziva_adapters_download', 'zip', './ziva_adapters')

print("✅ Arquivo criado: ziva_adapters_download.zip")
print("📥 Vá em Output → Procure 'ziva_adapters_download.zip'")
print("   Clique no arquivo .zip para baixar!")

# Listar o que está dentro
print("\n📁 Conteúdo do zip:")
for root, dirs, files in os.walk('./ziva_adapters'):
    level = root.replace('./ziva_adapters', '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')
