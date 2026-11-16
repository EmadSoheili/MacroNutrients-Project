# Here I have created a Dockerfile for a the LangChain and FastAPI application


# 1. Start with an official lightweight Python 3.11 image
FROM python:3.11-slim

# 2. Install uv for fast, deterministic dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Copy dependency files first (caches installs if code changes later)
COPY pyproject.toml uv.lock ./

# 5. Install dependencies into the system environment using uv.lock
RUN uv sync --frozen --no-dev --no-install-project

# 6. Copy the rest of your application code into the container
COPY . .

# 7. Expose port 8080 (Google Cloud Run's default port)
EXPOSE 8080

# 8. Start FastAPI using uvicorn on port 8080
CMD ["uv", "run", "--no-sync", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]