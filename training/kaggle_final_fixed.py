# Ziva LoRA - Kaggle (API Atualizada)
# Compatible with TRL 0.8+ - Janeiro 2026

"""
SETUP:
1. Kaggle → Settings → Internet → ON
2. Kaggle → Settings → Accelerator → GPU P100
3. Run All
"""

# ============================================
# CELL 1: Install
# ============================================
import torch
import json
from datasets import load_dataset
from trl import SFTTrainer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
print("📦 Installing...")
# !pip install -q --upgrade transformers peft trl bitsandbytes accelerate datasets
# print("✅ Restart: Kernel → Restart & Run All")

# ============================================
# CELL 2: Train
# ============================================

# Data
data = [
    {"text": "User: temperatura\nAssistant: get_weather"},
    {"text": "User: clima\nAssistant: get_weather"},
    {"text": "User: que horas\nAssistant: get_datetime"},
    {"text": "User: anime kpop\nAssistant: web_search"},
]
with open('train.json', 'w') as f:
    json.dump(data, f)

print(f"GPU: {torch.cuda.get_device_name(0)}")
print("📥 Loading...")

# Model
model = AutoModelForCausalLM.from_pretrained(
    "unsloth/mistral-7b-bnb-4bit",
    quantization_config=BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    ),
    device_map="auto",
    trust_remote_code=True,
)

tokenizer = AutoTokenizer.from_pretrained("unsloth/mistral-7b-bnb-4bit")
tokenizer.pad_token = tokenizer.eos_token

# LoRA
model = prepare_model_for_kbit_training(model)
model = get_peft_model(model, LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05,
    bias="none", task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
))

print("🏋️ Training...")

# Train (NEW API - no dataset_text_field)
trainer = SFTTrainer(
    model=model,
    train_dataset=load_dataset('json', data_files='train.json', split='train'),
    tokenizer=tokenizer,
    max_seq_length=256,
    args=TrainingArguments(
        output_dir="./ziva_adapters",
        num_train_epochs=2,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        max_steps=20,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=5,
        save_steps=10,
        report_to="none",
    ),
    # Use formatting_func instead of dataset_text_field
    formatting_func=lambda x: x["text"],
)

trainer.train()

# Save
model.save_pretrained("./ziva_adapters")
tokenizer.save_pretrained("./ziva_adapters")

print("\n🎉 DONE! Download 'ziva_adapters' from Output →")
