# Ziva LoRA Training - Kaggle Notebook (Versão Simplificada)
# Use esta versão se houver problemas de conexão

"""
SETUP INSTRUCTIONS:
1. Go to https://www.kaggle.com/code
2. Click "New Notebook"
3. Settings → Accelerator → GPU P100
4. Settings → Internet → ON (IMPORTANTE!)
5. Copy/paste this entire code
6. Run all cells
"""

# ============================================
# CELL 1: Check Internet and Install
# ============================================
import os
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch
import json
import subprocess
print("🌐 Checking internet connection...")
result = subprocess.run(['ping', '-c', '1', 'google.com'], capture_output=True)
if result.returncode == 0:
    print("✅ Internet OK")
else:
    print("❌ No internet! Enable in Settings → Internet → ON")
    print("Then restart kernel and try again")

print("\n📦 Installing dependencies (this may take 2-3 minutes)...")

# Install without version pinning to use Kaggle's cache
# !pip install -q --no-deps transformers peft trl bitsandbytes accelerate datasets

print("✅ Dependencies installed!")

# ============================================
# CELL 2: Verify Installation
# ============================================
print("🔍 Verifying installations...")
try:
    import transformers
    import peft
    import trl
    import bitsandbytes
    import accelerate
    print(f"✅ transformers: {transformers.__version__}")
    print(f"✅ peft: {peft.__version__}")
    print(f"✅ trl: {trl.__version__}")
    print(f"✅ accelerate: {accelerate.__version__}")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Try restarting kernel and running again")

# ============================================
# CELL 3: Create Training Data
# ============================================
print("\n📝 Creating training data...")

training_data = [
    {"text": "User: qual a temperatura em são paulo\nAssistant: Vou buscar a previsão do tempo para São Paulo usando a ferramenta get_weather."},
    {"text": "User: que horas são\nAssistant: Vou verificar a hora atual usando a ferramenta get_datetime."},
    {"text": "User: qual anime tem kpop no nome\nAssistant: Vou buscar essa informação usando web_search para encontrar animes com kpop no nome."},
    {"text": "User: como está o clima hoje\nAssistant: Vou consultar a previsão do tempo atual usando get_weather."},
    {"text": "User: qual a data de hoje\nAssistant: Vou verificar a data atual usando get_datetime."},
    {"text": "User: pesquise sobre inteligência artificial\nAssistant: Vou usar web_search para buscar informações sobre inteligência artificial."},
    {"text": "User: temperatura em artur nogueira\nAssistant: Vou buscar a temperatura em Artur Nogueira usando get_weather."},
    {"text": "User: que dia é hoje\nAssistant: Vou verificar o dia atual usando get_datetime."},
]

with open('training_data.json', 'w', encoding='utf-8') as f:
    json.dump(training_data, f, ensure_ascii=False, indent=2)

print(f"✅ Created {len(training_data)} training examples")

# ============================================
# CELL 4: Load Model
# ============================================

print("\n🚀 GPU Check:")
print(f"   Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"   Device: {torch.cuda.get_device_name(0)}")
    print(
        f"   VRAM: {
            torch.cuda.get_device_properties(0).total_memory /
            1024**3:.1f} GB")

MODEL_NAME = "unsloth/mistral-7b-bnb-4bit"
OUTPUT_DIR = "./ziva_lora_adapters"

print(f"\n📥 Loading {MODEL_NAME}...")
print("   (This will take 3-5 minutes)")

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
# CELL 5: Setup LoRA
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
print("✅ LoRA configured!")

# ============================================
# CELL 6: Load Data and Train
# ============================================

print("\n📚 Loading training data...")
dataset = load_dataset('json', data_files='training_data.json', split='train')
print(f"   {len(dataset)} examples loaded")

print("\n🏋️ Starting training...")
print("   This will take ~10-15 minutes")

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
# CELL 7: Save Adapters
# ============================================
print("\n💾 Saving adapters...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print(f"\n✅ Saved to: {OUTPUT_DIR}")
print("\n📁 Files:")
for file in os.listdir(OUTPUT_DIR):
    print(f"   - {file}")

print("\n" + "=" * 50)
print("🎉 SUCCESS! Download 'ziva_lora_adapters' folder")
print("   from Output panel (right side)")
print("=" * 50)
