from fastapi import APIRouter, Depends, HTTPException, Request
from api.schemas import (
    ApiResponse,
    ConversationRequest, ConversationResponse,
    OptimizeRequest, OptimizeResponse,
    BenchmarkRequest, BenchmarkResponse
)
from services.conversation_api_client import ConversationApiClient
from services.benchmark_api_client import BenchmarkApiClient
from core.orchestrator import WorkflowOrchestrator
import logging
import re

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize external API clients (assuming endpoints are in .env or config)
# In a larger app, you might use a dependency injection system (e.g., FastAPI's Depends)
# or pass these clients from a central factory/container.
conversation_api_client = ConversationApiClient()
benchmark_api_client = BenchmarkApiClient()

# Dependency to get the orchestrator instance from the app state
def get_orchestrator_dependency(request: Request) -> WorkflowOrchestrator:
    return request.app.state.orchestrator

def validate_bpmn_xml(diagram_data: str) -> bool:
    """Validate that the diagram_data contains valid BPMN XML structure."""
    try:
        # Basic XML structure check
        if not diagram_data.strip().startswith('<'):
            return False
        
        # Check for BPMN namespace or definitions
        if 'bpmn:definitions' not in diagram_data and 'definitions' not in diagram_data:
            return False
        
        # Check for basic BPMN elements
        bpmn_elements = ['process', 'task', 'startEvent', 'endEvent', 'sequenceFlow']
        has_bpmn_elements = any(element in diagram_data for element in bpmn_elements)
        
        return has_bpmn_elements
    except Exception:
        return False

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
    
    Common validation errors:
    - Empty or missing prompt
    - Invalid BPMN XML in diagram_data
    - Memory string too long (>10KB)
    - Invalid session_id format
    """
    try:
        # Additional validation beyond Pydantic
        if not request_body.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
        if not validate_bpmn_xml(request_body.diagram_data):
            raise HTTPException(
                status_code=400, 
                detail="Invalid BPMN XML structure. Diagram data must contain valid BPMN elements."
            )
        
        if len(request_body.current_memory) > 10000:
            raise HTTPException(
                status_code=400, 
                detail="Memory string too long. Maximum length is 10,000 characters."
            )
        
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
                diagram_data=data["diagram_data"],
                detail_descriptions=data["detail_descriptions"],
                answer=data["answer"],
                memory=data["memory"]
            )
        elif response["status"] == "clarification_needed":
            raise HTTPException(status_code=400, detail=response["message"])
        else:
            raise HTTPException(status_code=500, detail=response["message"])
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Handle Pydantic validation errors
        logger.error(f"Validation error in conversation: {e}")
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in conversation interaction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process conversation: {e}")

@router.post("/optimize", response_model=OptimizeResponse, summary="Call the Optimize API to get an optimized process diagram")
async def optimize_process(
    request_body: OptimizeRequest,
    request: Request,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator_dependency)
):
    """
    Optimizes the given BPMN diagram and returns the new diagram, a summary of changes, node descriptions, optimization details, and updated memory.
    """
    try:
        # Validate BPMN XML
        if not validate_bpmn_xml(request_body.diagram_data):
            raise HTTPException(
                status_code=400,
                detail="Invalid BPMN XML structure. Diagram data must contain valid BPMN elements."
            )

        # Use orchestrator to handle optimization (implement this logic in orchestrator)
        response = orchestrator.handle_optimization(
            diagram_data=request_body.diagram_data,
            memory=request_body.memory
        )
        if response["status"] == "completed":
            data = response["data"]
            return OptimizeResponse(
                diagram_data=data["diagram_data"],
                answer=data["answer"],
                detail_descriptions=data["detail_descriptions"],
                optimization_detail=data["optimization_detail"],
                memory=data["memory"]
            )
        elif response["status"] == "clarification_needed":
            raise HTTPException(status_code=400, detail=response["message"])
        else:
            raise HTTPException(status_code=500, detail=response["message"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in optimize_process: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process optimization: {e}")

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