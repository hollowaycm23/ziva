import os
import sys
import traceback

# Garante que o diretório atual está no path
sys.path.append(os.getcwd())

from core.vector_stores.factory import get_vector_store
import numpy as np

def test_backend(name):
    print(f"\n--- Testando Backend: {name} ---")
    os.environ["ZIVA_VECTOR_STORE_BACKEND"] = name
    
    try:
        store = get_vector_store(collection_name=f"test_{name}")
        print(f"✅ Store {name} inicializada")
        
        text = "O beija-flor é o único pássaro que voa para trás."
        emb = np.random.rand(768).tolist()
        
        print("DEBUG: Chamando add_text...")
        point_id = store.add_text(text, emb)
        if point_id:
            print(f"✅ Texto adicionado (ID: {point_id})")
        else:
            print("⚠️ Texto já existia ou erro na adição")
            
        print("DEBUG: Chamando search...")
        results = store.search(emb, limit=1)
        if results and results[0]['text'] == text:
            print(f"✅ Busca retornou o texto correto (Score: {results[0]['score']:.4f})")
        else:
            print(f"❌ Erro na busca. Resultados: {results}")
            
    except Exception as e:
        print(f"❌ Erro no backend {name}: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_backend("faiss")
