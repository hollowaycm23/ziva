# Ziva LoRA Training - Kaggle Notebook
# Copy this entire notebook to Kaggle and run!

"""
SETUP INSTRUCTIONS:
1. Go to https://www.kaggle.com/code
2. Click "New Notebook"
3. Settings → Accelerator → GPU P100
4. Copy/paste this entire code
5. Run all cells
6. Download the 'adapters' folder when done
"""

# ============================================
# CELL 1: Install Dependencies
# ============================================
import os
from datasets import load_dataset
from trl import SFTTrainer
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training
)
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments
)
import torch
import json
print("📦 Installing dependencies...")
# !pip install -q transformers==4.36.0 peft==0.7.1 trl==0.7.4 bitsandbytes==0.41.3 accelerate==0.25.0

print("✅ Dependencies installed!")

# ============================================
# CELL 2: Upload Training Data
# ============================================
print("📤 Upload your training data...")
print("Create a file 'training_data.json' with this format:")
print("""
[
  {"text": "User: qual a temperatura\\nAssistant: Vou buscar a temperatura para você."},
  {"text": "User: que horas são\\nAssistant: Vou verificar a hora atual."}
]
""")

# For now, create sample data

sample_data = [
    {"text": "User: qual a temperatura em são paulo\nAssistant: Vou buscar a previsão do tempo para São Paulo usando a ferramenta get_weather."},
    {"text": "User: que horas são\nAssistant: Vou verificar a hora atual usando a ferramenta get_datetime."},
    {"text": "User: qual anime tem kpop no nome\nAssistant: Vou buscar essa informação usando web_search."},
    {"text": "User: como está o clima hoje\nAssistant: Vou consultar a previsão do tempo usando get_weather."},
    {"text": "User: qual a data de hoje\nAssistant: Vou verificar a data atual usando get_datetime."},
]

with open('training_data.json', 'w', encoding='utf-8') as f:
    json.dump(sample_data, f, ensure_ascii=False, indent=2)

print("✅ Sample training data created!")

# ============================================
# CELL 3: Load Model and Setup LoRA
# ============================================

print("🚀 GPU Available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print(f"   Device: {torch.cuda.get_device_name(0)}")
    print(
        f"   VRAM: {
            torch.cuda.get_device_properties(0).total_memory /
            1024**3:.1f} GB")

# Model configuration
MODEL_NAME = "unsloth/mistral-7b-bnb-4bit"
OUTPUT_DIR = "./ziva_lora_adapters"

print(f"\n📥 Loading model: {MODEL_NAME}...")

# 4-bit quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

# Load model
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

# Prepare for k-bit training
model = prepare_model_for_kbit_training(model)

print("✅ Model loaded!")

# ============================================
# CELL 4: Configure LoRA
# ============================================
print("\n⚙️ Configuring LoRA...")

lora_config = LoraConfig(
    r=16,                      # LoRA rank
    lora_alpha=32,             # LoRA alpha
    lora_dropout=0.05,         # Dropout
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj"],
    # Mistral attention modules
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

print("✅ LoRA configured!")

# ============================================
# CELL 5: Load Training Data
# ============================================
print("\n📚 Loading training data...")

dataset = load_dataset('json', data_files='training_data.json', split='train')
print(f"   Loaded {len(dataset)} examples")
print(f"   Sample: {dataset[0]['text'][:100]}...")

# ============================================
# CELL 6: Training Configuration
# ============================================
print("\n🏋️ Setting up training...")

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,                    # Number of epochs
    per_device_train_batch_size=1,         # Batch size (small for memory)
    gradient_accumulation_steps=4,         # Accumulate gradients
    gradient_checkpointing=True,           # Save memory
    warmup_steps=10,
    max_steps=50,                          # Total training steps
    learning_rate=2e-4,
    fp16=True,                             # Mixed precision
    logging_steps=5,
    save_strategy="steps",
    save_steps=25,
    report_to="none",
    optim="paged_adamw_8bit",             # Memory-efficient optimizer
)

# ============================================
# CELL 7: Create Trainer and Train
# ============================================
print("\n🚀 Starting training...")

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=512,
    tokenizer=tokenizer,
    args=training_args,
    packing=False,
)

# Start training
trainer.train()

print("\n✅ Training complete!")

# ============================================
# CELL 8: Save Adapters
# ============================================
print("\n💾 Saving LoRA adapters...")

# Save adapter
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print(f"✅ Adapters saved to: {OUTPUT_DIR}")
print("\n📥 Download the 'ziva_lora_adapters' folder and copy to:")
print("   /home/holloway/ziva/training/adapters/")

# List saved files
print("\n📁 Saved files:")
for file in os.listdir(OUTPUT_DIR):
    print(f"   - {file}")

# ============================================
# CELL 9: Test the Adapter (Optional)
# ============================================
print("\n🧪 Testing the trained adapter...")

# Generate sample text
prompt = "User: qual a temperatura em são paulo\nAssistant:"
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

outputs = model.generate(
    **inputs,
    max_new_tokens=50,
    temperature=0.7,
    do_sample=True,
)

generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f"\n📝 Generated:\n{generated_text}")

print("\n✅ All done! Download 'ziva_lora_adapters' folder now!")
