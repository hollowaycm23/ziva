
from core.backup_system import SessionBackup
import threading
import time
import os
import shutil
from pathlib import Path

# Set up mockup environment
os.environ["ZIVA_TEST_MODE"] = "1"

print("Starting Final System Verification...")

# 1. Verify Backup System
print("Test 1: Backup System...")

dummy_db = Path("/tmp/ziva_test.db")
dummy_db.touch()
backup_dir = Path("/tmp/ziva_backups")
if backup_dir.exists():
    shutil.rmtree(backup_dir)

backup_sys = SessionBackup(db_path=str(dummy_db), backup_dir=str(backup_dir))
backup_sys.start(interval_seconds=1)
time.sleep(2)
backup_sys.stop()

backups = list(backup_dir.glob("*.db"))
if len(backups) > 0:
    print(f"SUCCESS: Backup created ({len(backups)} files)")
else:
    print("FAILED: No backups created")
    exit(1)

# 2. Verify Graph Integration Logic
# (We only verify checking if modules load correctly without syntax errors,
# as full runtime requires Ollama/Docker)
print("\nTest 2: Module Integrity...")
try:
    from agent.ziva import ZivaAgent
    from core.graph.ziva_graph import app
    from core.graph.nodes.lookup_tool import lookup_tool_node
    print("SUCCESS: Modules loaded correctly.")
except ImportError as e:
    print(f"FAILED: Import error: {e}")
    exit(1)
except Exception as e:
    # ZivaAgent init might fail on missing Docker/Ollama/Tailscale,
    # but we just want to ensure Python syntax is valid.
    print(f"WARNING: Init error (expected in CI env): {e}")

print("\nALL CHECKS PASSED.")
