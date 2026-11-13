# Here I have created the web search node to perform web searches using the Tavily API.


from dotenv import load_dotenv      # To load environment variables from a .env file
load_dotenv()                       # Load environment variables from .env file

import os
from typing import Any, Dict        # To specify the return type of the function
from langchain_core.documents import Document       # To represent documents in LangChain
from langchain_tavily import TavilySearch           # To perform web searches using Tavily
from graph.state import GraphState                  # To manage the state of the graph


# Create an instance of the TavilySearch class
web_search_tool = TavilySearch(max_results=3)


# Define the web_search function that performs a web search based on the question in the state
def web_search(state: GraphState) -> Dict[str, Any]:
    print(f"\n--- PERFORMING WEB SEARCH ---\n")

    question = state["question"]
    documents = state.get("documents", None)

    tavily_results = web_search_tool.invoke({"query": question})["results"]

    joined_tavily_results = "\n".join(
        [tavily_result["content"] for tavily_result in tavily_results]
    )

    # Capture the first URL from Tavily results to show later as a RAG reference
    source_url = tavily_results[0].get("url", "No URL found") if tavily_results else "No URL found"

    web_results = Document(
        page_content=joined_tavily_results,
        metadata={
            "food_name": f"Web Search: {question}",
            "portion": "Variable (Web)",
            "calories": 0.0,
            "protein_g": 0.0,
            "fat_g": 0.0,
            "carbs_g": 0.0,
            "fiber_g": 0.0,
            "source": f"{source_url}",
            "page_number": 0,
        }
    )


    if documents is not None:
        documents.append(web_results)
    else:
        documents = [web_results]

    return {
        "documents": documents,
        "question": question,
    }
