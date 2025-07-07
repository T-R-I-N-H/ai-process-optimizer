from fastapi import APIRouter, Depends, HTTPException, Request
from api.schemas import (
    ApiResponse,
    ConversationRequest, ConversationResponse,
    OptimizeRequest, OptimizeResponse,
    BenchmarkRequest, BenchmarkResponse
)
from services.conversation_api_client import ConversationApiClient
from services.optimize_api_client import OptimizeApiClient
from services.benchmark_api_client import BenchmarkApiClient
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize external API clients (assuming endpoints are in .env or config)
# In a larger app, you might use a dependency injection system (e.g., FastAPI's Depends)
# or pass these clients from a central factory/container.
conversation_api_client = ConversationApiClient()
optimize_api_client = OptimizeApiClient()
benchmark_api_client = BenchmarkApiClient()


@router.post("/conversation", response_model=ConversationResponse, summary="Interact with the Conversation API for diagram questions/modifications")
async def conversation_interaction(
    request_body: ConversationRequest
):
    """
    Sends a prompt, diagram data, and current memory to the Conversation API.
    Receives an action (answer or modify), data, answer, and updated memory.
    """
    try:
        response = conversation_api_client.interact(
            prompt=request_body.prompt,
            diagram_data=request_body.diagram_data,
            memory=request_body.current_memory
        )
        return ConversationResponse(**response)
    except Exception as e:
        logger.error(f"Error calling Conversation API: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to interact with Conversation API: {e}")

@router.post("/optimize", response_model=OptimizeResponse, summary="Call the Optimize API to get an optimized process diagram")
async def optimize_process(
    request_body: OptimizeRequest
):
    """
    Sends diagram data and optimization goals to the Optimize API.
    Receives an optimized diagram, predicted improvements, and trade-offs.
    """
    try:
        response = optimize_api_client.optimize(
            diagram_data=request_body.diagram_data,
            optimization_goals=request_body.optimization_goals,
            original_process_metrics=request_body.original_process_metrics
        )
        return OptimizeResponse(**response)
    except Exception as e:
        logger.error(f"Error calling Optimize API: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to interact with Optimize API: {e}")

@router.post("/benchmark", response_model=BenchmarkResponse, summary="Call the Benchmark API to compare process performance")
async def benchmark_process(
    request_body: BenchmarkRequest
):
    """
    Sends diagram data and target metrics to the Benchmark API.
    Receives a benchmark report and identified performance gaps.
    """
    try:
        response = benchmark_api_client.benchmark(
            diagram_data=request_body.diagram_data,
            target_metrics=request_body.target_metrics,
            industry_data=request_body.industry_data
        )
        return BenchmarkResponse(**response)
    except Exception as e:
        logger.error(f"Error calling Benchmark API: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to interact with Benchmark API: {e}")