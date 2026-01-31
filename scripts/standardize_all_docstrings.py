#!/usr/bin/env python3
"""
Script para padronizar docstrings em todo o projeto Ziva.
Processa todos os arquivos Python e aplica formato Google Style.
"""

import logging
from extensions.docstring_tools import standardize_docstrings
from pathlib import Path
import sys
sys.path.insert(0, '/home/holloway/ziva')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BatchStandardize")


def standardize_project(directory="/home/holloway/ziva", dry_run=False):
    """
    Padroniza docstrings de todo o projeto.

    Args:
        directory (str): Diretório raiz do projeto
        dry_run (bool): Se True, apenas reporta sem modificar arquivos

    Returns:
        dict: Estatísticas de padronização
    """
    base_path = Path(directory)

    # Buscar todos os arquivos Python
    ignore_dirs = {'.venv', '__pycache__', 'node_modules', '.git', 'data'}
    py_files = [
        f for f in base_path.rglob('*.py')
        if not any(ig in str(f) for ig in ignore_dirs)
    ]

    print(f"📁 Encontrados {len(py_files)} arquivos Python")
    print(
        f"🔧 Modo: {
            'DRY RUN (sem modificações)' if dry_run else 'APLICANDO MUDANÇAS'}\n")

    total_functions = 0
    total_classes = 0
    errors = 0

    for idx, file_path in enumerate(py_files, 1):
        try:
            print(
                f"[{idx}/{len(py_files)}] Processando: {file_path.name}...", end=" ")

            result = standardize_docstrings(
                str(file_path), auto_fix=not dry_run)

            # Extrair estatísticas do resultado
            if "Funções corrigidas:" in result:
                funcs = int(
                    result.split("Funções corrigidas: ")[1].split("\n")[0])
                classes = int(
                    result.split("Classes corrigidas: ")[1].split("\n")[0])
                total_functions += funcs
                total_classes += classes

                if funcs > 0 or classes > 0:
                    print(f"✅ {funcs}f {classes}c")
                else:
                    print("⏭️  OK")
            else:
                print("⚠️  Erro")
                errors += 1

        except Exception as e:
            print(f"❌ {e}")
            errors += 1

    print(f"\n📊 Resumo:")
    print(f"   - Arquivos processados: {len(py_files)}")
    print(f"   - Funções padronizadas: {total_functions}")
    print(f"   - Classes padronizadas: {total_classes}")
    print(f"   - Erros: {errors}")

    if dry_run:
        print(f"\n⚠️  DRY RUN - Nenhuma modificação foi feita")
        print(f"   Execute sem --dry-run para aplicar mudanças")
    else:
        print(f"\n✅ Padronização completa!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Padronizar docstrings do projeto")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas reportar sem modificar")
    parser.add_argument(
        "--dir",
        default="/home/holloway/ziva",
        help="Diretório do projeto")

    args = parser.parse_args()

    standardize_project(args.dir, args.dry_run)
