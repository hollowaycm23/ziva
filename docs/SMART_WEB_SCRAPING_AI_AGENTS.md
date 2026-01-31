# Smart Web Scraping com AI Agents + LLM
## Pesquisa Profunda e Exemplos de Código

## Visão Geral

Smart Web Scraping com AI Agents representa uma evolução significativa sobre métodos tradicionais, permitindo:
- **Adaptação Dinâmica**: Ajusta-se automaticamente a mudanças no layout
- **Compreensão Contextual**: Entende semântica do conteúdo
- **Extração Inteligente**: Usa linguagem natural para definir dados desejados
- **Redução de Código**: Menos parsing manual e manutenção

## Principais Frameworks e Ferramentas

### 1. llm-scraper (TypeScript)
**Descrição**: Usa LLMs para extrair dados estruturados de qualquer página web.

**Características**:
- Schema-based extraction (Zod)
- Suporta Ollama, OpenAI, local models
- Built on Playwright
- Type-safe TypeScript

**Exemplo de Código**:
```typescript
import { LLMScraper } from 'llm-scraper';
import { z } from 'zod';

const scraper = new LLMScraper({
  provider: 'ollama',
  model: 'llama2'
});

// Define schema
const productSchema = z.object({
  name: z.string(),
  price: z.number(),
  rating: z.number(),
  reviews: z.array(z.string())
});

// Scrape
const data = await scraper.scrape(
  'https://example.com/product',
  productSchema
);
```

### 2. ScrapeGraphAI (Python)
**Descrição**: Combina LLMs com lógica de grafos para pipelines adaptativos.

**Características**:
- Graph-based scraping
- Suporta GPT, Gemini, Groq, Ollama
- SmartScraperGraph, SearchGraph
- Multi-page extraction

**Exemplo de Código**:
```python
from scrapegraphai.graphs import SmartScraperGraph

graph_config = {
    "llm": {
        "model": "ollama/qwen2.5-coder:7b",
        "temperature": 0.1
    }
}

scraper = SmartScraperGraph(
    prompt="Extraia nome, preço e avaliações do produto",
    source="https://example.com/product",
    config=graph_config
)

result = scraper.run()
print(result)
```

### 3. Crawl4AI (Python)
**Descrição**: Converte conteúdo web em Markdown LLM-ready.

**Características**:
- LLM-friendly Markdown output
- Structured data extraction
- RAG-optimized
- CSS-based extraction

**Exemplo de Código**:
```python
from crawl4ai import WebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

crawler = WebCrawler()
crawler.warmup()

strategy = LLMExtractionStrategy(
    provider="ollama/qwen2.5-coder:7b",
    schema={
        "name": "product name",
        "price": "product price",
        "description": "product description"
    }
)

result = crawler.run(
    url="https://example.com/product",
    extraction_strategy=strategy
)

print(result.extracted_content)
```

### 4. Browser Use (Python)
**Descrição**: LLM controla navegador em tempo real via linguagem natural.

**Características**:
- Wrapper around Playwright
- Natural language commands
- Handles complex flows (login, forms)
- Pydantic structured output

**Exemplo de Código**:
```python
from browser_use import Agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4")
agent = Agent(
    task="Vá para Amazon e extraia os 5 produtos mais vendidos em eletrônicos",
    llm=llm
)

result = agent.run()
print(result)
```

## Integração com Playwright + LLM

### Exemplo 1: Playwright + Ollama (Python)
```python
from playwright.sync_api import sync_playwright
import requests
import json

def scrape_with_llm(url, prompt):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        
        # Extrair HTML
        html = page.content()
        browser.close()
        
        # Enviar para LLM
        response = requests.post('http://localhost:11434/api/generate', json={
            "model": "qwen2.5-coder:7b",
            "prompt": f"Extraia dados desta página HTML:\\n{html[:5000]}\\n\\n{prompt}",
            "stream": False
        })
        
        return response.json()['response']

# Uso
data = scrape_with_llm(
    "https://example.com/products",
    "Extraia lista de produtos em JSON com nome, preço e rating"
)
print(data)
```

### Exemplo 2: LangChain + Playwright
```python
from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
from playwright.sync_api import sync_playwright

def playwright_scraper(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        content = page.content()
        browser.close()
        return content[:2000]  # Limitar tamanho

tools = [
    Tool(
        name="WebScraper",
        func=playwright_scraper,
        description="Scrapes web pages and returns HTML content"
    )
]

llm = ChatOpenAI(model="gpt-4")
agent = initialize_agent(tools, llm, agent="zero-shot-react-description")

result = agent.run("Extraia informações sobre Python da Wikipedia")
```

## GPT-4 Vision para Scraping Visual

```python
import base64
from playwright.sync_api import sync_playwright
from openai import OpenAI

def scrape_with_vision(url, prompt):
    # Capturar screenshot
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        screenshot = page.screenshot()
        browser.close()
    
    # Encode para base64
    image_b64 = base64.b64encode(screenshot).decode()
    
    # Enviar para GPT-4V
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_b64}"
                    }
                }
            ]
        }]
    )
    
    return response.choices[0].message.content

# Uso
data = scrape_with_vision(
    "https://amazon.com/product/123",
    "Extraia todos os detalhes do produto em JSON"
)
```

## Implementação Completa: Smart Scraper Agent

```python
from playwright.sync_api import sync_playwright
from typing import Dict, List
import requests
import json

class SmartScraperAgent:
    def __init__(self, llm_url="http://localhost:11434/api/generate", model="qwen2.5-coder:7b"):
        self.llm_url = llm_url
        self.model = model
    
    def scrape(self, url: str, schema: Dict) -> Dict:
        # 1. Navegar e extrair HTML
        html = self._fetch_page(url)
        
        # 2. Gerar prompt com schema
        prompt = self._create_extraction_prompt(html, schema)
        
        # 3. Extrair dados via LLM
        data = self._llm_extract(prompt)
        
        return data
    
    def _fetch_page(self, url: str) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            html = page.content()
            browser.close()
            return html
    
    def _create_extraction_prompt(self, html: str, schema: Dict) -> str:
        schema_desc = json.dumps(schema, indent=2)
        return f"""Extraia dados desta página HTML seguindo o schema JSON:

Schema desejado:
{schema_desc}

HTML (primeiros 3000 caracteres):
{html[:3000]}

Retorne APENAS um JSON válido seguindo o schema."""
    
    def _llm_extract(self, prompt: str) -> Dict:
        response = requests.post(self.llm_url, json={
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        })
        
        result = response.json()['response']
        return json.loads(result)

# Uso
agent = SmartScraperAgent()

schema = {
    "products": [{
        "name": "string",
        "price": "number",
        "rating": "number",
        "in_stock": "boolean"
    }]
}

data = agent.scrape("https://example.com/products", schema)
print(json.dumps(data, indent=2))
```

## Melhores Práticas

1. **Chunking de HTML**: Limitar tamanho do HTML enviado ao LLM
2. **Schema Claro**: Definir schemas JSON precisos
3. **Retry Logic**: Implementar retentativas para falhas
4. **Caching**: Cachear resultados para reduzir custos
5. **Rate Limiting**: Respeitar limites de API
6. **Error Handling**: Tratar erros de parsing e timeout

## Recursos Adicionais

- **llm-scraper**: https://github.com/mishushakov/llm-scraper
- **ScrapeGraphAI**: https://github.com/VinciGit00/Scrapegraph-ai
- **Crawl4AI**: https://github.com/unclecode/crawl4ai
- **Browser Use**: https://github.com/browser-use/browser-use
- **LangChain Docs**: https://python.langchain.com/docs/use_cases/web_scraping

## Conclusão

Smart Web Scraping com AI Agents + LLM oferece:
- ✅ Maior flexibilidade e adaptabilidade
- ✅ Menos código de manutenção
- ✅ Melhor compreensão semântica
- ✅ Extração baseada em linguagem natural
- ⚠️ Custos de API LLM
- ⚠️ Latência maior que scraping tradicional
