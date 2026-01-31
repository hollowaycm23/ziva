
import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class GraphExtractor:
    """
    Extracts Subject-Predicate-Object triplets from text using LLM.
    """
    
    def __init__(self, llm):
        self.llm = llm
        
        self.prompt = PromptTemplate(
            template="""
            You are a Knowledge Graph Builder. Extract meaningful relationships from the text as triplets: (Subject, Predicate, Object).
            
            Rules:
            1. Return ONLY a JSON list of objects: [{{"subject": "...", "predicate": "...", "object": "..."}}]
            2. Keep predicates simple (e.g., "is_a", "has_part", "located_in", "born_in", "married_to").
            3. Ignore generic or vague information. Focus on factual entities.
            4. Max 5 triplets per text chunk.
            
            Text: {text}
            
            JSON Triplets:
            """,
            input_variables=["text"]
        )
        
        self.chain = self.prompt | self.llm | StrOutputParser()

    def extract_from_text(self, text: str) -> list[dict]:
        """
        Extracts triplets from text.
        Returns: [{"subject": "A", "predicate": "B", "object": "C"}, ...]
        """
        # Truncate text to avoid overly expensive calls
        safe_text = text[:2000] 
        
        try:
            response = self.chain.invoke({"text": safe_text})
            # Clean md blocks
            response = response.replace("```json", "").replace("```", "").strip()
            
            # Heuristic cleanup if raw text returned
            if not response.startswith("["):
                # Try to find first [
                idx = response.find("[")
                if idx != -1:
                    response = response[idx:]
                    
            triplets = json.loads(response)
            
            valid_triplets = []
            if isinstance(triplets, list):
                for t in triplets:
                    if "subject" in t and "predicate" in t and "object" in t:
                        valid_triplets.append(t)
            return valid_triplets
            
        except Exception as e:
            # print(f"Graph Extraction Failed: {e}")
            return []
