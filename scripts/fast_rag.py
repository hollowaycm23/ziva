#!/home/holloway/ziva/agent_venv/bin/python3
import requests
from openai import OpenAI
import json
import os
import sys
import readline

# Adicionar raiz do projeto ao path para importar extensions
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# Importar ferramenta de busca unificada (com correções de fallbacks)
try:
    from extensions.unified_search import unified_web_search
except ImportError:
    print("[Aviso] unified_search não encontrado. Certifique-se de estar rodando na raiz do projeto ou com PYTHONPATH correto.")
    unified_web_search = None

# Configuration
# Default to Ollama if LM Studio not set explicitly
env_base_url = os.getenv("ZIVA_LLM_BASE_URL")
if not env_base_url:
    # Check if we should use Ollama or LM Studio default
    # For now default to Ollama which is what we activated
    LM_STUDIO_URL = "http://localhost:11434/v1"
    API_KEY = "ollama"
else:
    LM_STUDIO_URL = env_base_url
    API_KEY = "lm-studio"

SEARXNG_URL = os.getenv("ZIVA_SEARXNG_URL", "http://localhost:8080")
MODEL_NAME = os.getenv("ZIVA_LLM_MODEL", "ziva-base:latest")

client = OpenAI(base_url=LM_STUDIO_URL, api_key=API_KEY)

def ziva_search(query, num_results=3):
    """
    Realiza busca usando a ferramenta unificada (SearxNG -> Fallout Wikipedia -> etc)
    """
    print(f"\n[Sistema] Ziva está buscando por: '{query}'...")
    
    if not unified_web_search:
        return "[Erro] Módulo de busca unificada não disponível."

    try:
        # Usa unified_web_search que já tem fallback e logica robusta
        # Importante: a funcao retorna um Dict com 'results'
        res = unified_web_search(query, max_results=num_results)
        
        if not res.get("results"):
            return "Nenhum resultado encontrado na web para esta busca."
             
        context_text = f"--- RESULTADOS DA WEB PARA: '{query}' ---\n"
        context_text += f"Fonte Primária Usada: {res.get('primary_engine', 'desconhecido')}\n\n"
        
        for i, item in enumerate(res["results"]):
            title = item.get("title", "Sem título")
            content = item.get("description", "Sem resumo")
            url = item.get("url", "N/A")
            source = item.get("source", "N/A")
            
            context_text += f"[{i+1}] {title} ({source})\n    Resumo: {content}\n    Link: {url}\n\n"
            
        return context_text

    except Exception as e:
        return f"[Erro na Busca] Falha ao executar unified_web_search: {e}"

def interactive_chat():
    print("--- Ziva Online (Modo Rápido com Busca Unificada) ---")
    print("Dica: Digite '/web sua pergunta' para forçar uma pesquisa na internet.")
    print(f"Base URL: {LM_STUDIO_URL}")
    print(f"Model ({MODEL_NAME})")
    
    # Persona com instrução de RAG (Retrieval-Augmented Generation)
    system_prompt = """
    Você é Ziva, uma IA autônoma rodando localmente.
    Quando receber um 'Contexto da Web', use essas informações para responder à pergunta do usuário.
    Priorize as informações do contexto acima do seu conhecimento prévio.
    Cite as fontes se possível.
    
    REGRA DE FORMATAÇÃO:
    - NÃO use Markdown.
    - NÃO use **negrito** ou *itálico*.
    - NÃO use blocos de código (`code`).
    - Escreva apenas texto puro e direto.
    """

    history = [{"role": "system", "content": system_prompt}]

    while True:
        try:
            user_input = input("\nVocê: ")
        except EOFError:
            break
            
        if user_input.lower() in ["sair", "exit"]:
            break
        
        if not user_input.strip():
            continue
        
        # Lógica de Ferramenta
        contexto_extra = ""
        prompt_final = user_input

        # Gatilho manual para busca (mais confiável que deixar a IA adivinhar)
        if user_input.startswith("/web ") or "pesquise sobre" in user_input.lower():
            termo_busca = user_input.replace("/web ", "").replace("pesquise sobre ", "")
            contexto_extra = ziva_search(termo_busca)
            
            # Injeta o resultado da busca no prompt, mas invisível para o usuário
            prompt_final = f"{contexto_extra}\n\nCom base no contexto acima, responda: {user_input}"

        history.append({"role": "user", "content": prompt_final})

        try:
            print("Ziva: ", end="", flush=True)
            
            # Using the existing client from global scope
            stream = client.chat.completions.create(
                model=MODEL_NAME, # Use dynamic model name
                messages=history,
                temperature=0.1, # Temperatura baixa é crucial para ela ater-se aos dados da busca
                stream=True,
                timeout=120.0
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content
            
            # Salvamos no histórico a resposta limpa (sem o contexto gigante da web para não sujar a memória)
            history.append({"role": "assistant", "content": full_response})
            print()
            
        except Exception as e:
            print(f"\n[Erro] Falha na conexão com LLM Server: {e}")

if __name__ == "__main__":
    interactive_chat()
