
from core.dataset_loader import DatasetLoader
import os
import torch
import logging
from pathlib import Path
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training
)
from trl import SFTTrainer
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LoRATrainer")

# Ensure we can import from core
sys.path.insert(0, '/home/holloway/ziva')


class LoRATrainer:
    def __init__(self, model_name="unsloth/mistral-7b-bnB-4bit",
                 output_dir="./adapters"):
        self.model_name = model_name
        self.output_dir = output_dir
        self.tokenizer = None
        self.model = None

    def prepare_environment(self):
        """Configura ambiente e checa GPU"""
        if not torch.cuda.is_available():
            logger.warning(
                "⚠️ GPU não detectada! Modificando para modo CPU com modelo leve (GPT-2).")
            self.model_name = "gpt2"  # Fallback para CPU
            return False

        logger.info(f"🚀 GPU Detectada: {torch.cuda.get_device_name(0)}")
        return True

    def load_model(self):
        """Carrega modelo base"""
        logger.info(f"📥 Carregando modelo base: {self.model_name}...")

        # CPU Mode (GPT-2, no quantization)
        if self.model_name == "gpt2":
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.tokenizer.pad_token = self.tokenizer.eos_token
            return

        # GPU Mode (Mistral 4-bit with CPU offloading)
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            llm_int8_enable_fp32_cpu_offload=True  # Enable CPU offloading
        )

        # Custom device map to allow CPU offloading
        device_map = {
            "model.embed_tokens": 0,
            "model.layers": 0,
            "model.norm": 0,
            "lm_head": "cpu"  # Offload lm_head to CPU to save GPU memory
        }

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=bnb_config,
            device_map=device_map,
            low_cpu_mem_usage=True
        )

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token

        # Preparar para treino em k-bit
        self.model = prepare_model_for_kbit_training(self.model)

    def setup_lora(self):
        """Configura adaptadores LoRA"""
        logger.info(f"DEBUG: Configurando LoRA para modelo: {self.model_name}")

        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]

        if "gpt2" in self.model_name.lower():
            target_modules = ["c_attn"]
            logger.info(
                "DEBUG: Detectado GPT-2. Usando target_modules=['c_attn']")

        peft_config = LoraConfig(
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=target_modules
        )

        self.model = get_peft_model(self.model, peft_config)
        self.model.print_trainable_parameters()

    def train(self):
        """Executa loop de treinamento"""
        logger.info("🏋️ Iniciando treinamento...")

        # 1. Carregar Dados
        loader = DatasetLoader()
        dataset = loader.load_from_db()

        if not dataset:
            logger.error("❌ Abortando: Sem dados para treinar.")
            return

        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=1,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=4,
            gradient_checkpointing=True,  # Reduz uso de memória
            warmup_steps=2,
            max_steps=10,
            learning_rate=2e-4,
            fp16=False,  # Disable mixed precision to avoid BFloat16 issues
            logging_steps=1,
            save_strategy="steps",
            save_steps=5,
            report_to="none",
            dataloader_num_workers=2,  # Parallel data loading
            dataloader_pin_memory=True,  # Faster GPU transfer
            optim="adamw_torch_fused",  # Faster optimizer
        )

        trainer = SFTTrainer(
            model=self.model,
            train_dataset=dataset,
            # dataset_text_field="text", # REMOVED
            # max_seq_length=512, # REMOVED
            # tokenizer=self.tokenizer, # REMOVED: Causing TypeError in
            # installed TRL version
            args=training_args,
        )

        trainer.train()

        logger.info("✅ Treinamento concluído! Salvando adaptadores...")

        # Criar diretório se não existir
        os.makedirs(self.output_dir, exist_ok=True)

        # Salvar adapter
        trainer.model.save_pretrained(self.output_dir)

        # Salvar tokenizer também
        self.tokenizer.save_pretrained(self.output_dir)

        # Verificar se salvou
        adapter_files = list(Path(self.output_dir).glob("adapter_*"))
        if adapter_files:
            logger.info(f"✅ Adapters salvos em: {self.output_dir}")
            for f in adapter_files:
                logger.info(f"   - {f.name}")
        else:
            logger.warning(
                f"⚠️ Nenhum arquivo de adapter encontrado em {
                    self.output_dir}")


if __name__ == "__main__":
    trainer = LoRATrainer()
    has_gpu = trainer.prepare_environment()
    # Proceed regardless of GPU, logic inside load_model handles it
    trainer.load_model()
    trainer.setup_lora()
    trainer.train()
