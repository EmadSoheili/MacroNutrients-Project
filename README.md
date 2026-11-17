# 🥗 MacroNutrients Agentic RAG

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Adaptive_RAG-emerald)
![Gemini](https://img.shields.io/badge/Google-Gemini_3.5_Flash_Lite-4285F4?logo=google&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-SSE_Streaming-009688?logo=fastapi&logoColor=white)
![Pinecone](https://img.shields.io/badge/Pinecone-Vector_DB-black)
![Cloud Run](https://img.shields.io/badge/Google_Cloud-Run-4285F4?logo=googlecloud&logoColor=white)

An **Adaptive Retrieval-Augmented Generation (RAG)** agent that calculates accurate macronutrients (calories, protein, carbs, fat, and fiber) for any meal or food item. Built with **LangGraph**, **Gemini 3.5 Flash Lite**, **Pinecone**, **Tavily**, and **FastAPI**, and deployed on **Google Cloud Run**.

* **Live Demo:** https://macronutrients-agent-814923894075.us-east1.run.app
* **Note:** Protected by a demo passkey in the top-right header.

---

## Key Features

* **Self-Correcting RAG:** Grades retrieved nutrition documents, falls back to Tavily web search if a food is missing, and verifies calculations before responding.
* **Live Node Streaming:** Streams LangGraph node execution (`retrieve` -> `grade_documents` -> `generate`) in real time via Server-Sent Events (SSE).
* **Session Macro Tracker:** Automatically updates **Macros of the Day** (`Cal`, `Pro`, `Carb`, `Fat`, `Fiber`) across queries.
* **Source Citations:** Shows exact PDF page numbers or web sources for every calculation.

---

## Demo & Observability

### Web Interface
![MacroNutrients Agentic RAG UI](assets/MacroNutrients%20Agentic%20RAG.png)

### LangSmith Tracing
![LangSmith Trace](assets/LangSmith.png)

---

## System Architecture

![LangGraph Architecture](assets/graph.png)

1. **Retrieve:** Searches the `macronutrients-project` Pinecone index for matching foods.
2. **Grade Documents:** Filters out irrelevant matches using structured Gemini outputs.
3. **Web Search Fallback:** Queries Tavily if any requested food is missing from the local database.
4. **Generate & Validate:** Scales values to requested portions, checks for hallucinations and completeness, and formats the response.

---

## Tech Stack

* **LLM & Embeddings:** Google Gemini 3.5 Flash Lite, Google Generative AI Embeddings
* **Agent & Observability:** LangGraph, LangChain, LangSmith
* **Retrieval:** Pinecone, Tavily Search API
* **Backend & Frontend:** FastAPI (SSE), SlowAPI, HTML, Tailwind CSS, JavaScript
* **Cloud & CI/CD:** Docker, `uv`, Google Cloud Run, Cloud Build, Secret Manager

---

## Data Sources & Ingestion (One-Time Setup)

### Reference PDFs
* [Health Canada: Nutrient Value of Some Common Foods](https://www.canada.ca/content/dam/hc-sc/migration/hc-sc/fn-an/alt_formats/pdf/nutrition/fiche-nutri-data/nvscf-vnqau-eng.pdf)
* [FitForFilms: Macros of Common Foods (V3)](https://fitforfilms.com/wp-content/uploads/Macros-of-common-foods-V3.pdf)

### Offline Pipeline
Two one-time scripts in `scripts/` build the vector database from the PDFs above:

1. **PDF Extraction (`scripts/extract_nutrition_data.py`):** Extracts 62 pages of nutritional tables into `data/nutrition_db.json` (**1,455 food items**).
   * ![PDF Processing 1](assets/PDF%20Processing%201.png)
   * ![PDF Processing 2](assets/PDF%20Processing%202.png)

2. **Vector Ingestion (`scripts/ingestion.py`):** Embeds and upserts all 1,455 items into Pinecone in batches of 50.
   * ![Ingestion](assets/Ingestion.png)
   * ![Pinecone](assets/Pinecone.png)

---

## Project Structure

```text
MacroNutrients-Project/
├── assets/
│   ├── graph.png                       # Compiled LangGraph architecture diagram
│   ├── Ingestion.png                   # Pinecone batch ingestion log screenshot
│   ├── LangSmith.png                   # LangSmith trace screenshot
│   ├── MacroNutrients Agentic RAG.png  # Live web UI screenshot
│   ├── PDF Processing 1.png            # PDF extraction log (FitForFilms & Health Canada)
│   ├── PDF Processing 2.png            # PDF extraction log (Health Canada completion)
│   └── Pinecone.png                    # Pinecone index dashboard screenshot
├── data/
│   ├── FitForFilms.pdf                 # Source PDF 1: Macros of Common Foods
│   ├── HealthCanada.pdf                # Source PDF 2: Nutrient Value of Common Foods
│   └── nutrition_db.json               # 1,455 structured food records extracted from PDFs
├── graph/
│   ├── chains/
│   │   ├── __init__.py
│   │   ├── answer_grader.py            # Verifies response answers the user's question
│   │   ├── generation.py               # Calculates scaled macros and formats Markdown
│   │   ├── hallucination_grader.py     # Checks calculations against retrieved documents
│   │   └── retrieval_grader.py         # Evaluates relevance of retrieved food items
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── generate.py                 # Executes macro generation chain
│   │   ├── grade_documents.py          # Filters retrieved documents and flags web search
│   │   ├── retrieve.py                 # Queries Pinecone vector store
│   │   └── web_search.py               # Runs Tavily fallback search for missing foods
│   ├── __init__.py
│   ├── consts.py                       # Node name constants
│   ├── graph.py                        # StateGraph workflow and conditional routing
│   └── state.py                        # GraphState TypedDict definition
├── scripts/
│   ├── extract_nutrition_data.py       # One-time Gemini PDF-to-JSON extraction script
│   └── ingestion.py                    # One-time Pinecone batch embedding & upsert script
├── static/
│   ├── app.js                          # SSE stream reader, Markdown parser & macro tracker
│   └── index.html                      # Tailwind CSS dark-mode frontend UI
├── .dockerignore                       # Excludes local env and cache files from Docker build
├── .env                                # Local environment variables (gitignored)
├── .gitignore                          # Git ignore rules
├── .python-version                     # Python version pin (3.11)
├── Dockerfile                          # Production container configuration using uv
├── main.py                             # FastAPI server, SSE endpoint, passkey auth & rate limiter
├── pyproject.toml                      # Project dependencies and metadata
├── README.md                           # Project documentation
└── uv.lock                             # Locked dependency versions
```

---

## Local Setup

1. **Clone & Install:**
   ```bash
   git clone [https://github.com/EmadSoheili/MacroNutrients-Project.git](https://github.com/EmadSoheili/MacroNutrients-Project.git)
   cd MacroNutrients-Project
   uv sync
   ```

2. **Add `.env` File:**
   ```env
   GOOGLE_API_KEY=your_google_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_INDEX_NAME=macronutrients-project
   TAVILY_API_KEY=your_tavily_api_key
   LANGCHAIN_API_KEY=your_langsmith_api_key
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=MacroNutrients-Agent
   DEMO_PASSKEY=your_chosen_passkey
   ```

3. **Run Server:**
   ```bash
   uv run uvicorn main:app --reload --port 8080
   ```
   Open `http://localhost:8080` and enter your `DEMO_PASSKEY`.

---

## Deployment & Security

* **Google Cloud Run:** Containerized with Docker + `uv` and configured to scale to zero when idle.
* **CI/CD:** Connected to GitHub via Cloud Build for automatic deployments on push to `main`.
* **Security:** Secrets stored in Google Cloud Secret Manager, protected by `x-demo-passkey` header validation and `5/minute` IP rate limiting.
