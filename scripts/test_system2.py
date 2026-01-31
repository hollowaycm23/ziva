from core.system2 import System2Thinking
import sys
import os
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("🧠 Testing System 2 Thinking (Mental Sandboxing)...")

    sys2 = System2Thinking()

    # query = "Solve logic puzzle: A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost?"
    # A classic trap for System 1 (often answers $0.10 incorrectly). System 2
    # should get $0.05.

    query = "Um bastão e uma bola custam R$ 1,10 no total. O bastão custa R$ 1,00 a mais que a bola. Quanto custa a bola?"

    start_time = time.time()
    rationale, answer = sys2.think_and_solve(query)
    end_time = time.time()

    print(f"\n⏱️  Time Taken: {end_time - start_time:.2f}s")
    print("-" * 50)
    print(f"📄 RATIONALE (Hidden Trace):\n{rationale}")
    print("-" * 50)
    print(f"🔥 FINAL ANSWER (User Facing):\n{answer}")
    print("-" * 50)

    if "0,05" in answer or "5 centavos" in answer or "$0.05" in answer:
        print("✅ SUCCESS: Logic Puzzle Solved Correctly!")
    else:
        print("⚠️  UNCERTAIN: Check output manually.")


if __name__ == "__main__":
    main()
