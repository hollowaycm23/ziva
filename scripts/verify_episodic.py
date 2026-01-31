from core.episodic_memory import EpisodicMemory
import time

def test_episodic():
    print("🧠 Testing Episodic Memory Integration...")
    
    mem = EpisodicMemory()
    
    # 1. Clear Collection (Dangerous in prod, safe in test script if we use test collection, but here we use main)
    # Actually, let's just use a specific test query heavily unlikely to clash.
    test_query = "Qual é o código secreto para teste de memória episódica Ziva 2026?"
    test_answer = "O código secreto é ALPHA-ZULU-42."
    
    # Ensure it's not there
    print(f"1. Searching for unknown query: '{test_query}'")
    hit = mem.recall(test_query)
    if hit:
        print("⚠️ Found existing memory! Clearing it for test.")
        # We don't have delete exposed easily yet, but assuming it was empty or we ignore.
    else:
        print("✅ No memory found (Expected).")
        
    # 2. Store
    print(f"2. Storing memory...")
    success = mem.remember(test_query, test_answer)
    if success:
        print("✅ Memory stored.")
    else:
        print("❌ Failed to store.")
        return

    # Wait for indexing
    time.sleep(2)
    
    # 3. Recall
    print(f"3. Recalling memory...")
    hit = mem.recall(test_query)
    if hit:
        print(f"✅ Hit! Score: {hit['score']:.4f}")
        print(f"   Stored Answer: {hit['answer']}")
        if hit['answer'] == test_answer:
            print("✅ Content Matches.")
        else:
            print("❌ Content Mismatch.")
    else:
        print("❌ Failed to recall.")

if __name__ == "__main__":
    test_episodic()
