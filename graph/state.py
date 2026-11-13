# This is to define the state of our Adaptive RAG graph


from typing import Any, Dict, List, TypedDict       # To define structured types for better type checking
from langchain_core.documents import Document            # To create Document objects for ingestion


class GraphState(TypedDict):
    """
    Represents the state of our Adaptive RAG graph.

    Attributes:
        question: User meal or nutrition query
        generation: LLM generated response
        web_search: Flag to trigger Tavily web search
        documents: List of retrieved Document objects (includes .metadata for citations)
        retry_count: Counter to cap hallucination retry loops
        running_macros: Cumulative session macros (calories, protein_g, carbs_g, fat_g)
    """
    question: str
    generation: str
    web_search: bool
    documents: List[Document]
    retry_count: int
    running_macros: Dict[str, float]