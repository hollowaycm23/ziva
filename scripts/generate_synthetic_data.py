
import time
from core.database import DatabaseManager
import sys
import random
import logging
from typing import List, Dict

# Ensure root is in path
sys.path.insert(0, '/home/holloway/ziva')


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("DataGen")


class SyntheticGenerator:
    def __init__(self):
        self.db = DatabaseManager()

    def generate_coding_examples(self, count=50) -> List[Dict]:
        examples = []
        tasks = [
            ("Create a function to calculate Fibonacci",
             "def fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)"),
            ("Write a script to list files", "import os\nprint(os.listdir('.'))"),
            ("How to read a JSON file?",
             "import json\nwith open('file.json') as f:\n    data = json.load(f)"),
            ("Explain asyncio run",
             "import asyncio\nasync def main(): pass\nasyncio.run(main())"),
            ("Simple Flask route",
             "from flask import Flask\napp = Flask(__name__)\n\n@app.route('/')\ndef home(): return 'Hello'"),
        ]

        for i in range(count):
            t = random.choice(tasks)
            examples.append({
                "instruction": f"{t[0]} (Variant {i}-{random.randint(1000, 9999)})",
                "output": t[1],
                "task_type": "coding",
                "quality_score": 0.9 + (random.random() * 0.1)
            })
        return examples

    def generate_shell_examples(self, count=50) -> List[Dict]:
        examples = []
        tasks = [
            ("List all processes on port 80", "lsof -i :80"),
            ("Find files larger than 100MB", "find . -type f -size +100M"),
            ("Count lines in a file", "wc -l filename.txt"),
            ("Check disk usage", "df -h"),
            ("Monitor system resources", "htop"),
        ]

        for i in range(count):
            t = random.choice(tasks)
            examples.append({
                "instruction": f"{t[0]} (Variant {i}-{random.randint(1000, 9999)})",
                "output": t[1],
                "task_type": "shell",
                "quality_score": 0.95
            })
        return examples

    def populate_db(self, total=100):
        data = []
        data.extend(self.generate_coding_examples(total // 2))
        data.extend(self.generate_shell_examples(total // 2))

        conn = self.db._get_conn()
        cursor = conn.cursor()

        count = 0
        for item in data:
            try:
                cursor.execute('''
                    INSERT INTO training_data (instruction, output, task_type, quality_score, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (item['instruction'], item['output'], item['task_type'], item['quality_score'], time.time()))
                count += 1
            except Exception:
                pass  # Ignore duplicates

        conn.commit()
        conn.close()
        logger.info(
            f"✅ Inseridos {count} novos exemplos sintéticos no banco de dados.")


if __name__ == "__main__":
    gen = SyntheticGenerator()
    gen.populate_db(total=200)
