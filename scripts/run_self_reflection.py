#!/usr/bin/env python3
from core.thought_police import ThoughtPolice
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("🔮 Starting Ziva Metacognition Cycle (Thought Police)...")
    try:
        police = ThoughtPolice()
        police.run_cycle()
        print("✨ Cycle Complete.")
    except Exception as e:
        print(f"❌ Critical Error in Thought Police: {e}")


if __name__ == "__main__":
    main()
