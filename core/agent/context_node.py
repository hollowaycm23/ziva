from core.config import config
from core.llm import LLMService
from langchain_core.messages import SystemMessage, HumanMessage
import logging

logger = logging.getLogger("ContextNode")

def contextualize_node(state):
    """
    Nó dedicado para reescrita de query baseada no histórico.
    Evita que o analyze_node fique sobrecarregado ou cause crashes por imports circulares.
    """
    messages = state.get("messages", [])
    if len(messages) <= 1:
        return {"input": state["input"]}

    try:
        # Build history string
        history_str = ""
        for msg in messages[:-1]:
            role = "User" if msg.type == "human" else "AI"
            content = msg.content[:200] # Truncate for efficiency
            history_str += f"{role}: {content}\n"
        
        # Resolve LLM via config for stability
        primary_config = config.get_llm_provider("agent.primary_model")
        if not primary_config:
            return {"input": state["input"]}

        llm = LLMService(
            model=primary_config["model_name"],
            base_url=primary_config["base_url"],
            api_key=primary_config["api_key"]
        )

        ctx_sys_msg = (
            "You are a Contextualizer. Reformulate the LAST User Query to be standalone, "
            "incorporating necessary context from the Chat History.\n"
            "Rules:\n"
            "1. If Query is already standalone, return it EXACTLY as is.\n"
            "2. If Query implies context (e.g. 'more concise', 'and him?'), rewrite it to be explicit.\n"
            "3. Output ONLY the rewritten query."
        )
        
        ctx_human_msg = f"History:\n{history_str}\nQuery: {state['input']}"
        
        # We use the raw LLMService to avoid LangChain overhead here if needed, 
        # but let's stick to a simple prompt
        rewritten = llm.chat([
            {"role": "system", "content": ctx_sys_msg},
            {"role": "user", "content": ctx_human_msg}
        ]).strip()
        
        if rewritten and len(rewritten) > 3 and rewritten != state["input"]:
            logger.info(f"🔄 Standalone Query: {rewritten}")
            return {"input": rewritten}
            
    except Exception as e:
        logger.error(f"Contextualization node error: {e}")
        
    return {"input": state["input"]}
