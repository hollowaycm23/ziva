from langgraph.graph import StateGraph, END
from core.agent.state import AgentState
from core.agent.nodes import (
    retrieve, grade_documents, generate, transform_query,
    web_search, validate_answer, contextualize_query,
    check_weather, offline_search, sherlock_search,
    get_memory_stats, get_system_services, get_network_devices,
    fetch_tech_news, set_mode, expand_query, reflection_node
)
import os

VERBOSE = os.getenv("ZIVA_VERBOSE", "false").lower() == "true"



def build_agent():
    """
    Builds the LangGraph agent workflow.
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("contextualize_query", contextualize_query)
    workflow.add_node("expand_query", expand_query)
    workflow.add_node("check_weather", check_weather)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("generate", generate)
    workflow.add_node("transform_query", transform_query)
    workflow.add_node("web_search", web_search)
    workflow.add_node("offline_search", offline_search)
    workflow.add_node("sherlock_search", sherlock_search)
    workflow.add_node("get_memory_stats", get_memory_stats)
    workflow.add_node("get_system_services", get_system_services)
    workflow.add_node("get_network_devices", get_network_devices)
    workflow.add_node("fetch_tech_news", fetch_tech_news)
    workflow.add_node("validate_answer", validate_answer)
    workflow.add_node("reflection_node", reflection_node)
    workflow.add_node("set_mode", set_mode)

    workflow.set_entry_point("contextualize_query")

    def route_query(state):
        if VERBOSE:
            print("---ROUTE QUERY---")
        question = state["question"].lower()

        if any(
            phrase in question for phrase in [
                "switch mode",
                "change mode",
                "mudar modo",
                "trocar modo",
                "modo arquiteto",
                "modo programador",
                "architect mode",
                "coder mode"]):
            if VERBOSE:
                print("---DECISION: ROUTE TO SET MODE---")
            return "set_mode"

        finance_keywords = [
            "dolar",
            "dólar",
            "bitcoin",
            "btc",
            "preço",
            "cotação",
            "valor",
            "euro",
            "selic",
            "cdi"]
        if any(w in question for w in finance_keywords):
            if VERBOSE:
                print("---DECISION: ROUTE TO WEB SEARCH (Finance/Real-time)---")
            return "web_search"

        weather_keywords = [
            "clima",
            "tempo",
            "temperatura",
            "chover",
            "chuva",
            "sol",
            "previsão"]
        if any(w in question for w in weather_keywords):
            if VERBOSE:
                print("---DECISION: ROUTE TO WEATHER TOOL---")
            return "check_weather"

        if "sherlock" in question:
            if VERBOSE:
                print("---DECISION: ROUTE TO SHERLOCK TOOL---")
            return "sherlock_search"

        services_keywords = [
            "serviços",
            "servicos",
            "portas",
            "porta",
            "rodando",
            "running",
            "services"]
        if any(w in question for w in services_keywords):
            if VERBOSE:
                print("---DECISION: ROUTE TO SYSTEM SERVICES---")
            return "get_system_services"

        memory_keywords = [
            "uso de memória",
            "uso de memoria",
            "status da memória",
            "status da memoria",
            "memória ram",
            "memoria ram",
            "quantas memórias",
            "estatísticas de memória",
            "qdrant",
            "chunks",
            "vetores"]
        if any(w in question for w in memory_keywords):
            if VERBOSE:
                print("---DECISION: ROUTE TO MEMORY STATS---")
            return "get_memory_stats"

        network_keywords = [
            "rede",
            "network",
            "máquinas",
            "maquinas",
            "dispositivos",
            "devices",
            "tailscale"]
        if any(w in question for w in network_keywords):
            if VERBOSE:
                print("---DECISION: ROUTE TO NETWORK DISCOVERY---")
            return "get_network_devices"

        news_keywords = [
            "notícias",
            "noticias",
            "novidades",
            "headlines",
            "news",
            "últimas",
            "ultimas"]
        tech_keywords = ["tecnologia", "tech", "hardware", "software"]
        if any(nw in question for nw in news_keywords) and any(
                tw in question for tw in tech_keywords):
            if VERBOSE:
                print("---DECISION: ROUTE TO TECH NEWS FETCH---")
            return "fetch_tech_news"
            
        if VERBOSE:
            print("---DECISION: ROUTE TO QUERY EXPANSION (Semantic Upgrade)---")
        return "expand_query"

    workflow.add_conditional_edges(
        "contextualize_query",
        route_query,
        {
            "expand_query": "expand_query",
            "check_weather": "check_weather",
            "sherlock_search": "sherlock_search",
            "get_system_services": "get_system_services",
            "get_memory_stats": "get_memory_stats",
            "get_network_devices": "get_network_devices",
            "fetch_tech_news": "fetch_tech_news",
            "set_mode": "set_mode",
            "web_search": "web_search"
        }
    )

    workflow.add_edge("expand_query", "retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_edge("check_weather", "generate")
    workflow.add_edge("offline_search", "generate")
    workflow.add_edge("sherlock_search", "generate")
    workflow.add_edge("get_system_services", "generate")
    workflow.add_edge("get_memory_stats", "generate")
    workflow.add_edge("get_network_devices", "generate")
    workflow.add_edge("fetch_tech_news", "generate")
    workflow.add_edge("set_mode", "generate")

    def decide_to_generate(state):
        """
        Determines whether to generate an answer, or re-generate a question.
        """
        if VERBOSE:
            print("---DECIDE TO GENERATE---")
        filtered_documents = state["documents"]
        retry_count = state.get("retry_count", 0)

        if not filtered_documents:
            if retry_count == 0:
                if VERBOSE:
                    print("---DECISION: RETRY / WEB SEARCH---")
                return "web_search"
            elif retry_count == 1:
                if VERBOSE:
                    print("---DECISION: RETRY / OFFLINE SEARCH---")
                return "offline_search"
            else:
                if VERBOSE:
                    print("---DECISION: GIVE UP---")
                return "generate"
        else:
            if VERBOSE:
                print("---DECISION: GENERATE---")
            return "generate"

    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "transform_query": "transform_query",
            "offline_search": "offline_search",
            "web_search": "web_search",
            "generate": "generate",
        },
    )

    workflow.add_edge("transform_query", "retrieve")
    workflow.add_edge("web_search", "generate")

    workflow.add_edge("generate", "validate_answer")

    def decide_after_validation(state):
        """
        Route based on validation.
        """

        if VERBOSE:
            print("---VALIDATE_ANSWER---")
        is_refusal = state.get("is_refusal", False)
        retry_count = state.get("retry_count", 0)

        if is_refusal:
            if VERBOSE:
                print("---DECISION: REFUSAL DETECTED. ATTEMPTING FALLBACK---")
            if retry_count <= 1:
                return "web_search"
            else:
                return END
        else:
            if VERBOSE:
                print("---DECISION: VALID ANSWER -> REFLECTION---")
            return "reflection_node"

    workflow.add_conditional_edges(
        "validate_answer",
        decide_after_validation,
        {
            "web_search": "web_search",
            "reflection_node": "reflection_node",
            END: END
        }
    )
    
    workflow.add_edge("reflection_node", END)

    app = workflow.compile()

    return app