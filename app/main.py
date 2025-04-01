import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Paper to Slides API",
    description="API for converting academic papers to presentation slides",
    version="0.1.0"
)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers after app is initialized to avoid circular imports
from app.routers import paper, slides, llm

# Include routers
app.include_router(paper.router, prefix="/api/papers", tags=["Papers"])
app.include_router(slides.router, prefix="/api/slides", tags=["Slides"])
app.include_router(llm.router, prefix="/api/llm", tags=["LLM"])

@app.get("/")
async def root():
    """Root endpoint returns API information."""
    return {
        "message": "Welcome to Paper to Slides API",
        "version": app.version,
        "docs_url": "/docs",
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
