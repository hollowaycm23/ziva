
import os
import sys
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer
from datasets import Dataset


def train():
    print("🚀 Iniciando Treinamento de Emergência (CPU)...")
    model_id = "gpt2"

    print("1. Carregando Modelo...")
    model = AutoModelForCausalLM.from_pretrained(model_id)
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    tokenizer.pad_token = tokenizer.eos_token

    print("2. Configurando LoRA...")
    peft_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["c_attn"],
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, peft_config)

    print("3. Preparando Dados...")
    data = [{"text": "Instruction: Test\nResponse: Success"}] * 5
    dataset = Dataset.from_list(data)

    print("4. Treinando...")
    args = TrainingArguments(
        output_dir="adapters",
        max_steps=1,
        use_cpu=True,
        logging_steps=1
    )

    trainer = SFTTrainer(
        model=model,
        args=args,
        train_dataset=dataset,
        dataset_text_field="text",
        tokenizer=tokenizer
    )

    trainer.train()

    print("5. Salvando...")
    trainer.save_model("adapters")
    print("✅ Adapters criados em 'adapters/'")


if __name__ == "__main__":
    train()
