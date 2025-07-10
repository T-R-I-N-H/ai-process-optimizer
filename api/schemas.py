from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union

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
    prompt: str = Field(description="The user's question, modification request, or information to add.")
    diagram_data: str = Field(description="The current BPMN XML diagram data.")
    current_memory: str = Field(description="The current conversational memory string.")

class ConversationResponse(BaseModel):
    action: str = Field(description="Determined action: 'answer_question', 'modify_diagram', or 'add_information'.")
    data: str = Field(description="XML data (e.g., modified diagram or original if answering).")
    answer: str = Field(description="The AI's answer, modification summary, or confirmation.")
    memory: str = Field(description="Updated conversational memory string.")

# --- Optimize API Endpoint ---
class OptimizeRequest(BaseModel):
    session_id: str = Field(description="The session ID for the process to optimize.")
    diagram_data: str = Field(description="The BPMN XML diagram data of the process to optimize.")
    optimization_goals: str = Field(description="A description of the optimization goals (e.g., 'reduce cost', 'increase throughput').")
    original_process_metrics: Optional[Dict[str, Union[str, float]]] = Field(None, description="Optional: Current performance metrics of the original process.")

class OptimizeResponse(BaseModel):
    optimized_diagram_data: str = Field(description="The BPMN XML diagram data of the optimized process.")
    predicted_improvements: str = Field(description="A summary of the predicted improvements.")
    trade_offs: str = Field(description="Any identified trade-offs or new considerations.")

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
    prompt: str = Field(description="Prompt for the visualization/description API.")
    file_texts: list[FileText] = Field(description="List of files with their types and contents.")

class VisualizeResponse(BaseModel):
    diagram_data: str = Field(description="BPMN XML diagram data.")
    diagram_name: str = Field(description="Name of the generated diagram.")
    diagram_description: str = Field(description="High-level description of the diagram.")
    detail_descriptions: dict[str, str] = Field(description="Map of node_id to node_description.")
    memory: str = Field(description="Memory/context string for future calls.")