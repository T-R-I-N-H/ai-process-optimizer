import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
import time
from fastapi import FastAPI, Request

logger = logging.getLogger("uvicorn.access")  # Or your preferred logger

app = FastAPI()

@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000  # ms
    logger.info(f"Request: {request.method} {request.url.path} completed in {process_time:.2f} ms")
    return response

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from api.routers import process_router, interaction_router, visualize_router
from core.orchestrator import WorkflowOrchestrator

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Process Optimizer API",
    description="Multi-Agent Pipeline for Process Analysis, Improvement, and Visualization",
    version="1.0.0",
)

# Configure CORS (Cross-Origin Resource Sharing)
# Adjust origins as needed for your frontend deployment
origins = [
    "http://localhost",
    "http://localhost:3000", # Example for a React/Vue frontend
    "http://127.0.0.1:8000",
    # Add your production frontend URL here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Workflow Orchestrator as a global instance
orchestrator_instance = WorkflowOrchestrator()

# Add orchestrator instance to app state for easy access in routers
app.state.orchestrator = orchestrator_instance
logger.info("Workflow Orchestrator initialized and added to app state.")

# Include API routers
app.include_router(process_router, prefix="/process", tags=["Process Management"])
app.include_router(interaction_router, prefix="/interaction", tags=["External API Interactions"])
app.include_router(visualize_router, prefix="/visualize", tags=["Visualization"])
logger.info("API routers included.")

@app.get("/")
async def read_root():
    """
    Root endpoint for API health check.
    """
    logger.info("Root endpoint accessed.")
    return {"message": "AI Process Optimizer API is running!"}

# To run the application:
# uvicorn main:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    logger.info("Starting Uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)