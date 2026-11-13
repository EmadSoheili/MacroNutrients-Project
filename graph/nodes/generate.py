# Here I have created the generate node to generate answers to nutrition-related questions.


from typing import Any, Dict                # To specify types for function arguments and return values
from graph.chains.generation import generation_chain        # To use the generation chain
from graph.state import GraphState                          # To manage the state of the graph


def generate(state: GraphState) -> Dict[str, Any]:
    print (f"\n--- GENERATING ANSWER ---\n")

    question = state["question"]
    documents = state["documents"]
    retry_count = state.get("retry_count", 0) + 1

    # Join each food item's page_content into a single context string
    context_str = "\n\n".join([doc.page_content for doc in documents])

    generation = generation_chain.invoke(
        {"context": context_str, "question": question}
    )

    return{
        "documents": documents,
        "question": question,
        "generation": generation,
        "retry_count": retry_count,
    }