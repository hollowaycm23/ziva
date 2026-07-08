import requests, json

# Test SearxNG
print("=== SEARXNG ===")
for port in [8080, 8082]:
    try:
        url = f'http://localhost:{port}/search'
        params = {'q': 'Poco X7 Pro 256GB preço Brasil 2026', 'format': 'json', 'language': 'pt-BR'}
        r = requests.get(url, params=params, timeout=5)
        print(f'Port {port}: Status {r.status_code}')
        data = r.json()
        results = data.get('results', [])
        print(f'  Results: {len(results)}')
        for res in results[:3]:
            print(f'  - {res.get("title","?")}')
            print(f'    Snippet: {res.get("content","")[:150]}')
            print(f'    URL: {res.get("url","")}')
    except Exception as e:
        print(f'Port {port}: Error - {type(e).__name__}: {e}')

# Test DuckDuckGo directly
print("\n=== DUCKDUCKGO ===")
try:
    from duckduckgo_search import DDGS
    with DDGS() as ddgs:
        results = list(ddgs.text('Poco X7 Pro 256GB preço Brasil 2026', max_results=5))
        print(f'Results: {len(results)}')
        for r in results[:3]:
            print(f'  - {r.get("title","?")}')
            print(f'    Snippet: {r.get("body","")[:150]}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')

# Test with simpler query
print("\n=== SEARXNG (Intel comparison) ===")
for port in [8080, 8082]:
    try:
        params = {'q': 'Intel Core i7-12700K vs Intel Core Ultra 7 265K comparison', 'format': 'json'}
        r = requests.get(f'http://localhost:{port}/search', params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            results = data.get('results', [])
            print(f'Port {port}: {len(results)} results')
            for res in results[:3]:
                print(f'  - {res.get("title","?")}')
                print(f'    Snippet: {res.get("content","")[:200]}')
    except Exception as e:
        print(f'Port {port}: Error - {e}')
