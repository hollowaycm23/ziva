
import re
import datetime
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range, MatchAny

def extract_query_filters(question: str) -> Filter:
    """
    Analisa a pergunta para extrair filtros de metadados (Data, Fonte).
    Retorna um objeto Filter do Qdrant ou None.
    """
    filters = []
    question_lower = question.lower()
    
    # --- 1. Filtro de Fonte (Source) ---
    # Heurística simples por palavras-chave
    source_keywords = {
        "reddit": "reddit.com",
        "globo": "globo.com",
        "g1": "globo.com",
        "wikipedia": "wikipedia.org",
        "wiki": "wikipedia.org",
        "youtube": "youtube.com",
        "guiadohacker": "guiadohacker.com.br"
    }
    
    selected_sources = []
    for keyword, domain in source_keywords.items():
        if keyword in question_lower:
            selected_sources.append(domain)
            
    if selected_sources:
        # MatchAny se houver múltiplas fontes (ex: "reddit ou globo")
        # Por enquanto vamos assumir uma ou MatchAny
        filters.append(
            FieldCondition(
                key="source",
                match=MatchAny(any=selected_sources)
            )
        )
        print(f"[FILTER] Sources detected: {selected_sources}")

    # --- 2. Filtro de Data (Date) ---
    # Formato esperado no metadado: "YYYY-MM-DD" ou timestamp
    # Aqui vamos assumir que o scraper salva "date" como string ISO "YYYY-MM-DD"
    
    today = datetime.date.today()
    date_filter = None
    
    if "hoje" in question_lower:
        # date_str = today.strftime("%Y-%m-%d")
        # date_filter = FieldCondition(
        #     key="date",
        #     range=Range(gte=date_str) # Maior ou igual a hoje (início do dia)
        # )
        pass
    elif "ontem" in question_lower:
        # yesterday = today - datetime.timedelta(days=1)
        # date_str = yesterday.strftime("%Y-%m-%d")
        # date_filter = FieldCondition(
        #     key="date",
        #     range=Range(gte=date_str)
        # )
        pass
    elif "semana passada" in question_lower or "ultima semana" in question_lower:
        # last_week = today - datetime.timedelta(days=7)
        # date_str = last_week.strftime("%Y-%m-%d")
        # date_filter = FieldCondition(
        #     key="date",
        #     range=Range(gte=date_str)
        # )
        pass
    elif "2024" in question_lower:
        # date_filter = FieldCondition(
        #     key="date",
        #     range=Range(gte="2024-01-01", lte="2024-12-31")
        # )
        pass
    elif "2023" in question_lower:
        # date_filter = FieldCondition(
        #     key="date",
        #     range=Range(gte="2023-01-01", lte="2023-12-31")
        # )
        pass

    # --- DATE FILTER DISABLED FOR STABILITY ---
    # Qdrant Range failed on string inputs. Requires Schema Migration to Unix Timestamp.
    if date_filter:
        # filters.append(date_filter)
        # print(f"[FILTER] Date constraint applied: {date_filter}")
        pass

    if not filters:
        return None

    return Filter(must=filters)
