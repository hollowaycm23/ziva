"""
Anime Knowledge Graph Node
Handles anime-related queries using AniList API.
"""
from typing import Dict, Any
from core.agent.state import AgentState
from core.config import config
from core.tools.anilist_anime import get_anilist_client
import logging

logger = logging.getLogger("AnimeNode")


def anime_search(state: AgentState) -> Dict[str, Any]:
    """
    Search for anime information using AniList API.

    Args:
        state: Current agent state with 'question' key

    Returns:
        Updated state with 'documents' containing anime info
    """
    print("---ANIME SEARCH---")
    question = state["question"]

    query = question.lower()
    for prefix in ['anime ', 'sobre ', 'what is ', 'quem é ', 'qual é ']:
        if prefix in query:
            query = query.split(prefix, 1)[1]
            break

    query = query.strip('?').strip()

    print(f"  🎌 Searching AniList for: {query}")

    client = get_anilist_client()
    results = client.search_anime(query, limit=3)

    documents = []
    if results:
        print(f"  ✅ Found {len(results)} anime")
        for anime in results:
            doc_text = f"""
Anime: {anime['title']}
Título em Romaji: {anime['title_romaji']}
Título em Japonês: {anime['title_japanese']}

Descrição: {anime['description']}

Informações:
- Episódios: {anime['episodes'] or 'Em andamento'}
- Season: {anime['season']} {anime['year']}
- Gêneros: {', '.join(anime['genres'])}
- Score: {anime['score']}/100
- Formato: {anime['format']}
- Status: {anime['status']}
- Studios: {', '.join(anime['studios']) if anime['studios'] else 'N/A'}

Fonte: AniList (ID: {anime['id']})
""".strip()

            documents.append(doc_text)

            try:
                from core.vector_store import VectorStore
                from core.llm import LLMService

                vs = VectorStore()
                emb_config = config.get_llm_provider("agent.embedding_model")
                model_name = emb_config["model_name"] if emb_config else "text-embedding-qwen2.5-0.5b-instruct"
                llm = LLMService(model=model_name)

                embedding = llm.embedding(doc_text)
                if embedding:
                    vs.add_text(
                        text=doc_text,
                        embedding=embedding,
                        metadata={
                            'type': 'anime',
                            'source': 'anilist',
                            'anime_id': anime['id'],
                            'title': anime['title']
                        }
                    )
                    logger.debug(f"Cached anime: {anime['title']}")
            except Exception as e:
                logger.error(f"Failed to cache anime: {e}")
    else:
        print("  ❌ No anime found via AniList")

    return {"documents": documents, "question": question}
