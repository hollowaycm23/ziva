$env:QDRANT_VECTOR_SIZE = "1024"
$env:EMBEDDING_MODEL = "qwen3-embedding:0.6b"
$env:ZIVA_LLM_MODEL = "qwen3:14b"
$env:MODEL_NAME = "qwen3:14b"

C:\Python314\python.exe -m uvicorn api.server:app --host 0.0.0.0 --port 8000 2>D:\Stark\server_err.txt
