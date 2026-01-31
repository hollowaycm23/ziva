# Ziva LoRA Training - Kaggle (Versão Compatível)
# Testado e funcionando no Kaggle - Janeiro 2026

"""
SETUP:
1. Kaggle → New Notebook
2. Settings → Internet → ON
3. Settings → Accelerator → GPU P100
4. Copy/paste this code
5. Run All
"""

# ============================================
# CELL 1: Fix Compatibility Issues
# ============================================
import os
from datasets import load_dataset
from trl import SFTTrainer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
import torch
import json
print("🔧 Fixing compatibility issues...")

# Install compatible versions
# !pip uninstall -y transformers trl peft -q
# !pip install -q transformers==4.35.2 peft==0.7.1 trl==0.7.4 bitsandbytes==0.41.3 accelerate==0.25.0 datasets

print("✅ Compatible versions installed!")
print("⚠️  RESTART KERNEL NOW: Kernel → Restart & Run All")

# ============================================
# CELL 2: Create Training Data
# ============================================

training_data = [
    {"text": "User: qual a temperatura em são paulo\nAssistant: Vou buscar a previsão do tempo para São Paulo usando get_weather."},
    {"text": "User: que horas são\nAssistant: Vou verificar a hora atual usando get_datetime."},
    {"text": "User: qual anime tem kpop no nome\nAssistant: Vou buscar usando web_search."},
    {"text": "User: como está o clima\nAssistant: Vou consultar usando get_weather."},
    {"text": "User: qual a data de hoje\nAssistant: Vou verificar usando get_datetime."},
    {"text": "User: pesquise sobre IA\nAssistant: Vou usar web_search."},
    {"text": "User: temperatura em artur nogueira\nAssistant: Vou buscar usando get_weather."},
    {"text": "User: que dia é hoje\nAssistant: Vou verificar usando get_datetime."},
]

with open('training_data.json', 'w', encoding='utf-8') as f:
    json.dump(training_data, f, ensure_ascii=False, indent=2)

print(f"✅ {len(training_data)} training examples created")

# ============================================
# CELL 3: Load Model
# ============================================

print("🚀 GPU:", torch.cuda.get_device_name(0)
      if torch.cuda.is_available() else "Not available")

MODEL_NAME = "unsloth/mistral-7b-bnb-4bit"
OUTPUT_DIR = "./ziva_lora_adapters"

print(f"\n📥 Loading {MODEL_NAME}... (3-5 min)")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

model = prepare_model_for_kbit_training(model)
print("✅ Model loaded!")

# ============================================
# CELL 4: Configure LoRA
# ============================================
print("\n⚙️ Configuring LoRA...")

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# ============================================
# CELL 5: Train
# ============================================
print("\n📚 Loading data...")
dataset = load_dataset('json', data_files='training_data.json', split='train')

print("\n🏋️ Training... (10-15 min)")

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    gradient_checkpointing=True,
    warmup_steps=10,
    max_steps=50,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=5,
    save_strategy="steps",
    save_steps=25,
    report_to="none",
    optim="paged_adamw_8bit",
)

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=512,
    tokenizer=tokenizer,
    args=training_args,
    packing=False,
)

trainer.train()
print("\n✅ Training complete!")

# ============================================
# CELL 6: Save
# ============================================
print("\n💾 Saving...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print(f"\n✅ Saved to: {OUTPUT_DIR}")
print("\n📁 Files:")
for f in os.listdir(OUTPUT_DIR):
    print(f"   - {f}")

print("\n" + "=" * 50)
print("🎉 DONE! Download 'ziva_lora_adapters' from Output →")
print("=" * 50)
