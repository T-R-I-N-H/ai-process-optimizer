import logging
from typing import Callable, Dict, List
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class VisualizationAgent(BaseAgent):
    """
    The Visualization Agent (VA).
    Generates BPMN diagrams from process descriptions.
    """
    
    def generate_diagram(self, process_name: str, process_steps: List[str], 
                        process_description: str = "", file_context: str = "") -> Dict:
        """
        Generates a BPMN diagram from process information.
        
        Args:
            process_name: Name of the process
            process_steps: List of process steps
            process_description: Additional description of the process
            file_context: Context from uploaded files
            
        Returns:
            Dictionary containing diagram_data, diagram_name, diagram_description, and detail_descriptions
        """
        
        # Create a focused prompt for BPMN diagram generation
        steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(process_steps)])
        
        prompt = f"""
        Generate a BPMN (Business Process Model and Notation) 2.0 XML diagram for the following process.
        
        Process Name: {process_name}
        Process Description: {process_description}
        Process Steps:
        {steps_text}
        
        File Context: {file_context}
        
        Create a valid BPMN 2.0 XML diagram that includes:
        1. A start event
        2. Tasks for each process step
        3. Sequence flows between tasks
        4. An end event
        5. Proper BPMN XML structure with namespaces
        
        Return the response in this exact JSON format:
        {{
            "diagram_data": "<bpmn:definitions xmlns:bpmn='http://www.omg.org/spec/BPMN/20100524/MODEL'>...</bpmn:definitions>",
            "diagram_name": "{process_name} Diagram",
            "diagram_description": "BPMN diagram representing the {process_name} process",
            "detail_descriptions": {{
                "StartEvent_1": "Process starts",
                "Task_1": "{process_steps[0] if process_steps else 'First task'}",
                "EndEvent_1": "Process ends"
            }}
        }}
        
        Ensure the BPMN XML is valid and follows BPMN 2.0 standards.
        """
        
        logger.info(f"VisualizationAgent: Generating BPMN diagram for process '{process_name}'")
        response = self.llm_caller(prompt, temperature=0.2, max_output_tokens=2000)
        logger.debug(f"VisualizationAgent: Raw LLM response: {response}")
        
        try:
            import json
            import re
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response_json = json.loads(json_match.group())
                return {
                    "diagram_data": response_json.get("diagram_data", "<bpmn:definitions>...</bpmn:definitions>"),
                    "diagram_name": response_json.get("diagram_name", f"{process_name} Diagram"),
                    "diagram_description": response_json.get("diagram_description", f"BPMN diagram for {process_name}"),
                    "detail_descriptions": response_json.get("detail_descriptions", {})
                }
            else:
                # Fallback if JSON parsing fails
                logger.warning("Could not parse JSON from LLM response, using fallback")
                return self._generate_fallback_diagram(process_name, process_steps)
                
        except Exception as e:
            logger.error(f"VisualizationAgent: Error parsing LLM response: {e}")
            return self._generate_fallback_diagram(process_name, process_steps)
    
    def _generate_fallback_diagram(self, process_name: str, process_steps: List[str]) -> Dict:
        """Generate a basic fallback BPMN diagram when LLM fails."""
        steps_text = "\n".join([f"<bpmn:task id='Task_{i+1}' name='{step}' />" for i, step in enumerate(process_steps)])
        
        fallback_xml = f"""<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <bpmn:process id="Process_{process_name.replace(' ', '_')}" name="{process_name}">
    <bpmn:startEvent id="StartEvent_1" name="Start" />
    {steps_text}
    <bpmn:endEvent id="EndEvent_1" name="End" />
  </bpmn:process>
</bpmn:definitions>"""
        
        detail_descriptions = {
            "StartEvent_1": "Process starts",
            "EndEvent_1": "Process ends"
        }
        for i, step in enumerate(process_steps):
            detail_descriptions[f"Task_{i+1}"] = step
        
        return {
            "diagram_data": fallback_xml,
            "diagram_name": f"{process_name} Diagram",
            "diagram_description": f"Basic BPMN diagram for {process_name}",
            "detail_descriptions": detail_descriptions
        }
    
    def process(self, process_name: str, process_steps: List[str], 
                process_description: str = "", file_context: str = "") -> Dict:
        """Generic process method for BaseAgent."""
        return self.generate_diagram(process_name, process_steps, process_description, file_context) 