from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from core.llm_interface import call_gemini
from core.orchestrator import WorkflowOrchestrator
import logging
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Conversation API", description="Advanced Conversation API for BPMN diagrams.", version="1.0.0")
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

orchestrator = WorkflowOrchestrator()

@app.post("/conversation", response_model=ConversationResponse)
def conversation_endpoint(request: ConversationRequest):
    # 1. Intent detection using LLM
    intent_prompt = (
        f"Classify the user's intent as either 'answer_question' or 'modify_diagram'.\n"
        f"User prompt: {request.prompt}\n"
        f"If the user wants to change, add, remove, or update the diagram/process, classify as 'modify_diagram'.\n"
        f"If the user is asking about the process or diagram, classify as 'answer_question'.\n"
        f"Respond with only the intent string."
    )
    intent = call_gemini(intent_prompt, temperature=0.0, max_output_tokens=10).strip().lower()
    if 'modify' in intent:
        action = 'modify_diagram'
    else:
        action = 'answer_question'

    # 2. Orchestrate based on intent
    if action == 'answer_question':
        # Use LLM to answer based on diagram_data and memory
        answer_prompt = (
            f"You are an expert on BPMN processes.\n"
            f"Here is the BPMN XML diagram:\n{request.diagram_data}\n"
            f"User question: {request.prompt}\n"
            f"Memory: {request.memory}\n"
            f"Answer the user's question about the process."
        )
        answer = call_gemini(answer_prompt, temperature=0.2, max_output_tokens=512)
        data = request.diagram_data
        memory = request.memory  # Optionally update memory if needed
    else:
        # Use LLM to generate new process steps or modifications
        mod_prompt = (
            f"You are an expert BPMN process designer.\n"
            f"Here is the current BPMN XML diagram:\n{request.diagram_data}\n"
            f"User request: {request.prompt}\n"
            f"Memory: {request.memory}\n"
            f"Modify the BPMN diagram as requested. Return only the new BPMN XML, no explanation."
        )
        data = call_gemini(mod_prompt, temperature=0.3, max_output_tokens=2048)
        answer = f"The diagram has been modified as requested."
        memory = request.memory  # Optionally update memory if needed

    return ConversationResponse(
        action=action,
        data=data,
        answer=answer,
        memory=memory
    ) 