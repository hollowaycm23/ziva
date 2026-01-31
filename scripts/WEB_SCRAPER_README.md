# Web Scraper com Playwright

Script Python para fazer scraping de páginas web, incluindo sites dinâmicos que usam JavaScript (React, Vue, Angular, etc).

## Instalação

As dependências já estão instaladas no projeto Ziva:
- `playwright`
- Navegador Chromium

## Uso Básico

### Scraping Simples
```bash
python3 scripts/web_scraper.py https://example.com
```

### Extrair Elemento Específico
```bash
python3 scripts/web_scraper.py https://example.com --selector "article"
```

### Aguardar Elemento Carregar
```bash
python3 scripts/web_scraper.py https://example.com --wait-for ".content"
```

### Salvar Resultado em JSON
```bash
python3 scripts/web_scraper.py https://example.com --output resultado.json
```

## Exemplos Práticos

### 1. Extrair Título de Artigo
```bash
python3 scripts/web_scraper.py https://pt.wikipedia.org/wiki/Quasar --selector "h1"
```

### 2. Extrair Conteúdo Principal
```bash
python3 scripts/web_scraper.py https://github.com --selector "main"
```

### 3. Site com JavaScript (SPA)
```bash
python3 scripts/web_scraper.py https://react-app.com --wait-for "#app" --selector "#content"
```

## Uso Programático

```python
from scripts.web_scraper import scrape_page, scrape_multiple_pages

# Uma página
result = scrape_page("https://example.com", selector="article")
print(result['title'])
print(result['text'])

# Múltiplas páginas
urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
]
results = scrape_multiple_pages(urls, selector=".content")
```

## Recursos

- ✅ Suporta JavaScript/SPA
- ✅ Captura screenshot automaticamente
- ✅ Aguarda carregamento completo
- ✅ Extrai texto e HTML
- ✅ Salva resultado em JSON
- ✅ Processa múltiplas URLs

## Saída

O script retorna um dicionário com:
- `url`: URL da página
- `title`: Título da página
- `text`: Texto extraído (limitado a 2000 caracteres)
- `html_length`: Tamanho do HTML
- `screenshot`: Caminho do screenshot salvo

Screenshots são salvos em `tmp/screenshot_*.png`
