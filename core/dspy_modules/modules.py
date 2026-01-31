import dspy
import os
from core.dspy_modules.signatures import (
    ContextualizeQuery, GradeDocuments, RewordQuery, GenerateAnswer
)

class Contextualizer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(ContextualizeQuery)
    
    def forward(self, chat_history, question):
        return self.prog(chat_history=chat_history, question=question)

class Grader(dspy.Module):
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(GradeDocuments)
    
    def forward(self, question, document):
        return self.prog(question=question, document=document)

class Reworder(dspy.Module):
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(RewordQuery)
    
    def forward(self, question):
        return self.prog(question=question)

class Generator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(GenerateAnswer)
    
    def forward(self, context, question):
        return self.prog(context=context, question=question)

def load_compiled_state(module_instance, path="core/dspy_modules/compiled_state.json"):
    """
    Loads compiled keys/weights into a module instance if the file exists.
    """
    if os.path.exists(path):
        try:
            module_instance.load(path)
            print(f"✅ DSPy: Loaded compiled state from {path}")
        except Exception as e:
            print(f"⚠️ DSPy: Failed to load compiled state: {e}")
    else:
        print(f"ℹ️ DSPy: No compiled state found at {path}, using zero-shot.")

if __name__ == "__main__":
    # Test execution
    from core.dspy_config import configure_dspy
    configure_dspy()
    
    gen = Generator()
    res = gen("Context: Python is a language.", "What is Python?")
    print(res)
