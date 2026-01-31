import subprocess
import json
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("CognitiveGate")

class EulerPoinsotGate:
    """
    Interface to the external Euler-Poinsot benchmark gate.
    Enforces physical consistency in reasoning.
    """
    
    def __init__(self, gate_path: str = None):
        if gate_path:
            self.gate_binary = gate_path
        else:
            # Default to ziva/gate/euler_gate
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.gate_binary = os.path.join(base_dir, "gate", "euler_gate")

    def check_physics(self, I: List[float], omega0: List[float], dt: float = 0.01, total_time: float = 10.0) -> Dict:
        """
        Runs the cognitive check.
        Returns Dict with keys: 'passed', 'message', 'max_error'
        """
        payload = {
            "I1": I[0],
            "I2": I[1],
            "I3": I[2],
            "omega0": omega0,
            "dt": dt,
            "total_time": total_time,
            "tolerance": 1e-4
        }
        
        input_json = json.dumps(payload)
        
        try:
            if not os.path.exists(self.gate_binary):
                return {"passed": False, "message": f"Gate binary not found at {self.gate_binary}"}

            process = subprocess.Popen(
                [self.gate_binary],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=input_json)
            
            if process.returncode != 0:
                return {"passed": False, "message": f"Gate crashed: {stderr}"}
                
            result = json.loads(stdout)
            return result
            
        except Exception as e:
            logger.error(f"Gate execution failed: {e}")
            return {"passed": False, "message": f"Internal Error: {str(e)}"}

# Example Usage Node for LangGraph
def cognitive_gate_node(state):
    """
    LangGraph node that acts as a gate.
    Expected state: {"physics_proposal": {...}}
    Updates state: {"gate_result": {...}}
    """
    proposal = state.get("physics_proposal")
    if not proposal:
        return {"gate_result": {"passed": True, "message": "No physics to check (Skipped)"}}
    
    gate = EulerPoinsotGate()
    
    # Extract params (assuming agent structured them correctly)
    I = proposal.get("inertia", [1.0, 1.0, 1.0])
    w0 = proposal.get("velocity", [0.0, 0.0, 0.0])
    
    result = gate.check_physics(I, w0)
    
    return {"gate_result": result}
