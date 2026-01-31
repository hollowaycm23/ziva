import sys
import os
import json
from unittest.mock import MagicMock

# Add root to sys.path
sys.path.append(os.getcwd())

# ----------------- CONFIGURING BACKEND -----------------
# Force LM Studio as per user requirement (NO OLLAMA)
os.environ["ZIVA_LLM_BACKEND"] = "lm_studio"
os.environ["ZIVA_LLM_BASE_URL"] = "http://100.104.242.35:1234/v1"
os.environ["ZIVA_LLM_MODEL"] = "qwen2.5-coder-7b-instruct" # Adjust if necessary
os.environ["MODEL_NAME"] = "qwen2.5-coder-7b-instruct"

# ----------------- MOCKING RAG TO AVOID HANGS -----------------
# We mock functionality before importing the graph to ensure isolation
sys.modules["rag.retrieval.research_augmenter"] = MagicMock()
mock_augmenter = MagicMock()
mock_augmenter.research.return_value = {"mock_source": "Physics Textbook"}
mock_augmenter.format_additional_info.return_value = "Mocked Physics Context: Euler equations describe rigid body rotation."
sys.modules["rag.retrieval.research_augmenter"].get_research_augmenter.return_value = mock_augmenter

from core.graph.ziva_graph import app
from langchain_core.messages import HumanMessage

def stress_test():
    print("🔥 STARTED: Hard Cognitive Stress Test (Euler-Poinsot Gate)\n")
    
    test_cases = [
        {
            "name": "CASE 1: CONSISTENT PHYSICS (Pass Expected)",
            # I1=1, I2=1, I3=1 (Sphere/Cube) -> Stable rotation. 
            # With equal inertia, euler derivs are 0. Energy is constant.
            "query": "Analyze Euler rotation: I=[1.0, 1.0, 1.0], omega0=[1.0, 1.0, 1.0], dt=0.01",
            "expect_pass": True
        },
        {
            "name": "CASE 2: BROKEN PHYSICS (Fail Expected)",
            # This is harder to forge via text to FORCE an error in a real simulation unless we inject bad params directly 
            # or if the user asks for impossible conditions.
            # But the Gate runs the simulation based on inputs.
            # Wait, the Gate verifies if the simulation *diverges* or if invariants hold for the *given* parameters.
            # Actually, the Gate runs a correct simulation. 
            # The test here is: Does the Gate TRIGGER?
            # And: Does the Gate correctly simulate and report?
            # A 'Fail' in the Gate usually means the params led to instability (unlikely with RK4 and reasonable time) 
            # OR the inputs were invalid (e.g. negative inertia).
            # Let's try Negative Inertia.
            "query": "Analyze Euler rotation: I=[-1.0, 2.0, 3.0], omega0=[1.0, 0.0, 0.0]",
            "expect_pass": False
        },
        {
            "name": "CASE 3: UNSTABLE AXIS (Pass Expected but Chaotic)",
            # Intermediate axis theorem (Tennis Racket Theorem). 
            # I1 < I2 < I3. Rotation around I2 is unstable.
            # Gate should still PASS (Energy is conserved even in unstable rotation), 
            # but it verifies our integration is good enough to track it.
            "query": "Analyze Euler rotation: I=[1.0, 2.0, 3.0], omega0=[0.01, 1.0, 0.01]",
            "expect_pass": True
        }
    ]
    
    results = []

    for test in test_cases:
        print(f"--- {test['name']} ---")
        inputs = {"input": test['query']}
        
        gate_seen = False
        gate_outcome = None
        
        try:
            for output in app.stream(inputs):
                for key, value in output.items():
                    if key == "cognitive_gate_node":
                        gate_seen = True
                        res = value.get("gate_result", {})
                        passed = res.get("passed")
                        gate_outcome = passed
                        
                        status = "✅ PASSED" if passed else f"❌ FAILED ({res.get('message')})"
                        print(f"      [GATE]: {status}")
                        
        except Exception as e:
            print(f"      [ERROR]: Execution crashed: {e}")
        
        # Verification
        success = False
        if test['expect_pass']:
            if gate_seen and gate_outcome is True: success = True
        else:
            if gate_seen and gate_outcome is False: success = True
            
        results.append((test['name'], success, gate_outcome))
        print(f"   Test Result: {'✅ SUCCESS' if success else '❌ FAILURE'}\n")

    print("\n--- SUMMARY ---")
    all_pass = True
    for name, success, outcome in results:
        mark = "✅" if success else "❌"
        outcome_str = "Passed" if outcome else "Failed"
        print(f"{mark} {name} -> Gate Outcome: {outcome_str}")
        if not success: all_pass = False
        
    if all_pass:
        print("\n🏆 ALL COGNITIVE TESTS PASSED. The Gate is holding.")
    else:
        print("\n⚠️ SOME TESTS FAILED. Check logic.")

if __name__ == "__main__":
    stress_test()
