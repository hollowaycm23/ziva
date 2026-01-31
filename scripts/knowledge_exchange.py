#!/usr/bin/env python3
"""
Knowledge Exchange CLI - Troca de informações com peers via P2P
"""
from core.p2p_learning import GabrielleConnector
import sys
import os
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def query_peer_status(host, port=9000):
    """Consulta status e capabilities de um peer"""
    print(f"🔍 Consultando peer: {host}:{port}")

    conn = GabrielleConnector(host=host, port=port)
    if not conn.is_connected:
        print("❌ Peer offline ou inacessível")
        return None

    # Envia query RPC pedindo informações do projeto
    query = """
    Por favor, descreva:
    1. Nome do seu projeto
    2. Stack tecnológica (linguagens, frameworks)
    3. Estado atual de desenvolvimento
    4. Áreas onde você precisa de ajuda ou consultoria
    5. Conhecimento que você pode compartilhar

    Responda em formato estruturado JSON.
    """

    response = conn.ask_remote_llm(query)

    if response:
        print("\n📡 Resposta recebida do peer:")
        print("=" * 60)
        print(response)
        print("=" * 60)
        return response
    else:
        print("⚠️ Sem resposta do peer")
        return None


def share_knowledge(host, topic, port=9000):
    """Compartilha conhecimento sobre um tópico específico"""
    print(f"📤 Compartilhando conhecimento sobre: {topic}")

    # Gera resposta usando LLM local
    from core.llm import LLMService
    llm = LLMService()

    prompt = f"""
    Explique de forma clara e concisa sobre: {topic}

    Inclua:
    - Conceitos principais
    - Melhores práticas
    - Exemplos práticos
    - Recursos úteis
    """

    knowledge = llm.completion(prompt)

    # Envia para peer via P2P
    conn = GabrielleConnector(host=host, port=port)
    if conn.is_connected:
        dataset = [{
            "instruction": f"Knowledge about: {topic}",
            "output": knowledge,
            "source": "ziva_collaborative_learning"
        }]
        success = conn.teach_gabrielle(dataset)
        if success:
            print("✅ Conhecimento compartilhado com sucesso!")
        else:
            print("❌ Falha ao compartilhar")
    else:
        print("❌ Peer inacessível")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="P2P Knowledge Exchange")
    parser.add_argument("--host", required=True, help="Peer IP")
    parser.add_argument("--port", type=int, default=9000, help="P2P Port")
    parser.add_argument("--action", choices=["status", "share"], required=True)
    parser.add_argument("--topic", help="Topic to share (for share action)")

    args = parser.parse_args()

    if args.action == "status":
        query_peer_status(args.host, args.port)
    elif args.action == "share":
        if not args.topic:
            print("❌ --topic required for share action")
            sys.exit(1)
        share_knowledge(args.host, args.topic, args.port)
