"""
Merge LoRA adapter with base model and convert to Ollama format.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import os


class LoRAMerger:
    """Merge LoRA adapter with base model."""

    def __init__(
        self,
        base_model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
        adapter_path: str = "models/ziva-lora-adapter",
        output_path: str = "models/ziva-optimized"
    ):
        self.base_model_name = base_model_name
        self.adapter_path = adapter_path
        self.output_path = output_path

    def merge_and_save(self):
        """Merge LoRA adapter with base model and save."""
        print("🔄 Merging LoRA adapter with base model...")

        # Load tokenizer
        print("📥 Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_name,
            trust_remote_code=True
        )

        # Load base model
        print("📥 Loading base model...")
        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )

        # Load LoRA adapter
        print("📥 Loading LoRA adapter...")
        model = PeftModel.from_pretrained(base_model, self.adapter_path)

        # Merge adapter weights into base model
        print("🔀 Merging adapter weights...")
        merged_model = model.merge_and_unload()

        # Save merged model
        print(f"💾 Saving merged model to {self.output_path}...")
        os.makedirs(self.output_path, exist_ok=True)
        merged_model.save_pretrained(self.output_path)
        tokenizer.save_pretrained(self.output_path)

        print("✅ Merge complete!")
        print(f"📁 Merged model saved to: {self.output_path}")

        return self.output_path

    def create_ollama_modelfile(self, merged_path: str):
        """Create Ollama Modelfile for the merged model."""
        modelfile_content = f"""FROM {merged_path}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER stop "<|im_end|>"

SYSTEM \"\"\"
You are Ziva, an advanced AI assistant optimized for tool selection and decision-making.
You excel at determining when to use tools and selecting the appropriate tool for each task.
\"\"\"
"""

        modelfile_path = os.path.join(merged_path, "Modelfile")
        with open(modelfile_path, 'w') as f:
            f.write(modelfile_content)

        print(f"📝 Modelfile created: {modelfile_path}")
        return modelfile_path

    def deploy_to_ollama(self, merged_path: str):
        """Deploy merged model to Ollama."""
        import subprocess

        print("\n🚀 Deploying to Ollama...")

        # Create Modelfile
        modelfile = self.create_ollama_modelfile(merged_path)

        # Import to Ollama
        cmd = f"ollama create ziva-optimized:latest -f {modelfile}"
        print(f"Running: {cmd}")

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ Model deployed to Ollama as 'ziva-optimized:latest'")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"❌ Deployment failed: {e}")
            print(e.stderr)
            return False

        return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Merge LoRA adapter and deploy to Ollama")
    parser.add_argument(
        "--base-model",
        default="Qwen/Qwen2.5-Coder-7B-Instruct")
    parser.add_argument("--adapter", default="models/ziva-lora-adapter")
    parser.add_argument("--output", default="models/ziva-optimized")
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Deploy to Ollama after merge")

    args = parser.parse_args()

    merger = LoRAMerger(
        base_model_name=args.base_model,
        adapter_path=args.adapter,
        output_path=args.output
    )

    # Merge
    merged_path = merger.merge_and_save()

    # Deploy if requested
    if args.deploy:
        merger.deploy_to_ollama(merged_path)
    else:
        print("\n💡 To deploy to Ollama, run:")
        print(f"   python3 training/merge_lora.py --deploy")
