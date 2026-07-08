import requests
for port in [8080, 8082]:
    try:
        url = f'http://localhost:{port}/search?q=test&format=json'
        r = requests.get(url, timeout=5)
        print(f'Port {port}: Status {r.status_code}')
        data = r.json()
        results = data.get('results', [])
        print(f'  Results: {len(results)}')
        if results:
            print(f'  First title: {results[0].get("title", "?")}')
            print(f'  First snippet: {results[0].get("content", "")[:100]}')
    except Exception as e:
        print(f'Port {port}: Error - {e}')
