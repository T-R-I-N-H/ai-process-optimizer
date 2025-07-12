from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from core.llm_interface import call_gemini
from core.orchestrator import WorkflowOrchestrator
import logging
import json
import re
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Conversation API", description="Advanced Conversation API for BPMN diagrams.", version="1.0.0")
logger = logging.getLogger(__name__)

class ConversationRequest(BaseModel):
    prompt: str = Field(..., description="User's question or modification request.")
    diagram_data: str = Field(..., description="Current BPMN XML diagram data.")
    current_memory: str = Field("", description="Current conversational memory string.")

class ConversationResponse(BaseModel):
    action: str = Field(..., description="Action taken: answer_question or modify_diagram.")
    diagram_data: str = Field(..., description="BPMN XML data (if modified, else original).")
    detail_descriptions: dict[str, str] = Field(..., description="Map of node_id to node_description.")
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
            f"Memory: {request.current_memory}\n"
            f"Answer the user's question about the process."
        )
        answer = call_gemini(answer_prompt, temperature=0.2, max_output_tokens=512)
        diagram_data = request.diagram_data
        detail_descriptions = {}  # Empty for questions
        memory = request.current_memory  # Optionally update memory if needed
    else:
        # Use structured LLM approach similar to orchestrator's _modify_diagram method
        context = f"""
        Original Diagram: {request.diagram_data}
        Conversation Memory: {request.current_memory}
        """
        
        modification_prompt = f"""
        Based on the following context, modify the BPMN diagram according to the user's request.
        
        Context:
        {context}
        
        User Modification Request: "{request.prompt}"
        
        Generate a modified BPMN 2.0 XML diagram that incorporates the requested changes.
        Also extract the node descriptions from the modified diagram.
        
        Return the response in this exact JSON format:
        {{
            "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
            "detail_descriptions": {{
                "StartEvent_1": "Process starts",
                "Task_1": "Description of the first task",
                "Task_2": "Description of the second task",
                "EndEvent_1": "Process ends"
            }},
            "summary": "Detailed description of what was modified (e.g., 'Added a new quality check task after Task_2, renamed Task_1 to 'Order Processing')"
        }}
        
        Ensure the BPMN XML is valid and follows BPMN 2.0 standards.
        The summary should clearly explain what changes were made to the diagram.
        """
        
        try:
            response = call_gemini(modification_prompt, temperature=0.3, max_output_tokens=2000)
            
            # Parse JSON response similar to orchestrator approach
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                diagram_data = result.get("diagram_data", request.diagram_data)
                detail_descriptions = result.get("detail_descriptions", {})
                answer = result.get("summary", "Diagram modified based on user request")
            else:
                # Fallback: try to extract basic information from the response
                diagram_data = request.diagram_data
                detail_descriptions = {}
                answer = f"Applied modification: {request.prompt}"
                
        except Exception as e:
            logger.error(f"Error modifying diagram: {e}")
            diagram_data = request.diagram_data
            detail_descriptions = {}
            answer = f"Error occurred during modification: {str(e)}"
        
        memory = request.current_memory  # Optionally update memory if needed

    return ConversationResponse(
        action=action,
        diagram_data=diagram_data,
        detail_descriptions=detail_descriptions,
        answer=answer,
        memory=memory
    ) 