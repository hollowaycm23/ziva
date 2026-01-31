#!/usr/bin/env python3
"""
Script para limpar ruído do Qdrant.
Remove documentos de fontes irrelevantes detectadas na auditoria.
"""

import sys
import os
import logging
from qdrant_client import QdrantClient, models

# Configuração - Tenta conectar via localhost ou container IP
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
TARGET_COLLECTIONS = ["ziva_knowledge", "main_knowledge", "gabrielle_knowledge"]

# Padrões de ruído para remover
NOISE_DOMAINS = [
    "dicio.com.br",
    "wiktionary.org",
    "meu.inss.gov.br",
    "claro.com.br",
    "minhaconexao.com.br",
    "answers.microsoft.com",
    "lexico.pt",
    "forosecuador.ec",
    "abcliterario.com",
    "automationanywhere.com",
    "prominasunica.com.br",
    "funic.faculdadeunica.com.br",
    "online.souunica.com.br",
    "360doc.com", # Chinês/Spam
    "jianshu.com",
    "163.com",
    "mathplayground.com"
]

NOISE_KEYWORDS = [
    "iframe src=", 
    "googletagmanager", 
    "Entrar com gov.br",
    "Esqueceu sua senha?",
    "Royal Joker opiniones"
]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("QdrantCleaner")

def main():
    logger.info(f"Conectando ao Qdrant em {QDRANT_HOST}:{QDRANT_PORT}...")
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        api_info = client.get_collections()
        logger.info(f"Conexão bem sucedida. Coleções: {[c.name for c in api_info.collections]}")
    except Exception as e:
        logger.error(f"Falha ao conectar ao Qdrant: {e}")
        return

    for collection_name in TARGET_COLLECTIONS:
        if collection_name not in [c.name for c in api_info.collections]:
            logger.warning(f"Coleção {collection_name} não encontrada, pulando.")
            continue
            
        logger.info(f"--- Processando coleção: {collection_name} ---")
        
        # 1. Scroll e identificar ruído
        logger.info(f"Iniciando varredura em {collection_name}...")
        
        points_to_delete = []
        total_scanned = 0
        next_page_offset = None
        
        while True:
            records, next_page_offset = client.scroll(
                collection_name=collection_name,
                limit=100,
                offset=next_page_offset,
                with_payload=True,
                with_vectors=False
            )
            
            for record in records:
                total_scanned += 1
                payload = record.payload or {}
                text = payload.get("text", "")
                source = payload.get("source", "")
                
                is_noise = False
                reason = ""
                
                # Checar domínio
                for domain in NOISE_DOMAINS:
                    if domain in source or domain in text:
                        is_noise = True
                        reason = f"Domínio bloqueado: {domain}"
                        break
                
                # Checar keywords se não flagrado pelo domínio
                if not is_noise:
                    for kw in NOISE_KEYWORDS:
                        if kw in text:
                            is_noise = True
                            reason = f"Keyword suspeita: {kw}"
                            break
                
                if is_noise:
                    logger.info(f"⚠️  Marcado para deleção ID {record.id}: {reason}")
                    points_to_delete.append(record.id)
                    
            if not next_page_offset:
                break
                
        logger.info(f"Varredura completa em {collection_name}. Scaneados: {total_scanned}. Para deletar: {len(points_to_delete)}")
        
        if not points_to_delete:
            logger.info(f"Nenhum documento de ruído em {collection_name}.")
            continue

        # Confirmar deleção logicamente
        logger.info(f"Deletando {len(points_to_delete)} pontos em {collection_name}...")
        
        try:
            client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=points_to_delete
                )
            )
            logger.info("✅ Limpeza concluída com sucesso.")
        except Exception as e:
            logger.error(f"❌ Erro ao deletar pontos: {e}")

if __name__ == "__main__":
    main()
