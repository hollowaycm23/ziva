#!/usr/bin/env python3
"""
Script de diagnóstico para testar consistência das respostas da Ziva.
Testa a mesma pergunta múltiplas vezes para detectar inconsistências.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.agent.graph import build_agent
from datetime import datetime
import json

# Perguntas de teste com respostas esperadas
TEST_QUESTIONS = [
    {
        "question": "Qual é a única ave que consegue voar para trás?",
        "expected_keywords": ["beija-flor", "colibri", "hummingbird"],
        "wrong_answers": ["pinguim", "avestruz", "galinha"]
    },
    {
        "question": "Qual é o maior planeta do sistema solar?",
        "expected_keywords": ["júpiter", "jupiter"],
        "wrong_answers": ["terra", "marte", "saturno"]
    },
    {
        "question": "Qual é a capital do Brasil?",
        "expected_keywords": ["brasília", "brasilia"],
        "wrong_answers": ["são paulo", "rio de janeiro", "salvador"]
    },
    {
        "question": "Quantos continentes existem?",
        "expected_keywords": ["7", "sete", "seis", "6"],  # Aceita ambas as convenções
        "wrong_answers": ["três", "quatro", "cinco", "dez"]
    }
]

def test_consistency(agent, question_data, num_runs=3):
    """
    Testa a mesma pergunta múltiplas vezes e verifica consistência.
    """
    question = question_data["question"]
    expected = question_data["expected_keywords"]
    wrong = question_data["wrong_answers"]
    
    print(f"\n{'='*80}")
    print(f"TESTANDO: {question}")
    print(f"{'='*80}")
    
    results = []
    
    for i in range(num_runs):
        print(f"\n--- Execução {i+1}/{num_runs} ---")
        
        try:
            # Executa o agente
            state = {
                "question": question,
                "chat_history": [],
                "documents": [],
                "generation": "",
                "retry_count": 0
            }
            
            result = agent.invoke(state)
            answer = result.get("generation", "")
            
            print(f"Resposta: {answer[:200]}...")
            
            # Verifica se contém palavras esperadas
            answer_lower = answer.lower()
            has_expected = any(kw.lower() in answer_lower for kw in expected)
            has_wrong = any(wa.lower() in answer_lower for wa in wrong)
            
            results.append({
                "run": i+1,
                "answer": answer,
                "has_expected": has_expected,
                "has_wrong": has_wrong,
                "timestamp": datetime.now().isoformat()
            })
            
            # Feedback imediato
            if has_expected:
                print("✅ Resposta contém palavras-chave esperadas")
            else:
                print("❌ Resposta NÃO contém palavras-chave esperadas")
                
            if has_wrong:
                print("⚠️ ALERTA: Resposta contém palavras INCORRETAS!")
            
        except Exception as e:
            print(f"❌ ERRO: {e}")
            results.append({
                "run": i+1,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    # Análise de consistência
    print(f"\n{'='*80}")
    print("ANÁLISE DE CONSISTÊNCIA")
    print(f"{'='*80}")
    
    correct_count = sum(1 for r in results if r.get("has_expected", False))
    wrong_count = sum(1 for r in results if r.get("has_wrong", False))
    error_count = sum(1 for r in results if "error" in r)
    
    print(f"Respostas corretas: {correct_count}/{num_runs}")
    print(f"Respostas com erros: {wrong_count}/{num_runs}")
    print(f"Erros de execução: {error_count}/{num_runs}")
    
    consistency_rate = (correct_count / num_runs) * 100
    print(f"\nTaxa de consistência: {consistency_rate:.1f}%")
    
    if consistency_rate < 100:
        print("⚠️ INCONSISTÊNCIA DETECTADA!")
    else:
        print("✅ Respostas consistentes")
    
    return {
        "question": question,
        "consistency_rate": consistency_rate,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "error_count": error_count,
        "results": results
    }

def main():
    print("="*80)
    print("DIAGNÓSTICO DE CONSISTÊNCIA DA ZIVA")
    print("="*80)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total de perguntas: {len(TEST_QUESTIONS)}")
    print(f"Execuções por pergunta: 3")
    
    # Inicializa o agente
    print("\nInicializando agente Ziva...")
    try:
        agent = build_agent()
        print("✅ Agente inicializado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar agente: {e}")
        return
    
    # Executa testes
    all_results = []
    
    for question_data in TEST_QUESTIONS:
        result = test_consistency(agent, question_data, num_runs=3)
        all_results.append(result)
    
    # Relatório final
    print(f"\n{'='*80}")
    print("RELATÓRIO FINAL")
    print(f"{'='*80}")
    
    total_consistency = sum(r["consistency_rate"] for r in all_results) / len(all_results)
    print(f"\nTaxa de consistência geral: {total_consistency:.1f}%")
    
    print("\nResumo por pergunta:")
    for r in all_results:
        status = "✅" if r["consistency_rate"] == 100 else "❌"
        print(f"{status} {r['question']}: {r['consistency_rate']:.0f}%")
    
    # Salva resultados
    output_file = f"diagnostico_consistencia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Resultados salvos em: {output_file}")
    
    if total_consistency < 80:
        print("\n⚠️ ATENÇÃO: Taxa de consistência abaixo de 80%!")
        print("Recomenda-se investigar e corrigir o sistema.")
    elif total_consistency < 100:
        print("\n⚠️ Sistema apresenta inconsistências ocasionais.")
    else:
        print("\n✅ Sistema apresenta alta consistência!")

if __name__ == "__main__":
    main()
