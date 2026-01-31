import sys
import os

# Add root to sys.path
sys.path.append(os.getcwd())

from core.graph.ziva_graph import app
from langchain_core.messages import HumanMessage

def verify_gate():
    print("🧪 Starting Cognitive Gate Verification...")
    
    # Query designed to trigger the "euler" or "rigid body" heuristic in analyze_node
    query = "Analyze the Euler rotation for a rigid body with I=[1, 2, 3] and omega0=[1, 0.1, 0.1]."
    
    inputs = {"input": query}
    
    gate_triggered = False
    gate_passed = False
    
    print(f"   Query: {query}")
    
    try:
        for output in app.stream(inputs):
            for key, value in output.items():
                print(f"   ➡ Node Visited: {key}")
                if key == "cognitive_gate_node":
                    gate_triggered = True
                    res = value.get("gate_result", {})
                    print(f"      GATE OUTPUT: {res}")
                    if res.get("passed"):
                        gate_passed = True
                
                if key == "respond_node":
                    print(f"      Response: {value.get('response')[:100]}...")

        if gate_triggered:
            print("✅ SUCCESS: Cognitive Gate was triggered!")
            if gate_passed:
                print("✅ SUCCESS: Physics validation PASSED.")
            else:
                print("⚠️ WARNING: Physics validation FAILED (expected for random params?).")
        else:
            print("❌ FAILURE: Cognitive Gate was NOT triggered.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ FAILURE: Graph execution crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    verify_gate()
