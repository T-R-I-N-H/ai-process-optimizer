from fastapi import APIRouter, HTTPException, Request
from api.schemas import VisualizeRequest, VisualizeResponse, NodeDescription
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/visualize", response_model=VisualizeResponse, summary="Generate BPMN diagram and descriptions from parsed file text", tags=["Visualization"])
async def visualize_description(request_body: VisualizeRequest, request: Request):
    """
    Generate a BPMN diagram and detailed descriptions from parsed file text.

    This endpoint takes a user prompt and the text parsed from a process file (PDF, DOCX, BPMN, etc.),
    and returns:
    - BPMN diagram data (XML)
    - A high-level diagram description
    - Detailed descriptions for each node in the diagram
    - Memory/context string for future calls

    **Sample Request:**
    ```json
    {
      "prompt": "Generate a BPMN diagram for a simple order process.",
      "file_texts": "Order Process: 1. Customer places order. 2. System processes order. 3. Order shipped. 4. Order delivered."
    }
    ```

    **Sample Response:**
    ```json
    {
      "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
      "diagram_description": "This BPMN diagram represents a simple order process with steps for placing, processing, shipping, and delivering an order.",
      "detail_descriptions": [
        {"node_id": "Task_1", "node_description": "Customer places an order."},
        {"node_id": "Task_2", "node_description": "System processes the order."},
        {"node_id": "Task_3", "node_description": "Order is shipped to the customer."},
        {"node_id": "Task_4", "node_description": "Order is delivered to the customer."}
      ],
      "memory": "session_memory_string"
    }
    ```
    """
    orchestrator = request.app.state.orchestrator
    try:
        # Use the orchestrator to generate BPMN XML and related info
        # We'll treat the prompt as the process description and file_texts as context
        session_id = orchestrator.start_new_session(user_id="visualize_api")
        result = orchestrator.process_user_query(
            session_id=session_id,
            query=request_body.prompt,
            file_texts=request_body.file_texts,
            file_type="bpmn"
        )
        data = result.get("data", {})
        # Convert detail_descriptions to NodeDescription objects if needed
        detail_descriptions = [
            NodeDescription(**desc) if not isinstance(desc, NodeDescription) else desc
            for desc in data.get("detail_descriptions", [])
        ]
        return VisualizeResponse(
            diagram_data=data.get("diagram_data", ""),
            diagram_description=data.get("diagram_description", ""),
            detail_descriptions=detail_descriptions,
            memory=""
        )
    except Exception as e:
        logger.error(f"Error calling Visualize API: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to call Visualize API: {e}") 