#!/home/holloway/ziva/agent_venv/bin/python3
import time
import os
import requests
import readline
from openai import OpenAI

# Configurações
LM_STUDIO_URL = os.getenv("ZIVA_LLM_BASE_URL", "http://localhost:1234/v1")
SEARXNG_URL = os.getenv("ZIVA_SEARXNG_URL", "http://localhost:8080")
MODEL_NAME = os.getenv("ZIVA_LLM_MODEL", "batiai/qwen3.6-35b:iq3")

client = OpenAI(base_url=LM_STUDIO_URL, api_key="ziva-local")

def ziva_search(query, num_results=3):
    """
    Realiza uma busca no SearXNG local e retorna um resumo limpo.
    """
    print(f"\n[Sistema] 🔍 Executando busca por: '{query}'...")
    
    params = {
        'q': query,
        'format': 'json',
        'language': 'pt-BR',
        'safesearch': '0'
    }
    
    try:
        response = requests.get(f"{SEARXNG_URL}/search", params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if not data.get('results'):
            return "Nenhum resultado encontrado."

        context_text = f"--- DADOS WEB ('{query}') ---\n"
        for i, result in enumerate(data['results'][:num_results]):
            title = result.get('title', 'Sem título')
            content = result.get('content', 'Sem resumo')
            url = result.get('url', 'N/A')
            context_text += f"[{i+1}] {title}: {content} ({url})\n"
            
        return context_text

    except Exception as e:
        return f"[Erro na Busca] {e}"

# Prompt de Sistema focado em Tool Use (Uso de Ferramentas)
system_prompt = """
Você é Ziva, uma IA autônoma e especialista técnica.
Você tem acesso a uma ferramenta de busca em tempo real.

REGRAS DE PENSAMENTO:
1. Se o usuário perguntar sobre:
   - Eventos recentes (notícias, lançamentos, preços atuais).
   - Documentação técnica específica que pode ter mudado.
   - Fatos que você não tem certeza absoluta.
   
2. VOCÊ DEVE responder APENAS com o comando:
   [SEARCH: termo da busca]
   
3. Se você já tiver a informação no contexto ou na memória, responda normalmente.

4. FORMATO DE RESPOSTA FINAL:
   - APENAS TEXTO PURO.
   - NUNCA use Markdown (**negrito**, `código`, etc).
   - Isso é crucial para o sistema de voz ler corretamente.
"""

history = [{"role": "system", "content": system_prompt}]

print("--- Ziva Autônoma (Modo Decisão Ativado) ---")
print(f"Model: {MODEL_NAME}")
print("Digite 'sair' para encerrar.")

while True:
    try:
        user_input = input("\nVocê: ")
    except EOFError:
        break
        
    if user_input.lower() in ["sair", "exit"]:
        break
    
    # Adiciona a pergunta do usuário ao histórico temporário
    history.append({"role": "user", "content": user_input})

    # --- PASSO 1: O Agente Decide ---
    print("Ziva (Thinking)...", end="\r")
    
    try:
        # Primeira chamada: Verificar intenção
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=history,
            temperature=0.0, # Temperatura ZERO para decisão lógica precisa
            max_tokens=50    # Limitamos tokens pois só queremos saber se vai buscar ou não
        )
        
        primeira_resposta = completion.choices[0].message.content.strip()

        # --- PASSO 2: Verifica se ela pediu busca ---
        if "[SEARCH:" in primeira_resposta:
            # Extrai o termo da busca. Ex: [SEARCH: preço rtx 5090] -> preço rtx 5090
            try:
                termo = primeira_resposta.split("[SEARCH:")[1].replace("]", "").strip()
            except IndexError:
                termo = primeira_resposta # Fallback
            
            print(f"Ziva: 🔍 Decidi pesquisar sobre: '{termo}'...")
            
            # Executa a busca real no SearXNG
            resultado_web = ziva_search(termo)
            
            # Injeta o resultado no histórico como uma mensagem de sistema/ferramenta
            history.append({
                "role": "system", 
                "content": f"RESULTADO DA BUSCA (FERRAMENTA):\n{resultado_web}\n\nAgora responda à pergunta original do usuário usando esses dados."
            })
            
            # --- PASSO 3: Resposta Final com os Dados ---
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=history,
                temperature=0.2, # Um pouco de criatividade para montar o texto final
                stream=True
            )
            
            print("Ziva: ", end="", flush=True)
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    c = chunk.choices[0].delta.content
                    print(c, end="", flush=True)
                    full_response += c
            print()
            
            # Salva a resposta final no histórico
            history.append({"role": "assistant", "content": full_response})

        else:
            # Se ela não pediu busca, apenas imprime a resposta que ela já deu (ou gera o resto)
            # Como limitamos max_tokens no passo 1, é melhor gerar de novo completo se não for busca
            # A MENOS que a primeira resposta já seja completa e curta.
            
            if len(primeira_resposta) < 10 or primeira_resposta.endswith("..."): 
                # Se for muito curta ou parecer cortada, gera de novo em stream
                stream_normal = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=history,
                    temperature=0.2,
                    stream=True
                )
                print("Ziva: ", end="", flush=True)
                full_resp = ""
                for chunk in stream_normal:
                    if chunk.choices[0].delta.content:
                        c = chunk.choices[0].delta.content
                        print(c, end="", flush=True)
                        full_resp += c
                print()
                history.append({"role": "assistant", "content": full_resp})
            else:
                print(f"Ziva: {primeira_resposta}")
                history.append({"role": "assistant", "content": primeira_resposta})

    except Exception as e:
        print(f"\n[Erro] {e}")
