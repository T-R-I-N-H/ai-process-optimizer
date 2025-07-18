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
                        process_description: str = "", file_context: str = "", diagram_data: str = None) -> Dict:
        """
        Generates a BPMN diagram from process information and optionally the original diagram.
        """
        steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(process_steps)])
        diagram_context = f"\nOriginal BPMN Diagram Data:\n{diagram_data}\n" if diagram_data else ""
        prompt = f"""
        Generate a BPMN 2.0 XML diagram for the improved process from the original diagram. Here are the information of the improved process:
        Improve Process Name: {process_name}
        Improve Process Summary: {process_description}
        Improve Process Steps:
        {steps_text}
        File Context: {file_context}
        {diagram_context}
        Generate a valid BPMN 2.0 XML diagram that represents the process described. Ensure the diagram accurately reflects the participants (roles/departments) and the flow of information between them. Include the following BPMN elements:

        1.  A clear and concise process name.
        2.  Appropriate Pools and Lanes to clearly segment the process by participating roles or departments (e.g., "Customer," "Bank," "Department X"). Name each Pool and Lane distinctly.
        3.  Sequential tasks/activities within each Lane. The name of each task and activity should be concise, ideally between 4-8 words, and clearly describe the action.
        4.  Gateways for decision points and conditional branching (e.g., Exclusive Gateways for "yes/no" decisions, Parallel Gateways for concurrent activities). Add these for robust process logic, even if not explicitly detailed in the input data.
        5.  Sequence Flows (solid arrows) to connect tasks/activities logically within the same Lane. Ensure all tasks are connected to subsequent tasks, gateways, or an end event, preventing disconnected elements.
        6.  Message Flows (dashed arrows) to illustrate the exchange of information or communication between different Pools or Lanes, where interactions across participants occur.
        7.  Start and end events to define the beginning and termination points of the process.
        8.  A proper and well-structured BPMN XML compliant with BPMN 2.0 standards.
        Return the response in this exact JSON format:
        {{
            "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
            "diagram_name": "Process Name Diagram",
            "diagram_description": "A clear description of what this diagram represents",
            "detail_descriptions": {{
                "Name of task 1": "Description of the first task",
                "Name of task 2": "Description of the second task"
            }}
        }}
        Ensure the BPMN XML is valid and follows BPMN 2.0 standards. Ensure the return XML is visualizable using bpmn.io
        """
        logger.info(f"VisualizationAgent: Generating BPMN diagram for process '{process_name}'")
        response = self.llm_caller(prompt, temperature=0.2, max_output_tokens=65000)
        logger.debug(f"VisualizationAgent: Raw LLM response: {response}")
        try:
            import json
            import re
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
                process_description: str = "", file_context: str = "", diagram_data: str = None) -> Dict:
        return self.generate_diagram(process_name, process_steps, process_description, file_context, diagram_data) 