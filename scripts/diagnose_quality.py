import sys
import os
import time

# Force VERBOSE for capture
os.environ["ZIVA_VERBOSE"] = "true"

# Add path
sys.path.append(os.getcwd())

from core.vector_store import VectorStore
from core.llm import LLMService

# Instantiate directly
vs = VectorStore(collection_name="main_knowledge")
embedder = LLMService(model="nomic-embed-text:latest")
from core.agent.nodes import retrieve, generate
from core.agent.state import AgentState

# Test Battery
TEST_CASES = [
    {"q": "O que sao Pikas?", "type": "Ambiguous/Bio"},
    {"q": "Qual a formula da teoria dos 3 corpos?", "type": "Scientific/Factual"},
    {"q": "Quem e o fabricante da moto CG?", "type": "General Knowledge"},
    {"q": "Quem sou eu?", "type": "Episodic/User Identity"},
    {"q": "Resuma as noticias de tecnologia de hoje", "type": "Tool/News"}
]

def analyze_retrieval_quality(question, docs):
    print(f"\n🧐 Analyzing Retrieval for: '{question}'")
    if not docs:
        print("🔴 FAIL: No documents retrieved.")
        return 0
    
    print(f"✅ Retrieved {len(docs)} docs.")
    # Check relevance (Naive keyword check for diagnostic)
    keywords = question.lower().split()
    relevant_count = 0
    for d in docs:
        if any(k in d.lower() for k in keywords if len(k) > 3):
            relevant_count += 1
            
    print(f"📊 Keyword Relevance: {relevant_count}/{len(docs)} docs contain query terms.")
    if relevant_count == 0:
        print("🔴 CRITICAL: Potential Semantic Drift (Docs retrieved but irrelevant).")
        for i, d in enumerate(docs[:2]):
            print(f"   Doc {i}: {d[:100]}...")
    return relevant_count

def run_diagnostic():
    print("🏥 Starting Ziva Core Diagnostic...")
    print("====================================")
    
    results = {}
    
    for case in TEST_CASES:
        q = case["q"]
        print(f"\n🧪 Testing: {q} ({case['type']})")
        
        state = AgentState(question=q, chat_history=[])
        
        # 1. Test Retrieval
        t0 = time.time()
        try:
            retrieval_result = retrieve(state)
            docs = retrieval_result.get("documents", [])
            retrieval_time = time.time() - t0
            
            # Analyze
            score = analyze_retrieval_quality(q, docs)
            
            # 2. Test Generation
            state["documents"] = docs
            gen_result = generate(state)
            answer = gen_result.get("generation", "")
            
            print(f"💬 Answer: {answer[:150]}...")
            
            if "não sei" in answer.lower() or "desculpe" in answer.lower():
                print("⚠️ Model Refusal Detected.")
            
        except Exception as e:
            print(f"🔴 CRASH: {e}")
            import traceback
            traceback.print_exc()

    print("\n====================================")
    print("Diagnostic Complete.")

if __name__ == "__main__":
    run_diagnostic()
