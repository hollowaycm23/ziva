#!/usr/bin/env python3
"""
Script simplificado para auditar a base de conhecimento do Qdrant.
Usa Ollama diretamente para embeddings.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
import json
from datetime import datetime
import requests

def get_embedding_ollama(text, model="nomic-embed-text:latest"):
    """
    Gera embedding usando Ollama diretamente.
    """
    try:
        url = "http://localhost:11434/api/embed"
        payload = {
            "model": model,
            "input": text
        }
        resp = requests.post(url, json=payload, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            return data.get("embedding", [])
        else:
            print(f"❌ Erro ao gerar embedding: {resp.status_code}")
            return []
    except Exception as e:
        print(f"❌ Erro na API Ollama: {e}")
        return []

def search_qdrant(client, collection_name, query_vector, limit=10):
    """
    Busca documentos no Qdrant.
    """
    try:
        results = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit
        )
        
        documents = []
        for point in results.points:
            if hasattr(point, 'payload') and 'text' in point.payload:
                documents.append({
                    "text": point.payload['text'],
                    "score": point.score if hasattr(point, 'score') else 0
                })
        
        return documents
    except Exception as e:
        print(f"❌ Erro ao buscar no Qdrant: {e}")
        return []

def audit_topic(client, topic, keywords, wrong_keywords=None):
    """
    Audita documentos sobre um tópico específico.
    """
    print(f"\n{'='*80}")
    print(f"AUDITANDO TÓPICO: {topic}")
    print(f"{'='*80}")
    
    # Gera embedding
    query_vector = get_embedding_ollama(topic)
    
    if not query_vector:
        print("❌ Falha ao gerar embedding. Pulando tópico.")
        return {
            "topic": topic,
            "total_docs": 0,
            "issues": [{"error": "Failed to generate embedding"}],
            "documents": []
        }
    
    # Busca documentos
    results = search_qdrant(client, "main_knowledge", query_vector, limit=10)
    
    print(f"\nEncontrados {len(results)} documentos")
    
    # Analisa cada documento
    issues = []
    
    for i, doc in enumerate(results):
        text = doc.get("text", "")
        score = doc.get("score", 0)
        print(f"\n--- Documento {i+1} (Score: {score:.4f}) ---")
        print(f"Texto: {text[:200]}...")
        
        # Verifica presença de palavras-chave esperadas
        has_keywords = any(kw.lower() in text.lower() for kw in keywords)
        
        # Verifica presença de palavras incorretas
        has_wrong = False
        if wrong_keywords:
            has_wrong = any(wk.lower() in text.lower() for wk in wrong_keywords)
        
        if has_keywords:
            print("✅ Contém palavras-chave esperadas")
        else:
            print("⚠️ NÃO contém palavras-chave esperadas")
            issues.append({
                "doc_id": i+1,
                "issue": "missing_keywords",
                "text": text[:200],
                "score": score
            })
        
        if has_wrong:
            print("❌ PROBLEMA: Contém palavras INCORRETAS!")
            issues.append({
                "doc_id": i+1,
                "issue": "wrong_keywords",
                "text": text[:200],
                "score": score
            })
    
    return {
        "topic": topic,
        "total_docs": len(results),
        "issues": issues,
        "documents": [{"text": d.get("text", "")[:200], "score": d.get("score", 0)} for d in results]
    }

def main():
    print("="*80)
    print("AUDITORIA DA BASE DE CONHECIMENTO (QDRANT)")
    print("="*80)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Inicializa conexão
    print("\nInicializando conexão com Qdrant...")
    try:
        client = QdrantClient(host="localhost", port=6333)
        print("✅ Conexão estabelecida")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return
    
    # Estatísticas gerais
    print("\n" + "="*80)
    print("ESTATÍSTICAS GERAIS")
    print("="*80)
    
    try:
        collection_info = client.get_collection("main_knowledge")
        print(f"Total de vetores: {collection_info.points_count}")
        print(f"Dimensão dos vetores: {collection_info.config.params.vectors.size}")
    except Exception as e:
        print(f"⚠️ Erro ao obter estatísticas: {e}")
    
    # Tópicos para auditar
    topics_to_audit = [
        {
            "topic": "Qual ave voa para trás?",
            "keywords": ["beija-flor", "colibri", "hummingbird", "voo reverso", "voo para trás"],
            "wrong_keywords": ["pinguim", "avestruz", "galinha", "águia", "falcão"]
        },
        {
            "topic": "beija-flor características",
            "keywords": ["beija-flor", "colibri", "néctar", "flores", "asas", "batimento"],
            "wrong_keywords": ["pinguim", "nadar", "gelo"]
        },
        {
            "topic": "maior planeta sistema solar",
            "keywords": ["júpiter", "jupiter", "maior planeta", "gigante gasoso"],
            "wrong_keywords": ["terra", "marte", "vênus"]
        },
        {
            "topic": "capital do Brasil",
            "keywords": ["brasília", "brasilia", "capital", "distrito federal"],
            "wrong_keywords": ["são paulo", "rio de janeiro", "salvador"]
        }
    ]
    
    all_results = []
    
    for topic_data in topics_to_audit:
        result = audit_topic(
            client, 
            topic_data["topic"],
            topic_data["keywords"],
            topic_data.get("wrong_keywords")
        )
        all_results.append(result)
    
    # Relatório final
    print(f"\n{'='*80}")
    print("RELATÓRIO DE AUDITORIA")
    print(f"{'='*80}")
    
    total_issues = sum(len(r["issues"]) for r in all_results)
    print(f"\nTotal de problemas encontrados: {total_issues}")
    
    if total_issues > 0:
        print("\n⚠️ PROBLEMAS DETECTADOS:")
        for result in all_results:
            if result["issues"]:
                print(f"\nTópico: {result['topic']}")
                for issue in result["issues"]:
                    print(f"  - Doc {issue['doc_id']}: {issue['issue']}")
                    print(f"    Texto: {issue['text']}...")
    else:
        print("\n✅ Nenhum problema detectado na base de conhecimento")
    
    # Salva resultados
    output_file = f"auditoria_qdrant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Resultados salvos em: {output_file}")

if __name__ == "__main__":
    main()
