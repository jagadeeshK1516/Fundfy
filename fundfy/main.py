"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="Fundfy AI Business Execution Platform", version="0.1.0")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
