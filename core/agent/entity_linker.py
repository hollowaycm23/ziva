
import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.llm import LLMService
# Assuming we can use the existing 'llm' from nodes.py or re-instantiate. 
# Better to decouple or pass it in. For now, we'll re-use the chat model config.

class EntityLinker:
    """
    Identifies entities in the query and links them to canonical forms using LLM and Glossary.
    """
    
    def __init__(self, llm):
        self.llm = llm
        
        # Fast Glossary for common deviations
        # Format: "alias": "Canonical Entity Name"
        self.glossary = {
            "lula": "Luiz Inácio Lula da Silva",
            "bolsonaro": "Jair Messias Bolsonaro",
            "fhc": "Fernando Henrique Cardoso",
            "jfk": "John F. Kennedy",
            "mlk": "Martin Luther King Jr.",
            "eua": "United States",
            "usa": "United States",
            "uk": "United Kingdom",
            "ia": "Artificial Intelligence",
            "ai": "Artificial Intelligence",
            "nlp": "Natural Language Processing",
            "rag": "Retrieval-Augmented Generation",
            "stf": "Supremo Tribunal Federal",
            "tse": "Tribunal Superior Eleitoral"
        }
        
        self.prompt = PromptTemplate(
            template="""
            You are an expert Entity Linker. Your goal is to identify the main named entities (Person, Organization, Location, Concept) in the text and provide their full CANONICAL name.
            
            Rules:
            1. Return ONLY a JSON list of strings.
            2. Canonicalize names (e.g., "Lula" -> "Luiz Inácio Lula da Silva").
            3. Translate acronyms if they are key entities (e.g., "CIA" -> "Central Intelligence Agency").
            4. If no entity is found, return [].
            
            Query: {question}
            
            JSON Entities:
            """,
            input_variables=["question"]
        )
        
        self.chain = self.prompt | self.llm | StrOutputParser()

    def extract_entities(self, question: str) -> list[str]:
        """
        Returns a list of canonical entities found in the question.
        e.g., "height of lula" -> ["Luiz Inácio Lula da Silva"]
        """
        entities = []
        question_lower = question.lower()
        
        # 1. Fast Glossary Check (Exact sub-string match heuristic)
        # We check word boundaries to avoid partial matches
        words = question_lower.split()
        for word in words:
            clean = word.strip(".,?!")
            if clean in self.glossary:
                canonical = self.glossary[clean]
                if canonical not in entities:
                    entities.append(canonical)
        
        # 2. LLM Extraction (Slower but comprehensive)
        # Only trigger if query is long/complex or no glossary hits? 
        # For now, let's always trigger for accuracy if we aren't starving resources.
        # Or, to save time, only if glossary didn't find much coverage relative to query length.
        # Let's run it.
        
        try:
            response = self.chain.invoke({"question": question})
            # Clean md blocks
            response = response.replace("```json", "").replace("```", "").strip()
            extracted = json.loads(response)
            
            if isinstance(extracted, list):
                for e in extracted:
                    if e not in entities:
                         # Double check duplicate against glossary (simple fuzzy check)
                        if not any(g_val in e for g_val in entities):
                            entities.append(e)
        except Exception as e:
            print(f"Entity Linker LLM Error: {e}")
            
        return entities

