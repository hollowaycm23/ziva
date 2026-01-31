from typing import List, TypedDict


class AgentState(TypedDict):
    """
    Represents the state of the agent in the graph.

    Attributes:
        question: The user's original question.
        documents: List of retrieved documents (content).
        generation: The generated answer.
    """
    question: str
    documents: List[str]
    generation: str
    retry_count: int
    chat_history: List[str]
    mode: str
    expanded_queries: List[str]
    reflection: dict
    is_refusal: bool
