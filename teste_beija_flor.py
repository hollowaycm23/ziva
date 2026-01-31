#!/usr/bin/env python3
"""
Teste simples e direto: pergunta sobre beija-flor para a Ziva.
Apenas observa o comportamento atual sem modificar nada.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.agent.graph import build_agent

def test_beija_flor():
    """
    Testa a pergunta sobre beija-flor 3 vezes.
    """
    print("="*80)
    print("TESTE SIMPLES: Qual ave voa para trás?")
    print("="*80)
    print("\nInicializando agente...")
    
    try:
        agent = build_agent()
        print("✅ Agente inicializado\n")
    except Exception as e:
        print(f"❌ Erro: {e}")
        return
    
    question = "Qual é a única ave que consegue voar para trás?"
    
    for i in range(3):
        print(f"\n{'='*80}")
        print(f"EXECUÇÃO {i+1}/3")
        print(f"{'='*80}")
        
        try:
            state = {
                "question": question,
                "chat_history": [],
                "documents": [],
                "generation": "",
                "retry_count": 0
            }
            
            print(f"Pergunta: {question}")
            print("\nProcessando...")
            
            result = agent.invoke(state)
            answer = result.get("generation", "")
            
            print(f"\n{'─'*80}")
            print("RESPOSTA:")
            print(f"{'─'*80}")
            print(answer)
            print(f"{'─'*80}\n")
            
            # Análise simples
            answer_lower = answer.lower()
            
            if "beija-flor" in answer_lower or "colibri" in answer_lower:
                print("✅ Resposta CORRETA (menciona beija-flor/colibri)")
            elif "pinguim" in answer_lower:
                print("❌ ALUCINAÇÃO DETECTADA (menciona pinguim)")
            else:
                print("⚠️ Resposta INCONCLUSIVA (não menciona beija-flor nem pinguim)")
                
        except Exception as e:
            print(f"❌ ERRO: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_beija_flor()
