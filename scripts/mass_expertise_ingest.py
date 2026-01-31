#!/usr/bin/env python3
import sys
import os
import time
import requests
import xml.etree.ElementTree as ET
import logging

# Ensure imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.vector_store import VectorStore
from core.llm import LLMService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ExpertiseIngest")

ARXIV_API_URL = "http://export.arxiv.org/api/query"
NAMESPACE = "{http://www.w3.org/2005/Atom}"

# Categories to ingest
DOMAINS = {
    "physics": ["quant-ph", "hep-th", "gr-qc"], # Quantum, High Energy, General Relativity
    "datascience": ["cs.LG", "cs.AI", "cs.CV", "stat.ML"] # Machine Learning, AI, Computer Vision
}

def get_arxiv_papers(query, max_results=10):
    """
    Fetch papers from arXiv API.
    """
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    logger.info(f"📡 Fetching {max_results} papers for query: '{query}'...")
    response = requests.get(ARXIV_API_URL, params=params)
    
    if response.status_code != 200:
        logger.error(f"API Error: {response.status_code}")
        return []

    root = ET.fromstring(response.content)
    papers = []

    for entry in root.findall(f"{NAMESPACE}entry"):
        title = entry.find(f"{NAMESPACE}title").text.strip().replace("\n", " ")
        summary = entry.find(f"{NAMESPACE}summary").text.strip().replace("\n", " ")
        paper_id = entry.find(f"{NAMESPACE}id").text.strip()
        published = entry.find(f"{NAMESPACE}published").text.strip()
        
        authors = []
        for author in entry.findall(f"{NAMESPACE}author"):
            name = author.find(f"{NAMESPACE}name").text
            authors.append(name)
            
        papers.append({
            "id": paper_id,
            "title": title,
            "summary": summary,
            "authors": authors,
            "published": published
        })
        
    logger.info(f"✅ Retrieved {len(papers)} papers.")
    return papers

def ingest_papers(papers, domain):
    """
    Embed and Store papers in Qdrant.
    """
    store = VectorStore(collection_name="ziva_knowledge") # Use main knowledge or separate?
    # Using 'ziva_knowledge' (was 'main_knowledge' in VectorStore default? Let's check.)
    # core/vector_store.py uses "main_knowledge" by default. 
    # Let's stick to default if possible or explicit "ziva_knowledge" if that's the standard.
    # User Implementation Plan says "ziva_knowledge"? No, it just says "Inrich system RAG".
    # I will use "ziva_knowledge" as it seems to be the main one used in `rag_helper`?
    # `rag_helper.py` uses `VectorStore()`. `VectorStore()` defaults to "main_knowledge".
    # I should use "main_knowledge" to ensure Ziva finds it!
    
    store = VectorStore(collection_name="main_knowledge")
    llm = LLMService() # For embeddings

    texts = []
    embeddings = []
    metadatas = []

    logger.info(f"🧠 Generating embeddings for {len(papers)} papers...")
    
    for paper in papers:
        # Create a rich text representation
        # "Title: ... \n Abstract: ..."
        content = f"Title: {paper['title']}\nAuthors: {', '.join(paper['authors'])}\nAbstract: {paper['summary']}"
        
        try:
            emb = llm.embedding(content)
            if not emb:
                logger.warning(f"Failed to embed paper: {paper['title']}")
                continue
                
            texts.append(content)
            embeddings.append(emb)
            metadatas.append({
                "type": "expertise",
                "source": "arxiv",
                "domain": domain,
                "external_id": paper["id"],
                "title": paper["title"],
                "published": paper["published"]
            })
        except Exception as e:
            logger.error(f"Embedding error: {e}")

    if texts:
        logger.info(f"💾 Storing {len(texts)} vectors in Qdrant...")
        store.add_texts(texts, embeddings, metadatas)
        logger.info("✅ Ingestion complete.")

def main():
    if len(sys.argv) > 1:
        # User supplied manual query
        queries = [sys.argv[1]]
        domain = "manual"
    else:
        # Default behavior: 5 from each category to start (Pilot)
        print("--- PHASE I: UNIVERSAL POLYMATH INGESTION ---")
        print("Select Domain to Ingest:")
        print("1. Physics (Quantum, HEP)")
        print("2. Data Science (ML, AI)")
        print("3. BOTH (Pilot Run - 5 papers each)")
        
        choice = input("Choice [3]: ").strip() or "3"
        
        target_domains = []
        if choice == "1": targets = ["physics"]
        if choice == "2": targets = ["datascience"]
        if choice == "3": targets = ["physics", "datascience"]
        
        for t in targets:
            # Construct OR query for the categories
            cats = DOMAINS[t]
            # cat:quant-ph OR cat:hep-th
            query = " OR ".join([f"cat:{c}" for c in cats])
            
            papers = get_arxiv_papers(query, max_results=5) # Pilot size
            if papers:
                ingest_papers(papers, t)
                time.sleep(3) # Rate limit politeness

if __name__ == "__main__":
    main()
