import dspy
from dspy.teleprompt import BootstrapFewShot
from core.dspy_modules.modules import Generator
from core.dspy_config import configure_dspy
from training.dataset_builder import build_dataset
import os

def validate_answer(example, pred, trace=None):
    """
    Simple metric: Check if the reference answer is contained in the prediction.
    """
    return example.answer.lower() in pred.answer.lower()

def compile_generator():
    print("🚀 Starting compilation for Generator module...")
    
    # 1. Configure DSPy
    configure_dspy()
    
    # 2. Load Dataset
    trainset = build_dataset()
    
    # 3. Define Module to Compile
    # We create a fresh instance
    generator = Generator()
    
    # 4. Define Optimizer
    # BootstrapFewShot is good for starting out (adds few-shot regular examples)
    teleprompter = BootstrapFewShot(metric=validate_answer, max_bootstrapped_demos=2, max_labeled_demos=2)
    
    # 5. Compile
    print("⏳ Compiling... (this may take a moment)")
    compiled_generator = teleprompter.compile(generator, trainset=trainset)
    
    # 6. Save
    output_path = "core/dspy_modules/compiled_generator.json"
    compiled_generator.save(output_path)
    print(f"✅ Compilation complete! Saved to {output_path}")

if __name__ == "__main__":
    compile_generator()
