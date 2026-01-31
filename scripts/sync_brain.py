#!/usr/bin/env python3
import os
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SyncBrain")

DEFAULT_TARGET = "holloway@falcon"
REMOTE_PATH = "~/ziva_deploy"


def sync_code(target):
    """
    Synchronizes code to remote node using rsync.
    """
    logger.info(f"🧠 Syncing Ziva Brain to {target}...")

    # Source is current directory (project root)
    source = os.getcwd() + "/"
    destination = f"{target}:{REMOTE_PATH}/"

    # Rsync command with exclusions
    cmd = [
        "rsync", "-avP",
        "--exclude", "__pycache__",
        "--exclude", "*.pyc",
        "--exclude", ".git",
        "--exclude", ".env",  # Don't overwrite local env secrets blindly
        "--exclude", "venv",
        "--exclude", "models",  # Models are heavy, managed via pull
        "--exclude", "brain",  # Artifacts stay local
        "--exclude", "db_data",  # Don't touch remote DB
        source,
        destination
    ]

    try:
        subprocess.run(cmd, check=True)
        logger.info("✅ File Sync Complete.")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Sync Failed: {e}")
        sys.exit(1)


def restart_remote(target):
    """
    Restarts the remote Ziva application to apply changes.
    """
    logger.info("🔄 Restarting Remote Ziva Node...")

    # Command to restart container
    ssh_cmd = [
        "ssh", target,
        f"cd {REMOTE_PATH} && docker compose restart ziva-api"
    ]

    try:
        subprocess.run(ssh_cmd, check=True)
        logger.info("✅ Remote Node Restarted with New Brain!")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Restart Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TARGET

    print(f"🦅 Gabrielle Uplift Tool (Targets: {target})")
    sync_code(target)

    # Optional: ask before restart? No, speed is key.
    restart_remote(target)
