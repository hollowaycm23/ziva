"""
LoRA Fine-Tuning Script for Ziva Custom LLM

Fine-tunes qwen2.5-coder:7b on Ziva-specific decision-making tasks
using collected training data and LoRA (Low-Rank Adaptation).

Optimized for 12GB VRAM with gradient checkpointing and mixed precision.
"""

import os
import json
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZivaLoRATrainer:
    """Fine-tune LLM with LoRA for Ziva-specific tasks."""

    def __init__(
        self,
        base_model: str = "qwen2.5-coder:7b",
        dataset_path: str = "data/training/ziva_lora_dataset.json",
        output_dir: str = "models/ziva-lora-adapter",
        max_length: int = 512
    ):
        self.base_model = base_model
        self.dataset_path = dataset_path
        self.output_dir = output_dir
        self.max_length = max_length

        # Convert Ollama model name to HuggingFace format
        self.hf_model_name = self._get_hf_model_name(base_model)

    def _get_hf_model_name(self, ollama_name: str) -> str:
        """Convert Ollama model name to HuggingFace model name."""
        model_map = {
            "qwen2.5-coder:7b": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "llama3:8b": "meta-llama/Meta-Llama-3-8B-Instruct",
            "mistral:7b": "mistralai/Mistral-7B-Instruct-v0.2"
        }
        return model_map.get(ollama_name, ollama_name)

    def load_dataset(self):
        """Load and prepare training dataset."""
        logger.info(f"Loading dataset from {self.dataset_path}")

        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert to training format
        training_data = []
        for example in data:
            # Format as instruction-response pairs
            instruction = example.get('instruction', '')
            response = example.get('response', '')

            if instruction and response:
                training_data.append({
                    'text': f"### Instruction:\n{instruction}\n\n### Response:\n{response}"
                })

        logger.info(f"Prepared {len(training_data)} training examples")
        return Dataset.from_list(training_data)

    def prepare_model(self):
        """Load and prepare model with LoRA."""
        logger.info(f"Loading base model: {self.hf_model_name}")

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            self.hf_model_name,
            trust_remote_code=True
        )
        tokenizer.pad_token = tokenizer.eos_token

        # Load model in 4-bit for memory efficiency
        model = AutoModelForCausalLM.from_pretrained(
            self.hf_model_name,
            load_in_4bit=True,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )

        # Prepare for k-bit training
        model = prepare_model_for_kbit_training(model)

        # LoRA configuration optimized for 12GB VRAM
        lora_config = LoraConfig(
            r=16,  # Rank - balance between capacity and memory
            lora_alpha=32,  # Scaling factor
            target_modules=[
                "q_proj",
                "v_proj",
                "k_proj",
                "o_proj"],
            # Attention layers
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )

        # Apply LoRA
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()

        return model, tokenizer

    def tokenize_function(self, examples, tokenizer):
        """Tokenize examples for training."""
        return tokenizer(
            examples['text'],
            truncation=True,
            max_length=self.max_length,
            padding='max_length'
        )

    def train(self, epochs: int = 3, batch_size: int = 2,
              learning_rate: float = 2e-4):
        """Execute LoRA fine-tuning."""
        logger.info("🚀 Starting LoRA fine-tuning...")

        # Load dataset
        dataset = self.load_dataset()

        # Prepare model
        model, tokenizer = self.prepare_model()

        # Tokenize dataset
        tokenized_dataset = dataset.map(
            lambda x: self.tokenize_function(x, tokenizer),
            batched=True,
            remove_columns=dataset.column_names
        )

        # Training arguments optimized for 12GB VRAM
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=8,  # Effective batch size: 16
            learning_rate=learning_rate,
            fp16=True,  # Mixed precision
            save_steps=100,
            logging_steps=10,
            save_total_limit=3,
            gradient_checkpointing=True,  # Save VRAM
            optim="paged_adamw_8bit",  # Memory-efficient optimizer
            warmup_steps=50,
            lr_scheduler_type="cosine",
            report_to="none"  # Disable wandb
        )

        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False
        )

        # Trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator
        )

        # Train
        logger.info("🏋️ Training started...")
        trainer.train()

        # Save adapter
        logger.info(f"💾 Saving LoRA adapter to {self.output_dir}")
        model.save_pretrained(self.output_dir)
        tokenizer.save_pretrained(self.output_dir)

        logger.info("✅ Training complete!")

        return model, tokenizer


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Fine-tune Ziva LLM with LoRA")
    parser.add_argument(
        "--base-model",
        default="qwen2.5-coder:7b",
        help="Base model name")
    parser.add_argument(
        "--dataset",
        default="data/training/ziva_lora_dataset.json",
        help="Training dataset path")
    parser.add_argument(
        "--output",
        default="models/ziva-lora-adapter",
        help="Output directory")
    parser.add_argument("--epochs", type=int, default=3,
                        help="Number of training epochs")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=2,
        help="Batch size per device")
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-4,
        help="Learning rate")

    args = parser.parse_args()

    trainer = ZivaLoRATrainer(
        base_model=args.base_model,
        dataset_path=args.dataset,
        output_dir=args.output
    )

    trainer.train(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate
    )
