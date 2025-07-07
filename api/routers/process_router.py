from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request, Form
from typing import Optional
from api.schemas import ApiResponse, ProcessClarifyRequest
from core.orchestrator import WorkflowOrchestrator
from utils.file_parser import parse_uploaded_file
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Dependency to get the orchestrator instance from the app state
def get_orchestrator_dependency(request: Request) -> WorkflowOrchestrator:
    return request.app.state.orchestrator

@router.post("/start", response_model=ApiResponse, summary="Start a new process analysis session")
async def start_process_analysis(
    request: Request, # <--- MOVED TO THE BEGINNING (non-default)
    user_id: str = Form(..., description="Identifier for the user initiating the process."),
    query: str = Form(..., description="The user's initial query or process description."),
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator_dependency),
    input_file: Optional[UploadFile] = File(None, description="Optional: Input file (PDF, DOCX, BPMN) for process context.")
):
    """
    Initiates a new multi-agent process analysis session.
    Optionally accepts an input file (PDF, DOCX, BPMN) for context.
    """
    file_texts = ""
    file_type = None

    if input_file:
        try:
            file_content = await input_file.read()
            file_texts, file_type = parse_uploaded_file(input_file.filename, file_content)
            logger.info(f"Parsed file: {input_file.filename}, type: {file_type}")
        except Exception as e:
            logger.error(f"Error parsing uploaded file {input_file.filename}: {e}")
            raise HTTPException(status_code=400, detail=f"Could not parse file: {e}")

    session_id = orchestrator.start_new_session(user_id)
    response = orchestrator.process_user_query(session_id, query, file_texts, file_type)

    return ApiResponse(
        status=response.get("status", "error"),
        message=response.get("message", "An unknown error occurred."),
        session_id=session_id,
        data=response.get("data")
    )

@router.get("/{session_id}/status", response_model=ApiResponse, summary="Get the status and results of a process analysis session")
async def get_process_status(
    session_id: str,
    request: Request, # <--- MOVED TO THE BEGINNING (non-default)
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator_dependency)
):
    """
    Retrieves the current status and results of a specific process analysis session.
    """
    session_status = orchestrator.get_session_status(session_id)

    if session_status["status"] == "error" and "Session not found" in session_status["message"]:
        raise HTTPException(status_code=404, detail=session_status["message"])

    return ApiResponse(
        status=session_status["status"],
        message=session_status["message"],
        session_id=session_id,
        data=session_status.get("data")
    )

@router.post("/{session_id}/clarify", response_model=ApiResponse, summary="Provide clarification for a paused session")
async def provide_clarification(
    session_id: str,
    clarification_request: ProcessClarifyRequest,
    request: Request, # <--- MOVED TO THE BEGINNING (non-default)
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator_dependency)
):
    """
    Provides additional information to the system when a session requires clarification.
    """
    response = orchestrator.resume_session_with_clarification(
        session_id,
        clarification_request.clarification_response
    )

    if response.get("status") == "error":
        raise HTTPException(status_code=400, detail=response.get("message"))

    return ApiResponse(
        status=response.get("status"),
        message=response.get("message"),
        session_id=session_id,
        data=response.get("data")
    )

@router.post("/{session_id}/end", response_model=ApiResponse, summary="End a process analysis session")
async def end_process_session(
    session_id: str,
    request: Request, # <--- MOVED TO THE BEGINNING (non-default)
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator_dependency)
):
    """
    Ends and cleans up resources for a specific process analysis session.
    """
    response = orchestrator.end_session(session_id)

    if response.get("status") == "error":
        raise HTTPException(status_code=404, detail=response.get("message"))

    return ApiResponse(
        status=response.get("status"),
        message=response.get("message"),
        session_id=session_id
    )