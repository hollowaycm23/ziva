#!/usr/bin/env python3
from core.p2p_learning import GabrielleConnector
from core.database import DatabaseManager
import sys
import os
import time
import argparse
import logging

# Setup path
sys.path.insert(0, '/home/holloway/ziva')

# from training.lora_trainer import LoRATrainer # Import delayed to avoid
# heavy load on CLI start

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("PipelineManager")


def check_status():
    print("\n📊 Ziva System Status")
    print("====================")

    # 1. DB Status
    db = DatabaseManager()
    conn = db._get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT Count(*) FROM training_data")
    count = cursor.fetchone()[0]
    print(f"📚 Training Examples: {count}")
    conn.close()

    # 2. P2P Status
    print("\n🔗 P2P Connection (Gabrielle)")
    connector = GabrielleConnector(host="100.114.201.84", port=9000)
    if connector.is_connected and connector.health_check():
        print("✅ Online & Authenticated")
    else:
        print("❌ Offline or Unreachable")
    connector.close()


def sync_all():
    print("\n🔄 Starting Full Synchronization")
    print("================================")
    os.system("/usr/bin/python3 /home/holloway/ziva/scripts/sync_full.py")


def train_now():
    print("\n🏋️ Starting Fine-Tuning Pipeline (LoRA)")
    print("========================================")
    print("⚠️  Warning: This requires significant GPU resources.")
    time.sleep(2)
    os.system("/usr/bin/python3 /home/holloway/ziva/training/lora_trainer.py")


def deploy_adapter():
    print("\n🚀 Deploying Adapter to Ollama")
    print("================================")
    os.system(
        "/usr/bin/python3 /home/holloway/ziva/scripts/deploy_to_ollama.py --test")


def main():
    parser = argparse.ArgumentParser(description="Ziva AI Pipeline Manager")
    parser.add_argument(
        'action',
        choices=[
            'status',
            'sync',
            'train',
            'deploy',
            'all'],
        help='Action to perform')

    args = parser.parse_args()

    if args.action == 'status':
        check_status()
    elif args.action == 'sync':
        sync_all()
    elif args.action == 'train':
        train_now()
    elif args.action == 'deploy':
        deploy_adapter()
    elif args.action == 'all':
        check_status()
        sync_all()
        train_now()
        deploy_adapter()


if __name__ == "__main__":
    main()
