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
from core.orchestrator import WorkflowOrchestrator
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize external API clients (assuming endpoints are in .env or config)
# In a larger app, you might use a dependency injection system (e.g., FastAPI's Depends)
# or pass these clients from a central factory/container.
conversation_api_client = ConversationApiClient()
optimize_api_client = OptimizeApiClient()
benchmark_api_client = BenchmarkApiClient()

# Dependency to get the orchestrator instance from the app state
def get_orchestrator_dependency(request: Request) -> WorkflowOrchestrator:
    return request.app.state.orchestrator

@router.post("/conversation", response_model=ConversationResponse, summary="Interact with the Conversation API for diagram questions/modifications")
async def conversation_interaction(
    request_body: ConversationRequest,
    request: Request,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator_dependency)
):
    """
    Handles conversation with the system about diagrams - questions, modifications, or information addition.
    
    This endpoint can:
    - Answer questions about existing diagrams
    - Modify diagrams based on user requests
    - Add information to conversation memory
    
    The system determines the conversation type and responds accordingly.
    """
    try:
        # Create a session for the conversation if not provided
        session_id = request_body.session_id if request_body.session_id else orchestrator.start_new_session(user_id="conversation_user")
        
        # Use the orchestrator's conversation workflow
        response = orchestrator.handle_conversation(
            session_id=session_id,
            query=request_body.prompt,
            diagram_data=request_body.diagram_data,
            memory=request_body.current_memory
        )
        
        if response["status"] == "completed":
            data = response["data"]
            return ConversationResponse(
                action=data["action"],
                data=data["data"],
                answer=data["answer"],
                memory=data["memory"]
            )
        else:
            raise HTTPException(status_code=400, detail=response["message"])
            
    except Exception as e:
        logger.error(f"Error in conversation interaction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process conversation: {e}")

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