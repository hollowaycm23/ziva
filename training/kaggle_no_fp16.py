# Ziva LoRA - Kaggle (SEM FP16)
# Fix BFloat16 Error - Janeiro 2026

"""
1. Kaggle → Settings → Internet ON + GPU P100
2. Run All
"""

# CELL 1: Install
import torch
import json
from datasets import Dataset
from trl import SFTTrainer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
print("📦 Installing...")
# !pip install -q transformers peft trl bitsandbytes accelerate datasets
print("✅ Restart: Kernel → Restart & Run All")

# CELL 2: Train

# Data
data = Dataset.from_dict({
    "text": [
        "User: temperatura\nAssistant: get_weather",
        "User: clima\nAssistant: get_weather",
        "User: que horas\nAssistant: get_datetime",
        "User: anime kpop\nAssistant: web_search",
    ]
})

print(f"GPU: {torch.cuda.get_device_name(0)}")

# Model
model = AutoModelForCausalLM.from_pretrained(
    "unsloth/mistral-7b-bnb-4bit",
    quantization_config=BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16),
    device_map="auto", trust_remote_code=True,
)
tokenizer = AutoTokenizer.from_pretrained("unsloth/mistral-7b-bnb-4bit")
tokenizer.pad_token = tokenizer.eos_token

# LoRA
model = prepare_model_for_kbit_training(model)
model = get_peft_model(
    model,
    LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
             "o_proj"]))

print("🏋️ Training...")

# Train - NO FP16 (fixes BFloat16 error)
trainer = SFTTrainer(
    model=model,
    train_dataset=data,
    args=TrainingArguments(
        output_dir="./ziva_adapters",
        max_steps=20,
        learning_rate=2e-4,
        fp16=False,  # DISABLED to avoid BFloat16 error
        bf16=False,  # Also disabled
        logging_steps=5,
        report_to="none"
    ),
)

trainer.train()
model.save_pretrained("./ziva_adapters")
tokenizer.save_pretrained("./ziva_adapters")

print("\n🎉 DONE! Download 'ziva_adapters'")
