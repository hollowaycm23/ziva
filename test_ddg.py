# Test DuckDuckGo
try:
    from ddgs import DDGS
    print("Using ddgs library")
except ImportError:
    from duckduckgo_search import DDGS
    print("Using duckduckgo_search library")

with DDGS() as ddgs:
    gen = ddgs.text('test query', max_results=3)
    if gen:
        for r in gen:
            print(f"Keys: {list(r.keys())}")
            print(f"  title={r.get('title')}")
            print(f"  href={r.get('href')}")
            print(f"  body={r.get('body')[:100] if r.get('body') else None}")
            break
    else:
        print("No results (None)")
