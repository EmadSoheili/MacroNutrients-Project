# Here I have created a FastAPI application that serves as an API for a MacroNutrients Calculator Agent.
# The application uses the FastAPI framework to handle HTTP requests and responses.
# It also implements rate limiting and CORS to ensure secure communication.
# SSE (Server-Sent Events) is used to stream responses from the API to the client in real-time.
# The application serves a static frontend UI.


# Ignore warnings related to fixed sampling defaults in the Google Generative AI Embeddings
import warnings
warnings.filterwarnings("ignore", message=".*uses fixed sampling defaults.*")

from dotenv import load_dotenv          # To load environment variables from a .env file
load_dotenv()                           # Load environment variables from .env file

import os       # To interact with the operating system
import json     # To read and write JSON files
from fastapi import FastAPI, Header, HTTPException, Request, status         # To create a FastAPI application and handle HTTP requests
from fastapi.middleware.cors import CORSMiddleware      # To handle Cross-Origin Resource Sharing (CORS)
from fastapi.responses import StreamingResponse         # To stream responses from the API
from fastapi.staticfiles import StaticFiles             # To serve static files
from pydantic import BaseModel          # To define data models for request and response validation
from slowapi import Limiter, _rate_limit_exceeded_handler        # To limit the rate of incoming requests
from slowapi.util import get_remote_address             # To get the remote address of incoming requests
from slowapi.errors import RateLimitExceeded            # To handle rate limit exceeded errors
from graph.graph import app_graph           # Import the application graph


# Initialize the rate limiter and FastAPI application
limiter = Limiter(key_func=get_remote_address)          # Define a rate limiter for incoming requests based on the remote address
app = FastAPI(title = "MacroNutrients Calculator Agent", version = "1.0.0")         # Define the FastAPI application
app.state.limiter = limiter         # Set the rate limiter for the application
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)          # Set the exception handler for rate limit exceeded errors


# Enable CORS for frontend communication to implement some security measures
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_PASSKEY = os.getenv("DEMO_PASSKEY", "secret-passkey")        # Get the demo passkey from environment variables, defaulting to "secret-passkey" if not set


# Define a Pydantic model for the chat request
class ChatRequest(BaseModel):
    message: str
    running_macros: dict = {"calories": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carbs_g": 0.0, "fiber_g": 0.0}


#
@app.post("/api/chat")          # Define the /api/chat endpoint to handle chat requests
@limiter.limit("5/minute")      # Limit to 5 requests per minute
async def chat_endpoint(request: Request, body: ChatRequest, x_demo_passkey: str = Header(default="")):
    """Streams graph execudion nodes and send results via Server-Sent Events (SSE) to the client."""

    # Verify Passkey
    if x_demo_passkey != DEMO_PASSKEY:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED if hasattr(status, 'HTTP_401_UNAUTHORIZED') else 401,
            detail="Invalid passkey. Access denied."
        )

    # Define the inputs for the graph execution
    inputs = {
        "question": body.message,
        "running_macros": body.running_macros,
        "retry_count": 0
    }

    # Define an asynchronous generator to stream graph updates
    async def event_generator():
        try:
            async for event in app_graph.astream(inputs, stream_mode="updates"):
                for node_name, node_output in event.items():
                    
                    # Helper to convert LangChain Document objects into JSON-friendly dicts
                    cleaned_output = {}
                    for k, v in node_output.items():
                        if k == "documents" and isinstance(v, list):
                            cleaned_output[k] = [{"page_content": d.page_content, "metadata": d.metadata} for d in v]
                        else:
                            cleaned_output[k] = v

                    payload = json.dumps({"node": node_name, "output": cleaned_output})
                    yield f"data: {payload}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    # Return a streaming response to the client using Server-Sent Events (SSE)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Mount static directory for Frontend UI
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")