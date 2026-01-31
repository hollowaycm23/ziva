"""
Custom LLM wrapper for Ziva's fine-tuned model.
Loads the merged LoRA model directly via transformers.
LangChain compatible.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Optional, List, Any, Mapping
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from pathlib import Path
import logging

logger = logging.getLogger("ZivaCustomLLM")


class ZivaCustomLLM(LLM):

    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "ziva_custom"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the model."""
        return self.generate(prompt, stop_sequences=stop, **kwargs)

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get identifying parameters."""
        return {
            "base_model": self.base_model,
            "adapter_path": self.adapter_path,
            "use_adapter": self.use_adapter
        }

    def __new__(cls, *args, **kwargs):
        """Override to allow LangChain instantiation."""
        return object.__new__(cls)

    def __init__(
        self,
        base_model: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
        adapter_path: str = "models/ziva-lora-adapter",
        device: str = "auto",
        load_in_4bit: bool = True,
        use_adapter: bool = True
    ):
        """Initialize the custom LLM with LoRA adapter for VRAM efficiency."""
        if not hasattr(self, '_initialized'):
            self.base_model = base_model
            self.adapter_path = adapter_path
            self.device = device
            self.load_in_4bit = load_in_4bit
            self.use_adapter = use_adapter
            self._initialized = True
            self._load_model()

    def _load_model(self):
        """Load base model + LoRA adapter for VRAM efficiency."""
        logger.info(f"Loading base model: {self.base_model}")

        try:
            # Load tokenizer from adapter path (has all tokens)
            adapter_exists = Path(self.adapter_path).exists()
            tokenizer_path = self.adapter_path if adapter_exists else self.base_model

            self._tokenizer = AutoTokenizer.from_pretrained(
                tokenizer_path,
                trust_remote_code=True
            )

            # Load base model with 4-bit quantization
            if self.load_in_4bit:
                from transformers import BitsAndBytesConfig

                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )

                self._model = AutoModelForCausalLM.from_pretrained(
                    self.base_model,
                    quantization_config=quantization_config,
                    device_map=self.device,
                    trust_remote_code=True
                )
            else:
                self._model = AutoModelForCausalLM.from_pretrained(
                    self.base_model,
                    torch_dtype=torch.float16,
                    device_map=self.device,
                    trust_remote_code=True
                )

            # Load LoRA adapter if available and requested
            if self.use_adapter and adapter_exists:
                from peft import PeftModel
                logger.info(f"Loading LoRA adapter from {self.adapter_path}")
                self._model = PeftModel.from_pretrained(
                    self._model, self.adapter_path)
                logger.info("✅ Custom Ziva model loaded with LoRA adapter")
            else:
                logger.info(
                    "✅ Base model loaded (adapter not found or disabled)")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.warning("Falling back to base model without adapter")
            self._load_fallback()

    def _load_fallback(self):
        """Load fallback base model if custom model fails."""
        base_model = "Qwen/Qwen2.5-Coder-7B-Instruct"
        logger.info(f"Loading fallback model: {base_model}")

        self._tokenizer = AutoTokenizer.from_pretrained(
            base_model,
            trust_remote_code=True
        )

        self._model = AutoModelForCausalLM.from_pretrained(
            base_model,
            load_in_4bit=True,
            device_map="auto",
            trust_remote_code=True
        )

    def generate(
        self,
        prompt: str,
        max_length: int = 256,
        temperature: float = 0.1,
        top_p: float = 0.9,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """
        Generate text from the model.

        Args:
            prompt: Input prompt
            max_length: Maximum length of generated text
            temperature: Sampling temperature (lower = more deterministic)
            top_p: Nucleus sampling parameter
            stop_sequences: List of sequences to stop generation

        Returns:
            Generated text
        """
        if self._model is None or self._tokenizer is None:
            raise RuntimeError("Model not loaded")

        # Tokenize input
        inputs = self._tokenizer(
            prompt, return_tensors="pt").to(
            self._model.device)

        # Generate
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                top_p=top_p,
                do_sample=temperature > 0,
                pad_token_id=self._tokenizer.eos_token_id
            )

        # Decode
        generated_text = self._tokenizer.decode(
            outputs[0], skip_special_tokens=True)

        # Remove prompt from output
        response = generated_text[len(prompt):].strip()

        # Apply stop sequences
        if stop_sequences:
            for stop_seq in stop_sequences:
                if stop_seq in response:
                    response = response[:response.index(stop_seq)]

        return response

    def invoke(self, prompt: str, **kwargs) -> str:
        """
        LangChain-compatible invoke method.

        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        return self.generate(prompt, **kwargs)

    @property
    def model(self):
        """Get the underlying model."""
        return self._model

    @property
    def tokenizer(self):
        """Get the tokenizer."""
        return self._tokenizer


# Global instance
_ziva_llm_instance = None


def get_ziva_llm() -> ZivaCustomLLM:
    """Get or create the global Ziva LLM instance."""
    global _ziva_llm_instance
    if _ziva_llm_instance is None:
        _ziva_llm_instance = ZivaCustomLLM()
    return _ziva_llm_instance


if __name__ == "__main__":
    # Test the custom LLM
    llm = get_ziva_llm()

    test_prompt = "Decide if a tool is needed. Respond ONLY with 'YES' or 'NO'.\n\nUser Request: pesquise sobre inteligência artificial\n\nDecision:"

    response = llm.generate(test_prompt, max_length=50, temperature=0.1)
    print(f"Prompt: {test_prompt}")
    print(f"Response: {response}")
