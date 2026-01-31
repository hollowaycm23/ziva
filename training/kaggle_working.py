# Ziva LoRA Training - Kaggle (VERSÃO FUNCIONAL)
# Testado - Janeiro 2026

"""
IMPORTANTE:
1. Kaggle → Settings → Internet → ON
2. Kaggle → Settings → Accelerator → GPU P100
3. Cole este código
4. Run All
"""

# ============================================
# CELL 1: Install Compatible Versions
# ============================================
import os
from datasets import load_dataset
from trl import SFTTrainer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
import torch
import json
print("📦 Installing compatible versions...")

# !pip install -q transformers==4.36.0 peft==0.8.0 trl==0.7.4 bitsandbytes==0.41.3 accelerate==0.25.0 datasets datasets

print("✅ Installed! Restart kernel: Kernel → Restart & Run All")

# ============================================
# CELL 2: Training Data
# ============================================

data = [
    {"text": "User: temperatura em são paulo\nAssistant: Usando get_weather para buscar."},
    {"text": "User: que horas são\nAssistant: Usando get_datetime."},
    {"text": "User: anime com kpop\nAssistant: Usando web_search."},
    {"text": "User: clima hoje\nAssistant: Usando get_weather."},
    {"text": "User: data de hoje\nAssistant: Usando get_datetime."},
]

with open('train.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ {len(data)} examples")

# ============================================
# CELL 3: Load & Train
# ============================================

print("GPU:", torch.cuda.get_device_name(0))

MODEL = "unsloth/mistral-7b-bnb-4bit"
OUT = "./ziva_adapters"

print(f"\n📥 Loading {MODEL}...")

model = AutoModelForCausalLM.from_pretrained(
    MODEL,
    quantization_config=BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    ),
    device_map="auto",
    trust_remote_code=True,
)

tokenizer = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token

model = prepare_model_for_kbit_training(model)
model = get_peft_model(model, LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05,
    bias="none", task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
))

print("✅ Model ready")
print("\n🏋️ Training...")

trainer = SFTTrainer(
    model=model,
    train_dataset=load_dataset('json', data_files='train.json', split='train'),
    dataset_text_field="text",
    max_seq_length=512,
    tokenizer=tokenizer,
    args=TrainingArguments(
        output_dir=OUT,
        num_train_epochs=3,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        gradient_checkpointing=True,
        max_steps=30,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=5,
        save_steps=15,
        report_to="none",
        optim="paged_adamw_8bit",
    ),
)

trainer.train()

print("\n💾 Saving...")
model.save_pretrained(OUT)
tokenizer.save_pretrained(OUT)

print(f"\n✅ Saved: {OUT}")
for f in os.listdir(OUT):
    print(f"  - {f}")

print("\n🎉 DONE! Download 'ziva_adapters' from Output →")
