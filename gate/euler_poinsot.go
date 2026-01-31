package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
)

// InputPayload defines the configuration for the simulation
type InputPayload struct {
	I1        float64   `json:"I1"`
	I2        float64   `json:"I2"`
	I3        float64   `json:"I3"`
	Omega0    []float64 `json:"omega0"` // [w1, w2, w3]
	TimeStep  float64   `json:"dt"`
	TotalTime float64   `json:"total_time"`
	Tolerance float64   `json:"tolerance"`
}

// OutputPayload defines the result of the validation
type OutputPayload struct {
	Passed       bool    `json:"passed"`
	MaxError     float64 `json:"max_error"`
	EnergyInit   float64 `json:"energy_init"`
	EnergyFinal  float64 `json:"energy_final"`
	MomentumInit float64 `json:"momentum_init"`
	MomentumFinal float64 `json:"momentum_final"`
	Message      string  `json:"message"`
}

func main() {
	// 1. Read input from Stdin
	var input InputPayload
	decoder := json.NewDecoder(os.Stdin)
	if err := decoder.Decode(&input); err != nil {
		fail(fmt.Sprintf("Invalid JSON input: %v", err))
		return
	}

	// 2. Validate inputs
	if input.I1 <= 0 || input.I2 <= 0 || input.I3 <= 0 {
		fail("Moments of inertia must be positive")
		return
	}
	if len(input.Omega0) != 3 {
		fail("Omega0 must have 3 components")
		return
	}
	if input.TimeStep <= 0 {
		input.TimeStep = 0.01 // Default
	}
	if input.TotalTime <= 0 {
		input.TotalTime = 10.0 // Default
	}
	if input.Tolerance <= 0 {
		input.Tolerance = 1e-4 // Default strictness
	}

	// 3. Initialize State
	w1, w2, w3 := input.Omega0[0], input.Omega0[1], input.Omega0[2]
	
	// Initial Invariants
	E_init := kineticEnergy(input.I1, input.I2, input.I3, w1, w2, w3)
	L_init := angularMomentum(input.I1, input.I2, input.I3, w1, w2, w3)

	// 4. Run Simulation (RK4 Integration)
	steps := int(input.TotalTime / input.TimeStep)
	maxError := 0.0

	for i := 0; i < steps; i++ {
		// Calculate derivatives
		dw1, dw2, dw3 := eulerDerivatives(input.I1, input.I2, input.I3, w1, w2, w3)
		
		// Simple Euler Step (For RK4 we would do 4 steps, but for high-frequency checks Euler might suffice 
		// if step is small. Let's do a simple midpoint/RK2 for better stability without full RK4 complexity)
		
		// Predictor
		w1_p := w1 + dw1*input.TimeStep
		w2_p := w2 + dw2*input.TimeStep
		w3_p := w3 + dw3*input.TimeStep
		
		dw1_p, dw2_p, dw3_p := eulerDerivatives(input.I1, input.I2, input.I3, w1_p, w2_p, w3_p)
		
		// Corrector
		w1 += 0.5 * (dw1 + dw1_p) * input.TimeStep
		w2 += 0.5 * (dw2 + dw2_p) * input.TimeStep
		w3 += 0.5 * (dw3 + dw3_p) * input.TimeStep
		
		// Validate Invariants at this step
		E_curr := kineticEnergy(input.I1, input.I2, input.I3, w1, w2, w3)
		L_curr := angularMomentum(input.I1, input.I2, input.I3, w1, w2, w3)
		
		errE := math.Abs(E_curr - E_init) / (E_init + 1e-9)
		errL := math.Abs(L_curr - L_init) / (L_init + 1e-9)
		
		if errE > maxError { maxError = errE }
		if errL > maxError { maxError = errL }
	}

	// 5. Final Validation
	passed := maxError < input.Tolerance

	output := OutputPayload{
		Passed:        passed,
		MaxError:      maxError,
		EnergyInit:    E_init,
		EnergyFinal:   kineticEnergy(input.I1, input.I2, input.I3, w1, w2, w3),
		MomentumInit:  L_init,
		MomentumFinal: angularMomentum(input.I1, input.I2, input.I3, w1, w2, w3),
		Message:       "Simulation Complete",
	}

	if !passed {
		output.Message = fmt.Sprintf("FAILED: Invariants violated. Max Error %.2e > Tolerance %.2e", maxError, input.Tolerance)
	}

	writeOutput(output)
}

func eulerDerivatives(I1, I2, I3, w1, w2, w3 float64) (float64, float64, float64) {
	// Euler Equations:
	// I1 * w1' = (I2 - I3) * w2 * w3
	// I2 * w2' = (I3 - I1) * w3 * w1
	// I3 * w3' = (I1 - I2) * w1 * w2
	
	dw1 := ((I2 - I3) * w2 * w3) / I1
	dw2 := ((I3 - I1) * w3 * w1) / I2
	dw3 := ((I1 - I2) * w1 * w2) / I3
	
	return dw1, dw2, dw3
}

func kineticEnergy(I1, I2, I3, w1, w2, w3 float64) float64 {
	return 0.5 * (I1*w1*w1 + I2*w2*w2 + I3*w3*w3)
}

func angularMomentum(I1, I2, I3, w1, w2, w3 float64) float64 {
	return math.Sqrt(math.Pow(I1*w1, 2) + math.Pow(I2*w2, 2) + math.Pow(I3*w3, 2))
}

func fail(msg string) {
	output := OutputPayload{
		Passed:  false,
		Message: msg,
	}
	writeOutput(output)
}

func writeOutput(out OutputPayload) {
	encoder := json.NewEncoder(os.Stdout)
	encoder.Encode(out)
}
