# This script ingests nutrition data from a JSON file into a Pinecone vector database 
# This is a one-time operation that should be run after the extraction script 


from dotenv import load_dotenv      # To load environment variables from a .env file
load_dotenv()                       # Load environment variables from .env file

import json     # To read and write JSON files
import os       # To interact with the operating system
import time     # To measure execution time
from pathlib import Path        # To handle file paths in a platform-independent way
from langchain_core.documents import Document       # To represent documents in LangChain
from langchain_google_genai import GoogleGenerativeAIEmbeddings       # To generate embeddings using Google Generative AI
from langchain_pinecone import PineconeVectorStore       # To interact with Pinecone vector database


# Define Embeddings
EMBEDDING = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")


# Define Paths and constants
DATA_FILE = Path("data/nutrition_db.json")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "macronutrients-project")
BATCH_SIZE = 50


def ingest():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"{DATA_FILE} not found. Run extraction first.")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    print(f"\n--- Loaded {len(items)} items from {DATA_FILE} ---\n")

    # Create Document objects for each item in the nutrition database
    docs = []
    for item in items:
        content = (
            f"Food: {item['food_name']}\n"
            f"Portion: {item['portion']}\n"
            f"Calories: {item['calories']} kcal\n"
            f"Protein: {item['protein_g']}g\n"
            f"Fat: {item['fat_g']}g\n"
            f"Carbs: {item['carbs_g']}g\n"
            f"Fiber: {item['fiber_g']}g\n"
            f"Source: {item['source']} (Page {item['page_number']})"
        )

        metadata = {
            "food_name": item["food_name"],
            "portion": item["portion"],
            "calories": float(item["calories"]),
            "protein_g": float(item["protein_g"]),
            "fat_g": float(item["fat_g"]),
            "carbs_g": float(item["carbs_g"]),
            "fiber_g": float(item["fiber_g"]),
            "source": item["source"],
            "page_number": int(item["page_number"]),
        }

        docs.append(Document(page_content=content, metadata=metadata))


    # Initialize Pinecone
    vectorstore = PineconeVectorStore(embedding=EMBEDDING, index_name=INDEX_NAME)

    # Clear existing vectors to avoid duplicates
    print(f"Clearing existing vectors from '{INDEX_NAME}'...")
    try:
        vectorstore.delete(delete_all=True)
        print("Existing vectors successfully cleared.")
    except Exception as e:
        if "Namespace not found" in str(e) or "404" in str(e):
            print("Index is currently empty. Proceeding with fresh ingestion.")
        else:
            print(f"Notice: {e}")

    print(f"Indexing Nutrition Data into '{INDEX_NAME}' in batches of {BATCH_SIZE}...")

    # Ingest documents in batches to Pinecone
    for i in range(0, len(docs), BATCH_SIZE):
        batch = docs[i : i + BATCH_SIZE]
        
        # Retry loop to gracefully handle Google API rate limits
        for attempt in range(5):
            try:
                vectorstore.add_documents(documents=batch)
                print(f"Ingested batch {min(i + BATCH_SIZE, len(docs))} of {len(docs)}")
                time.sleep(3)
                break
            except Exception as e:
                if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                    print("*** Google rate limit reached. Waiting 65s for quota window to reset...")
                    time.sleep(65)
                else:
                    raise e

    print (f"\n--- Successfully ingested {len(docs)} documents into Pinecone index '{INDEX_NAME}'. ---\n")



if __name__ == "__main__":
    ingest()
