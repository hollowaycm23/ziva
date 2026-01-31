#!/usr/bin/env python3
"""
Verify Generalist Knowledge
Queries Ziva with questions from various domains to test RAG retrieval and answer quality.
"""

import sys
import os
import time
from typing import List, Dict

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.ziva import ZivaAgent
from core.rag_helper import RAGHelper

def test_knowledge():
    # questions to test different domains
    test_cases = [
        {
            "domain": "Space Habitats",
            "question": "What is a Bernal Sphere and how does it provide artificial gravity?",
            "keywords": ["Bernal", "gravity", "sphere"]
        },
        {
            "domain": "Civilization Scales",
            "question": "Explain the Kardashev Scale and the energy consumption of a Type II civilization.",
            "keywords": ["Kardashev", "Type II", "energy", "star"]
        },
        {
            "domain": "Orbital Dynamics",
            "question": "Describe the Three-Body Problem and why it is chaotic.",
            "keywords": ["three-body", "chaos", "orbit"]
        },
        {
            "domain": "Megastructures",
            "question": "What are the design parameters of a Stanford Torus?",
            "keywords": ["Stanford", "Torus", "habitat"]
        }
    ]

    rag = RAGHelper()
    print("🧠 Initializing Ziva Knowledge Verification...")
    
    results = []

    for test in test_cases:
        print(f"\n🧪 Testing Domain: {test['domain']}")
        print(f"   Question: {test['question']}")
        
        # 1. Test Retrieval Directly first
        print("   🔍 Checking RAG Retrieval quality...")
        memories = rag.search_memories(test['question'], limit=3)
        
        found_keywords = False
        context_text = ""
        if memories:
            print(f"   ✅ Retrieved {len(memories)} chunks.")
            for mem in memories:
                context_text += mem.get('payload', {}).get('text', '') + " "
                # print(f"      - {mem.payload.get('title', 'No Title')}")
            
            # Check keywords
            missing = []
            for kw in test['keywords']:
                if kw.lower() in context_text.lower():
                    found_keywords = True
                else:
                    missing.append(kw)
            
            if len(missing) == 0:
                print("   ✅ All keywords found in context!")
            elif len(missing) < len(test['keywords']):
                print(f"   ⚠️ Some keywords missing: {missing}, but found others.")
            else:
                print(f"   ❌ Keywords missing: {missing}. Context might be irrelevant.")
        else:
            print("   ❌ No context retrieved!")

        results.append({
            "domain": test['domain'],
            "context_found": len(memories) > 0,
            "keywords_match": found_keywords
        })
        
    print("\n📊 Summary Results:")
    for r in results:
        status = "✅ PASS" if r['context_found'] and r['keywords_match'] else "❌ FAIL"
        print(f"{status} - {r['domain']}")

if __name__ == "__main__":
    test_knowledge()
