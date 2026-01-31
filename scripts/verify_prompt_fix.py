
import sys
import os
import time

# Add root to pythonpath
sys.path.append("/home/holloway/ziva")

try:
    from agent.ziva import ZivaAgent

    # Mocking necessary parts for lightweight init if needed,
    # but ZivaAgent seems to lazy load LLM, so instantiation should be safe-ish
    # if we don't call run_loop.
    # However, init calls database manager, etc. We hope they work or fail
    # gracefully.

    print("Iniciando ZivaAgent...")
    agent = ZivaAgent()

    payload = {
        "context": "Teste de verificação de prompt.",
        "input": "Quem é o presidente?"
    }

    print("\nconstruindo prompt...")
    prompt = agent.construct_prompt(payload)

    print("-" * 50)
    if "DATA ATUAL:" in prompt:
        print("SUCESSO: 'DATA ATUAL' encontrada no prompt.")
        # Extract date to verify
        import re
        match = re.search(r"DATA ATUAL: ([\d-]+ [\d:]+)", prompt)
        if match:
            print(f"Data detectada: {match.group(1)}")
    else:
        print("FALHA: 'DATA ATUAL' não encontrada no prompt.")

    if "VERIFIQUE A DATA ATUAL" in prompt:
        print("SUCESSO: Instrução crítica encontrada.")
    else:
        print("FALHA: Instrução crítica não encontrada.")

    print("-" * 50)
    print("Verificando ferramentas carregadas...")
    if "web_search" in agent.tools:
        print("SUCESSO: Ferramenta 'web_search' está carregada.")
    else:
        print("FALHA: Ferramenta 'web_search' NÃO está carregada.")
    print("-" * 50)
    sys.stdout.flush()
    os._exit(0)

except Exception as e:
    print(f"Erro fatal durante teste: {e}")
    sys.stdout.flush()
    os._exit(1)
