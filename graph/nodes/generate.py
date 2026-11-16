# Here I have created the generate node to generate answers to nutrition-related questions.

from typing import Any, Dict
from graph.chains.generation import generation_chain
from graph.state import GraphState


def generate(state: GraphState) -> Dict[str, Any]:
    print("\n--- GENERATING ANSWER ---")

    question = state["question"]
    documents = state["documents"]
    retry_count = state.get("retry_count", 0) + 1

    # Join each food item's page_content into a single context string
    context_str = "\n\n".join([doc.page_content for doc in documents])

    generation = generation_chain.invoke(
        {"context": context_str, "question": question}
    )

    # Extract only the current meal's macros so retries do not double-count
    meal_macros = {
        "calories": round(generation.calories, 1),
        "protein_g": round(generation.protein_g, 1),
        "carbs_g": round(generation.carbs_g, 1),
        "fat_g": round(generation.fat_g, 1),
        "fiber_g": round(generation.fiber_g, 1),
    }

    return {
        "documents": documents,
        "question": question,
        "generation": generation.answer,
        "retry_count": retry_count,
        "running_macros": meal_macros,
    }