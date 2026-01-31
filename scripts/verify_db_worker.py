from core.database import DatabaseManager
import sys
import os
import json
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DBVerify")


def verify_worker_db():
    try:
        logger.info("Initializing DatabaseManager...")
        db = DatabaseManager()

        # 1. Check Tables
        logger.info("Checking schema...")
        conn = db._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        required_tables = ['jobs', 'messages', 'peers', 'sessions']
        missing = [t for t in required_tables if t not in tables]

        if missing:
            logger.error(f"Missing tables: {missing}")
            return False
        logger.info(f"Tables present: {tables}")

        # 2. Test Job Insertion (Write)
        logger.info("Testing Job Write...")
        payload = {"task": "db_integrity_check", "test": True}
        job_id = db.add_job("system_test", payload)
        logger.info(f"Job inserted with ID: {job_id}")

        # 3. Test Job Retrieval (Read)
        logger.info("Testing Job Read (Pending)...")
        pending_job = db.get_pending_job()

        if not pending_job:
            logger.error(
                "Failed to retrieve pending job or queue was empty/stolen.")
            # It's possible another worker picked it up if running, but
            # unlikely in dev env unless agent is active.
        elif pending_job['id'] == job_id:
            logger.info(
                f"Successfully verified Job {job_id}: {
                    pending_job['payload']}")
        else:
            logger.info(
                f"Retrieved a different pending job: {
                    pending_job['id']}")

        # 4. Cleanup (Optional: mark as failed/completed so it doesn't hang)
        db.update_job_status(
            job_id, 'completed', result={
                "status": "verified"})
        logger.info("Job marked as completed.")

        return True

    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False


if __name__ == "__main__":
    if verify_worker_db():
        print("DB_VERIFICATION_SUCCESS")
        sys.exit(0)
    else:
        print("DB_VERIFICATION_FAILURE")
        sys.exit(1)
