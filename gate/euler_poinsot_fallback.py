#!/usr/bin/env python3
import sys
import json
import math

def kinetic_energy(I1, I2, I3, w1, w2, w3):
    return 0.5 * (I1 * w1**2 + I2 * w2**2 + I3 * w3**2)

def angular_momentum(I1, I2, I3, w1, w2, w3):
    return math.sqrt((I1 * w1)**2 + (I2 * w2)**2 + (I3 * w3)**2)

def euler_derivatives(I1, I2, I3, w1, w2, w3):
    dw1 = ((I2 - I3) * w2 * w3) / I1
    dw2 = ((I3 - I1) * w3 * w1) / I2
    dw3 = ((I1 - I2) * w1 * w2) / I3
    return dw1, dw2, dw3

def solve_euler():
    try:
        # 1. Read input
        input_data = sys.stdin.read()
        if not input_data:
            raise ValueError("Empty input")
        
        data = json.loads(input_data)
        
        I1 = float(data.get("I1", 1.0))
        I2 = float(data.get("I2", 1.0))
        I3 = float(data.get("I3", 1.0))
        omega0 = data.get("omega0", [0.0, 0.0, 0.0])
        dt = float(data.get("dt", 0.01))
        total_time = float(data.get("total_time", 10.0))
        tolerance = float(data.get("tolerance", 1e-4))
        
        w1, w2, w3 = omega0
        
        # Initial Invariants
        E_init = kinetic_energy(I1, I2, I3, w1, w2, w3)
        L_init = angular_momentum(I1, I2, I3, w1, w2, w3)
        
        steps = int(total_time / dt)
        max_error = 0.0
        
        # RK2 Integration
        for _ in range(steps):
            dw1, dw2, dw3 = euler_derivatives(I1, I2, I3, w1, w2, w3)
            
            # Predictor
            w1_p = w1 + dw1 * dt
            w2_p = w2 + dw2 * dt
            w3_p = w3 + dw3 * dt
            
            dw1_p, dw2_p, dw3_p = euler_derivatives(I1, I2, I3, w1_p, w2_p, w3_p)
            
            # Corrector
            w1 += 0.5 * (dw1 + dw1_p) * dt
            w2 += 0.5 * (dw2 + dw2_p) * dt
            w3 += 0.5 * (dw3 + dw3_p) * dt
            
            # Check Invariants
            E_curr = kinetic_energy(I1, I2, I3, w1, w2, w3)
            L_curr = angular_momentum(I1, I2, I3, w1, w2, w3)
            
            err_E = abs(E_curr - E_init) / (E_init + 1e-9)
            err_L = abs(L_curr - L_init) / (L_init + 1e-9)
            
            max_error = max(max_error, err_E, err_L)
            
        passed = max_error < tolerance
        
        output = {
            "passed": passed,
            "max_error": max_error,
            "energy_init": E_init,
            "energy_final": kinetic_energy(I1, I2, I3, w1, w2, w3),
            "momentum_init": L_init,
            "momentum_final": angular_momentum(I1, I2, I3, w1, w2, w3),
            "message": "Simulation Complete" if passed else f"FAILED: Error {max_error:.2e} > {tolerance:.2e}"
        }
        
        print(json.dumps(output))
        
    except Exception as e:
        error_out = {
            "passed": False,
            "message": str(e),
            "max_error": -1.0
        }
        print(json.dumps(error_out))

if __name__ == "__main__":
    solve_euler()
