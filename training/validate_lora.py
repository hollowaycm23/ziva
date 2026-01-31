"""
Test and validate the trained LoRA adapter.
Compare responses with and without the adapter.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import json


class LoRAValidator:
    """Validate LoRA adapter quality."""

    def __init__(
        self,
        base_model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
        adapter_path: str = "models/ziva-lora-adapter"
    ):
        self.base_model_name = base_model_name
        self.adapter_path = adapter_path

    def load_models(self):
        """Load base model and adapter."""
        print("📥 Loading base model...")

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_name,
            trust_remote_code=True
        )

        # Load base model
        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )

        print("📥 Loading LoRA adapter...")
        # Load model with adapter
        lora_model = PeftModel.from_pretrained(
            base_model,
            self.adapter_path
        )

        return tokenizer, base_model, lora_model

    def generate_response(self, model, tokenizer,
                          prompt: str, max_length: int = 256):
        """Generate response from model."""
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=max_length,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove the prompt from response
        response = response[len(prompt):].strip()
        return response

    def test_queries(self):
        """Test with example queries."""
        test_cases = [
            {
                "query": "Crie um script Python para obter dados climáticos",
                "expected_tool": "remote_shell or code_writer"
            },
            {
                "query": "Execute o comando date no servidor",
                "expected_tool": "local_shell or remote_shell"
            },
            {
                "query": "Escreva uma função para fibonacci",
                "expected_tool": "code_writer"
            }
        ]

        print("\n" + "=" * 80)
        print("🧪 TESTING LORA ADAPTER")
        print("=" * 80)

        tokenizer, base_model, lora_model = self.load_models()

        results = []

        for i, test in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: {test['query']}")
            print("-" * 80)

            # Test base model
            print("\n🔵 Base Model Response:")
            base_response = self.generate_response(
                base_model, tokenizer, test['query'])
            print(base_response[:200])

            # Test LoRA model
            print("\n🟢 LoRA Model Response:")
            lora_response = self.generate_response(
                lora_model, tokenizer, test['query'])
            print(lora_response[:200])

            results.append({
                "query": test['query'],
                "base_response": base_response,
                "lora_response": lora_response,
                "expected": test['expected_tool']
            })

        # Save results
        with open('models/validation_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 80)
        print("✅ Validation complete! Results saved to models/validation_results.json")
        print("=" * 80)

        return results


if __name__ == "__main__":
    validator = LoRAValidator()
    validator.test_queries()
