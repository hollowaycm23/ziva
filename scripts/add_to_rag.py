#!/usr/bin/env python3
"""
Script para adicionar documentos ao RAG da Ziva via API.
Contorna o problema de lock do Qdrant local.
"""

import sys
import requests
import json
from pathlib import Path


def add_document_to_rag(doc_path: str, api_url: str = "http://localhost:8000"):
    """
    Adiciona documento ao RAG via API da Ziva.

    Args:
        doc_path (str): Caminho do documento
        api_url (str): URL da API Ziva
    """
    path = Path(doc_path)

    if not path.exists():
        print(f"❌ Arquivo não encontrado: {doc_path}")
        return

    # Ler conteúdo
    content = path.read_text(encoding='utf-8')

    # Dividir em chunks
    chunk_size = 1000
    chunks = [content[i:i + chunk_size]
              for i in range(0, len(content), chunk_size)]

    print(f"📄 Documento: {path.name}")
    print(f"📊 Total de chunks: {len(chunks)}")
    print(f"🔄 Adicionando ao RAG via API...")

    # Enviar cada chunk via chat (o agente processará e adicionará ao RAG)
    for idx, chunk in enumerate(chunks):
        prompt = f"""Adicione este conhecimento ao sistema RAG:

Documento: {path.name}
Chunk: {idx + 1} / {len(chunks)}
Tópico: Smart Web Scraping com AI Agents

Conteúdo:
{chunk}

Armazene este conhecimento no sistema vetorial para consultas futuras."""

        try:
            response = requests.post(
                f"{api_url}/chat",
                json={"message": prompt},
                timeout=30
            )

            if response.status_code == 200:
                print(f"✅ Chunk {idx + 1}/{len(chunks)} processado")
            else:
                print(
                    f"⚠️  Chunk {idx + 1}/{len(chunks)} - Erro: {response.status_code}")

        except Exception as e:
            print(f"❌ Erro no chunk {idx + 1}: {e}")

    print(f"\n✅ Documento processado!")
    print(f"   Agora a Ziva pode responder perguntas sobre {path.name}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Adicionar documento ao RAG da Ziva")
    parser.add_argument("document", help="Caminho do documento")
    parser.add_argument(
        "--api",
        default="http://localhost:8000",
        help="URL da API")

    args = parser.parse_args()

    add_document_to_rag(args.document, args.api)
