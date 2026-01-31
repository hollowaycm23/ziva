import threading
import time
import logging
import traceback
from datetime import datetime

from core.thought_police import ThoughtPolice
from core.dreamer import Dreamer

logger = logging.getLogger("AutonomicSystem")


class AutonomicSystem:
    """
    Ziva's Autonomic Nervous System.
    Manages background cognitive processes (metacognition and memory
    consolidation) independently of user interaction.
    """

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None

        self.INTERVAL_THOUGHT_POLICE = 600
        self.INTERVAL_DREAM_CYCLE = 24 * 3600
        self.INTERVAL_LEARNING_CYCLE = 21600

        self.last_thought_check = datetime.min
        self.last_dream_cycle = datetime.min
        self.last_learning_cycle = datetime.min

    def start(self):
        """Starts the background autonomic loop."""
        if self._thread and self._thread.is_alive():
            logger.warning("Autonomic System is already running.")
            return

        logger.info("🫀 Autonomic Nervous System Starting...")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stops the background loop gracefully."""
        logger.info("🫀 Autonomic Nervous System Stopping...")
        self._stop_event.set()
        if self._thread:
            self._thread.join()

    def _run_loop(self):
        """Main biological loop."""
        logger.info("🫀 Autonomic Pulse Active.")

        while not self._stop_event.is_set():
            try:
                now = datetime.now()

                if (now - self.last_thought_check).total_seconds(
                ) > self.INTERVAL_THOUGHT_POLICE:
                    self._run_cogenitive_task(
                        "Metacognition", ThoughtPolice().run_cycle)
                    self.last_thought_check = now

                if (now - self.last_dream_cycle).total_seconds(
                ) > self.INTERVAL_DREAM_CYCLE:
                    self._run_cogenitive_task("Dream Phase", Dreamer().dream)
                    from core.learner import Learner
                    self._run_cogenitive_task(
                        "Neuro-Plasticity (Study)", Learner().study_session)
                    self.last_dream_cycle = now

                time.sleep(60)

            except Exception as e:
                logger.error(f"❌ Autonomic System Failure: {e}")
                time.sleep(60)

    def _run_cogenitive_task(self, name: str, task_func):
        """Helper to run a task safely."""
        logger.info(f"🧠 Autonomic Trigger: Starting {name}...")
        try:
            start_t = time.time()
            task_func()
            elapsed = time.time() - start_t
            logger.info(f"✨ {name} Complete (took {elapsed:.2f}s).")
        except Exception as e:
            logger.error(f"⚠️ {name} Failed: {e}")
            logger.debug(traceback.format_exc())


autonomic_system = AutonomicSystem()