import logging
from core.llm_interface import call_gemini

logger = logging.getLogger(__name__)

class VisualizeApiClient:
    def __init__(self):
        pass

    def visualize(self, prompt: str, file_texts: list) -> dict:
        """
        Dedicated visualization service that generates BPMN diagrams from process descriptions.
        This service only handles visualization, not process improvement or bottleneck analysis.
        """
        # Combine all file contents into a single string for context
        combined_file_content = ""
        for file_text in file_texts:
            combined_file_content += f"File Type: {file_text['file_type']}\n"
            combined_file_content += f"File Content:\n{file_text['file_content']}\n\n"
        
        # Create a focused prompt for BPMN diagram generation
        visualization_prompt = f"""
        Based on the following prompt and file content, generate a BPMN (Business Process Model and Notation) XML diagram.
        
        User Request: {prompt}
        
        File Content:
        {combined_file_content}
        
        Generate a valid BPMN 2.0 XML diagram that represents the process described. Include:
        1. A clear process name
        2. Sequential tasks/activities
        3. Gateways for decision points (if any)
        4. Start and end events
        5. Proper BPMN XML structure
        
        Return the response in this exact JSON format:
        {{
            "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
            "diagram_name": "Process Name Diagram",
            "diagram_description": "A clear description of what this diagram represents",
            "detail_descriptions": {{
                "Task_1": "Description of the first task",
                "Task_2": "Description of the second task"
            }}
        }}
        
        Ensure the BPMN XML is valid and follows BPMN 2.0 standards.
        """
        
        try:
            response = call_gemini(visualization_prompt, temperature=0.3, max_output_tokens=2000)
            
            # Try to extract JSON from the response
            import json
            import re
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response_json = json.loads(json_match.group())
                
                # Generate meaningful memory
                memory_content = f"""
                Visualization Session Memory:
                - User Request: {prompt}
                - Generated Diagram: {response_json.get("diagram_name", "Process Diagram")}
                - Diagram Description: {response_json.get("diagram_description", "Generated BPMN diagram")}
                - Number of Tasks: {len(response_json.get("detail_descriptions", {}))}
                - File Types Processed: {[ft['file_type'] for ft in file_texts]}
                - Generation Timestamp: {__import__('datetime').datetime.now().isoformat()}
                """
                
                return {
                    "diagram_data": response_json.get("diagram_data", "<bpmn:definitions>...</bpmn:definitions>"),
                    "diagram_name": response_json.get("diagram_name", "Process Diagram"),
                    "Diagram_description": response_json.get("diagram_description", "Generated BPMN diagram"),
                    "detail_descriptions": response_json.get("detail_descriptions", {}),
                    "Memory": memory_content.strip()
                }
            else:
                # Fallback if JSON parsing fails
                logger.warning("Could not parse JSON from LLM response, using fallback")
                fallback_memory = f"""
                Visualization Session Memory:
                - User Request: {prompt}
                - Status: Fallback diagram generated due to parsing error
                - File Types: {[ft['file_type'] for ft in file_texts]}
                - Generation Timestamp: {__import__('datetime').datetime.now().isoformat()}
                """
                
                return {
                    "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
                    "diagram_name": "Generated Process Diagram",
                    "Diagram_description": "BPMN diagram generated from process description",
                    "detail_descriptions": {"Task_1": "Process step 1", "Task_2": "Process step 2"},
                    "Memory": fallback_memory.strip()
                }
                
        except Exception as e:
            logger.error(f"Error in visualization service: {e}")
            error_memory = f"""
            Visualization Session Memory:
            - User Request: {prompt}
            - Status: Error occurred during generation
            - Error: {str(e)}
            - Generation Timestamp: {__import__('datetime').datetime.now().isoformat()}
            """
            
            # Return a basic fallback response
            return {
                "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
                "diagram_name": "Error - Process Diagram",
                "Diagram_description": "Error occurred during diagram generation",
                "detail_descriptions": {"Error": "Could not generate diagram"},
                "Memory": error_memory.strip()
            }