import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from core.agent.graph import build_agent
import asyncio

def run_query():
    print("🤖 Ziva Agent Query Runner")
    print("--------------------------")
    
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "Quem é o fabricante da moto CG 125?"
    print(f"❓ Question: {question}")
    
    app = build_agent()
    
    # Run the graph
    # Depending on how the graph is structured, it might return a stream or a final state
    result = app.invoke({"question": question})
    
    print("\n🏁 Final Result:")
    print("----------------")
    print(result.get("generation", "No generation found"))
    
    # Check if retrieval was used
    docs = result.get("documents", [])
    if docs:
        print(f"\n📚 Documents Retrieved: {len(docs)}")
        for i, doc in enumerate(docs[:3]): # Show top 3
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            print(f"   {i+1}. {content[:100]}...")

if __name__ == "__main__":
    run_query()
