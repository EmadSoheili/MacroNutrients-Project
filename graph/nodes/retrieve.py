# Here I have created a retriever node that will fetch relevant documents from vectorstore based on the question


from dotenv import load_dotenv          # To load environment variables from a .env file
load_dotenv()                           # Load environment variables from .env file

import os
from typing import Any, Dict            # To define type hints for function parameters and return types
from langchain_google_genai import GoogleGenerativeAIEmbeddings       # To use the Google Generative AI LLM
from langchain_pinecone import PineconeVectorStore              # To interact with Pinecone vector store
from graph.state import GraphState                              # To manage the state of the graph


# Initialize Embeddings and Pinecone Retriever
EMBEDDING = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "macronutrients-project")


# Function to retrieve relevant documents from Pinecone based on a query
retriever = PineconeVectorStore(
    index_name=INDEX_NAME,
    embedding=EMBEDDING
).as_retriever(search_kwargs={"k": 8})          # Retrieve top 8 similar documents



def retrieve(state: GraphState) -> Dict[str, Any]:
    print("\n--- RETRIEVING RELEVANT DOCUMENTS ---\n")
    
    question = state["question"]
    retry_count = state.get("retry_count", 0)

    # Fetch top matching vectors from Pinecone based on the question
    documents = retriever.invoke(question)

    return {
        "documents": documents,
        "question": question,
        "retry_count": retry_count
    }