"""
Auto fine-tuning orchestrator.
Creates LoRA fine-tuning jobs using Ollama's Modelfile system.
"""

import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger("AutoTuner")

TUNING_DIR = Path(__file__).parent.parent / "data" / "finetune"


class AutoTuner:
    """
    Creates and manages fine-tuning jobs.
    Uses Ollama's built-in fine-tuning via Modelfile + training data.
    """

    def __init__(self):
        self.tuning_dir = TUNING_DIR
        self.tuning_dir.mkdir(parents=True, exist_ok=True)

    def create_job(self, base_model: str = "batiai/qwen3.6-35b:iq3",
                   min_examples: int = 50) -> Optional[str]:
        from core.training_data import get_collector
        collector = get_collector()
        examples = collector.get_training_data(min_score=0.7, limit=200)

        if len(examples) < min_examples:
            logger.info(f"Not enough examples: {len(examples)} < {min_examples}")
            return None

        job_id = f"ft_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        job_dir = self.tuning_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        # Export training data
        data_path = collector.export_for_modelfile(
            output_path=job_dir / "training.jsonl",
            min_score=0.7,
            limit=200
        )
        if not data_path:
            return None

        # Create Modelfile
        modelfile_path = job_dir / "Modelfile"
        modelfile_content = f"""
FROM {base_model}

SYSTEM You are Ziva, a helpful AI assistant.

# Training data is loaded by Ollama
ADAPTER {data_path.name}
"""
        with open(modelfile_path, "w") as f:
            f.write(modelfile_content.strip())

        # Create job metadata
        job_meta = {
            "job_id": job_id,
            "base_model": base_model,
            "created_at": datetime.now().isoformat(),
            "training_examples": len(examples),
            "status": "ready",
            "modelfile": str(modelfile_path),
            "data_path": str(data_path),
        }
        with open(job_dir / "job.json", "w") as f:
            json.dump(job_meta, f, indent=2)

        logger.info(f"Fine-tuning job created: {job_id} ({len(examples)} examples)")
        return job_id

    def run_job(self, job_id: str) -> bool:
        job_dir = self.tuning_dir / job_id
        if not job_dir.exists():
            logger.error(f"Job {job_id} not found")
            return False

        with open(job_dir / "job.json", "r") as f:
            meta = json.load(f)

        new_model_name = f"ziva-{job_id}"
        logger.info(f"Running fine-tuning: {job_id} -> {new_model_name}")

        try:
            # Create new model with Ollama
            result = subprocess.run(
                ["ollama", "create", new_model_name, "-f", str(job_dir / "Modelfile")],
                capture_output=True, text=True, timeout=1800
            )
            if result.returncode == 0:
                meta["status"] = "completed"
                meta["model_name"] = new_model_name
                meta["completed_at"] = datetime.now().isoformat()
                with open(job_dir / "job.json", "w") as f:
                    json.dump(meta, f, indent=2)
                logger.info(f"Fine-tuning completed: {new_model_name}")
                return True
            else:
                meta["status"] = "failed"
                meta["error"] = result.stderr
                with open(job_dir / "job.json", "w") as f:
                    json.dump(meta, f, indent=2)
                logger.error(f"Fine-tuning failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            meta["status"] = "timeout"
            with open(job_dir / "job.json", "w") as f:
                json.dump(meta, f, indent=2)
            logger.error("Fine-tuning timed out (30 min)")
            return False
        except Exception as e:
            logger.error(f"Fine-tuning error: {e}")
            return False

    def list_jobs(self) -> list:
        jobs = []
        if self.tuning_dir.exists():
            for job_dir in sorted(self.tuning_dir.iterdir()):
                if job_dir.is_dir():
                    meta_path = job_dir / "job.json"
                    if meta_path.exists():
                        with open(meta_path, "r") as f:
                            meta = json.load(f)
                            jobs.append(meta)
        return sorted(jobs, key=lambda x: x.get("created_at", ""), reverse=True)

    def get_job(self, job_id: str) -> Optional[dict]:
        meta_path = self.tuning_dir / job_id / "job.json"
        if meta_path.exists():
            with open(meta_path, "r") as f:
                return json.load(f)
        return None


_tuner = None


def get_tuner():
    global _tuner
    if _tuner is None:
        _tuner = AutoTuner()
    return _tuner
