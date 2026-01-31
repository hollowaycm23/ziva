import time
import shutil
import logging
import threading
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("BackupSystem")


class SessionBackup:
    """
    Manages periodic backups of the agent's SQLite database and relevant
    persisted state.
    """

    def __init__(self, db_path: str = "/home/holloway/ziva/data/ziva.db",
                 backup_dir: str = "/home/holloway/ziva/backups/sessions"):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.running = False
        self.thread = None
        self.interval = 300  # 5 minutes default

    def start(self, interval_seconds: int = 300):
        """Starts the background backup thread."""
        self.interval = interval_seconds
        self.running = True
        self.thread = threading.Thread(target=self._backup_loop, daemon=True)
        self.thread.start()
        logger.info(f"Backup system started. Interval: {self.interval}s")

    def stop(self):
        """Stops the backup thread."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
            logger.info("Backup system stopped.")

    def _backup_loop(self):
        while self.running:
            try:
                time.sleep(self.interval)
                if not self.running:
                    break
                self.perform_backup()
            except Exception as e:
                logger.error(f"Error in backup loop: {e}")

    def perform_backup(self):
        """Executes a single backup operation."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"ziva_backup_{timestamp}.db"

            # Simple file copy (SQLite is robust, but WAL mode recommended for hot backups)
            # For this MVP, copy is acceptable if traffic is low.
            if self.db_path.exists():
                shutil.copy2(self.db_path, backup_file)

                # Cleanup old backups (keep last 5)
                backups = sorted(self.backup_dir.glob("ziva_backup_*.db"))
                if len(backups) > 5:
                    for old_backup in backups[:-5]:
                        old_backup.unlink()

                logger.info(f"Session backup created: {backup_file.name}")
            else:
                logger.warning(
                    f"Database file not found at {self.db_path}, skipping backup.")

        except Exception as e:
            logger.error(f"Backup failed: {e}")


# Global instance for easy import
backup_system = SessionBackup()
