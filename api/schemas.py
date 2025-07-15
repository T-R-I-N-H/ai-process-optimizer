from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Union
import re

# --- Common API Response Model ---
class ApiResponse(BaseModel):
    status: str = Field(description="Status of the operation (e.g., 'success', 'error', 'clarification_needed', 'completed').")
    message: str = Field(description="A descriptive message about the operation's outcome.")
    session_id: Optional[str] = Field(None, description="The session ID associated with the request.")
    data: Optional[Dict] = Field(None, description="Additional data relevant to the response.")

# --- Process Endpoints ---
# ProcessStartRequest fields are handled directly via Form and File in the endpoint,
# as it's a multipart/form-data request. No dedicated schema needed for it.

class ProcessClarifyRequest(BaseModel):
    clarification_response: str = Field(description="The user's response to a clarification request.")

# --- Conversation API Endpoint ---
class ConversationRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Optional: The session ID for the ongoing conversation. If not provided, a new session will be created.")
    prompt: str = Field(..., min_length=1, max_length=2000, description="The user's question, modification request, or information to add.")
    diagram_data: str = Field(..., min_length=10, max_length=50000, description="The current BPMN XML diagram data.")
    current_memory: str = Field(default="", max_length=10000, description="The current conversational memory string.")

    @validator('session_id')
    def validate_session_id(cls, v):
        if v is not None and not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Session ID must contain only alphanumeric characters, hyphens, and underscores')
        return v

    @validator('diagram_data')
    def validate_diagram_data(cls, v):
        if not v.strip():
            raise ValueError('Diagram data cannot be empty')
        
        # Basic XML validation
        if not v.strip().startswith('<'):
            raise ValueError('Diagram data must be valid XML')
        
        # Check for basic BPMN structure
        if 'bpmn:definitions' not in v and 'definitions' not in v:
            raise ValueError('Diagram data should contain BPMN definitions')
        
        return v

    @validator('prompt')
    def validate_prompt(cls, v):
        if not v.strip():
            raise ValueError('Prompt cannot be empty')
        return v.strip()

class ConversationResponse(BaseModel):
    action: str = Field(description="Determined action: 'answer_question', 'modify_diagram', or 'add_information'.")
    diagram_data: str = Field(description="BPMN XML data (modified diagram or original if answering).")
    detail_descriptions: dict[str, str] = Field(description="Map of node_id to node_description. Empty for answer_question, populated for modify_diagram.")
    answer: str = Field(description="The AI's answer, modification summary, or confirmation.")
    memory: str = Field(description="Updated conversational memory string.")

# --- Optimize API Endpoint ---
class OptimizeRequest(BaseModel):
    diagram_data: str = Field(description="The BPMN XML diagram data of the process to optimize.")
    memory: str = Field(default="", description="Current memory/context string.")

class OptimizeResponse(BaseModel):
    diagram_data: str = Field(description="The BPMN XML diagram data of the optimized process.")
    answer: str = Field(description="Summary of the changes made during optimization.")
    detail_descriptions: Dict[str, str] = Field(description="Map of node_id to node_description for the new diagram.")
    optimization_detail: Dict[str, str] = Field(description="Map of optimization factor to description, comparing with the old diagram.")
    memory: str = Field(description="Updated memory string, including new important information.")

# --- Benchmark API Endpoint ---
class BenchmarkRequest(BaseModel):
    session_id: str = Field(description="The session ID for the process to benchmark.")
    diagram_data: str = Field(description="The BPMN XML diagram data of the process to benchmark.")
    target_metrics: Dict[str, Union[str, float]] = Field(description="Target metrics for benchmarking (e.g., {'resolution_time': '24 hours'}).")
    industry_data: Optional[str] = Field(None, description="Optional: Relevant industry benchmark data or context.")

class BenchmarkResponse(BaseModel):
    benchmark_report: str = Field(description="A detailed report comparing the process to benchmarks.")
    performance_gaps: str = Field(description="Identified gaps in performance compared to targets.")

# --- Visualize + Description API Endpoint ---
class FileText(BaseModel):
    file_type: str = Field(description="Type of the file (e.g., 'pdf', 'docx', 'bpmn').")
    file_content: str = Field(description="Content extracted from the file.")

class VisualizeRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="Prompt for the visualization/description API.")
    file_texts: list[FileText] = Field(..., min_items=1, max_items=10, description="List of files with their types and contents.")

    @validator('file_texts')
    def validate_file_texts(cls, v):
        if not v:
            raise ValueError('At least one file must be provided')
        
        for file_text in v:
            if not file_text.file_type.strip():
                raise ValueError('File type cannot be empty')
            if not file_text.file_content.strip():
                raise ValueError('File content cannot be empty')
        
        return v

class VisualizeResponse(BaseModel):
    diagram_data: str = Field(description="BPMN XML diagram data.")
    diagram_name: str = Field(description="Name of the generated diagram.")
    diagram_description: str = Field(description="High-level description of the diagram.")
    detail_descriptions: dict[str, str] = Field(description="Map of node_id to node_description.")
    memory: str = Field(description="Memory/context string for future calls.")