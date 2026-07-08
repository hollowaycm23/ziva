import sys, os, warnings, logging
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'
logging.disable(logging.CRITICAL)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import config
em = config.get_llm_provider('agent.embedding_model')
print('Embedding config:', em)

# Test via Ollama native API
import requests
r = requests.post('http://localhost:11434/api/embeddings', json={
    'model': 'qwen3-embedding:0.6b',
    'prompt': 'teste'
}, timeout=30)
d = r.json()
print('Ollama embeddings API response keys:', list(d.keys()))
if 'embedding' in d:
    print(f'  dim={len(d["embedding"])}')
else:
    print(f'  error: {d}')

# Test via OpenAI-compatible API
r2 = requests.post('http://localhost:11434/v1/embeddings', json={
    'model': 'qwen3-embedding:0.6b',
    'input': 'teste'
}, timeout=30)
d2 = r2.json()
print('\nOpenAI-compatible embeddings API:')
if 'data' in d2 and len(d2['data']) > 0:
    emb = d2['data'][0]['embedding']
    print(f'  dim={len(emb)}')
else:
    print(f'  error: {d2}')

# Check LLMService embedding
from core.llm import LLMService
llm_svc = LLMService()
print(f'\nLLMService embedding model: {llm_svc.embedding_model}')
print(f'LLMService api_base: {llm_svc.api_base}')
emb = llm_svc.embedding('teste')
print(f'LLMService embedding result: {type(emb)}')
if emb:
    print(f'  dim={len(emb)}')
else:
    print('  returned None or empty')
