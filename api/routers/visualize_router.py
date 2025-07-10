from fastapi import APIRouter, HTTPException
from api.schemas import VisualizeRequest, VisualizeResponse
from services.visualize_api_client import VisualizeApiClient
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

visualize_api_client = VisualizeApiClient()

@router.post("/visualize", response_model=VisualizeResponse, summary="Generate BPMN diagram from process description", tags=["Visualization"])
async def visualize_description(request_body: VisualizeRequest):
    """
    Dedicated visualization service that generates BPMN diagrams from process descriptions.
    
    This endpoint is focused solely on diagram generation and does not perform process improvement
    or bottleneck analysis. For process improvement workflows, use the /process endpoints.

    This endpoint takes a user prompt and a list of files with their types and contents,
    and returns:
    - BPMN diagram data (XML)
    - Diagram name
    - A high-level diagram description
    - Detailed descriptions for each node in the diagram (as a map)
    - Memory/context string for future calls

    **Sample Request:**
    ```json
    {
      "prompt": "Create a BPMN diagram for an online course registration process",
      "file_texts": [
        {
          "file_type": "docx",
          "file_content": "Process: 1. Student browses courses. 2. Student selects course. 3. System processes payment. 4. Student receives confirmation."
        }
      ]
    }
    ```

    **Sample Response:**
    ```json
    {
      "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
      "diagram_name": "Course Registration Process Diagram",
      "diagram_description": "BPMN diagram representing the online course registration process",
      "detail_descriptions": {
        "Task_1": "Student browses available courses",
        "Task_2": "Student selects desired course",
        "Task_3": "System processes payment",
        "Task_4": "Student receives confirmation"
      },
      "memory": ""
    }
    ```
    """
    try:
        # Convert Pydantic models to dict for the client
        file_texts_dict = [file_text.model_dump() for file_text in request_body.file_texts]
        api_response = visualize_api_client.visualize(
            prompt=request_body.prompt,
            file_texts=file_texts_dict
        )
        return VisualizeResponse(
            diagram_data=api_response["diagram_data"],
            diagram_name=api_response["diagram_name"],
            diagram_description=api_response["Diagram_description"],
            detail_descriptions=api_response["detail_descriptions"],
            memory=api_response["Memory"]
        )
    except Exception as e:
        logger.error(f"Error in visualization service: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate diagram: {e}") 