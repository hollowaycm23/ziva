import dspy
import json
import os

# Define a small initial Golden Dataset for bootstrapping
initial_data = [
    {
        "question": "Qual a cotação do dólar hoje?",
        "context": "Context: O dólar comercial está cotado a R$ 5,15. (Data: 2025-01-12)",
        "answer": "O dólar comercial está cotado a R$ 5,15."
    },
    {
        "question": "Quem é o presidente do Brasil?",
        "context": "Context: O atual presidente do Brasil é Luiz Inácio Lula da Silva.",
        "answer": "O atual presidente do Brasil é Luiz Inácio Lula da Silva."
    },
    {
        "question": "O que é Ziva?",
        "context": "Context: Ziva é um assistente de IA autônomo baseado em Linux.",
        "answer": "Ziva é um assistente de IA autônomo baseado em Linux."
    }
]

def build_dataset(path="training/golden_dataset.json"):
    """
    Constructs and saves the Golden Dataset.
    In a real scenario, this would load from logs or human feedback.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    examples = []
    for item in initial_data:
        # Create DSPy Example
        # Start with simple GenerateAnswer alignment
        ex = dspy.Example(
            question=item["question"],
            context=item["context"],
            answer=item["answer"]
        ).with_inputs("context", "question")
        examples.append(ex)
    
    print(f"✅ Built dataset with {len(examples)} examples.")
    return examples

if __name__ == "__main__":
    build_dataset()
