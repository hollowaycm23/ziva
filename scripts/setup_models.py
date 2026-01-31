#!/usr/bin/env python3
"""
Setup Models - Baixa modelos necessários para Ziva Polymath
"""

from core.model_manager import get_model_manager
import sys
import os
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    mgr = get_model_manager()

    # Lista de modelos para baixar
    # DeepSeek R1 (Reasoning) e Llama 3 (General)
    models_to_pull = [
        "deepseek-r1:8b",  # Tentar tag padrão, se falhar tentar outras
        "llama3:8b"
    ]

    print("🚀 Iniciando download de modelos...")

    for model in models_to_pull:
        print(f"\n⬇️ Baixando {model}...")
        # Nota: pull_model é bloqueante neste script, mas o download é feito
        # pelo server Ollama
        success = mgr.pull_model(model)

        if success:
            print(f"✅ {model} pronto!")
        else:
            print(f"❌ Falha ao baixar {model}. Verifique o nome ou conexão.")
            # Fallback attempts
            if "deepseek" in model:
                fallback = "deepseek-coder:6.7b"
                print(f"qt Tentando fallback: {fallback}...")
                mgr.pull_model(fallback)

    print("\n🏁 Setup concluído!")
    print("Modelos disponíveis:")
    for m in mgr.list_models():
        print(f" - {m.name}")


if __name__ == "__main__":
    main()
