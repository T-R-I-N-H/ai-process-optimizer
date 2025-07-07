from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.conversation_api_client import ConversationApiClient
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ConversationRequest(BaseModel):
    prompt: str = Field(..., description="User's question or modification request.")
    diagram_data: str = Field(..., description="Current BPMN XML diagram data.")
    memory: str = Field("", description="Current conversational memory string.")

class ConversationResponse(BaseModel):
    action: str = Field(..., description="Action taken: answer_question or modify_diagram.")
    data: str = Field(..., description="BPMN XML data (if modified, else original or empty).")
    answer: str = Field(..., description="Answer to the user's question.")
    memory: str = Field(..., description="Updated memory string.")

@router.post("/conversation", response_model=ConversationResponse, summary="Interact with the Conversation API", tags=["Conversation"])
def conversation_endpoint(request: ConversationRequest):
    client = ConversationApiClient()
    try:
        result = client.interact(
            prompt=request.prompt,
            diagram_data=request.diagram_data,
            memory=request.memory
        )
        return ConversationResponse(
            action=result["action"],
            data=result["data"],
            answer=result["answer"],
            memory=result["memory"]
        )
    except Exception as e:
        logger.error(f"Error calling Conversation API: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to call Conversation API: {e}") 