#!/usr/bin/env python3
from core.dreamer import Dreamer
import sys
import os
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("🌙 Initiating Ziva Dream Cycle...")
    try:
        dreamer = Dreamer()
        start = time.time()
        dreamer.dream()
        print(f"☀️  Waking up. Cycle took {time.time() - start:.2f}s.")
    except Exception as e:
        print(f"❌ Nightmare (Error): {e}")


if __name__ == "__main__":
    main()
