from core.autonomic import AutonomicSystem
import sys
import os
import time
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MockAutonomic(AutonomicSystem):
    def __init__(self):
        super().__init__()
        # Override for fast testing
        self.INTERVAL_THOUGHT_POLICE = 2  # 2 seconds
        self.INTERVAL_DREAM_CYCLE = 5     # 5 seconds


def test_system():
    print("🫀 Testing Autonomic Nervous System...")
    auto = MockAutonomic()
    auto.start()

    print("⏳ Waiting for heavy pulses (10s)...")
    time.sleep(10)

    auto.stop()
    print("✅ System stopped. Check logs above for 'Autonomic Trigger'.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_system()
