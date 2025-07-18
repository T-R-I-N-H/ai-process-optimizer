import logging
from typing import Callable, List, Optional
from pydantic import ValidationError

from agents.base_agent import BaseAgent
from core.models import ProcessDescription, BottleneckHypothesis, VerifiedInformation

logger = logging.getLogger(__name__)

class BottleneckAnalysisAgent(BaseAgent):
    """
    The Process Analysis & Bottleneck Identification Agent (PABIA).
    Identifies potential bottlenecks and reasons within a process.
    """
    def identify_bottlenecks(self, process_desc: ProcessDescription, verified_info: Optional[VerifiedInformation] = None, diagram_data: str = None) -> List[BottleneckHypothesis]:
        """
        Analyzes a process description and diagram to identify potential bottlenecks.
        Can incorporate verified information for refinement.
        """
        info_context = ""
        if verified_info:
            info_context = f"\nConsider the following verified information and best practices: {verified_info.summary}\nSource Confidence: {verified_info.confidence}"
        diagram_context = f"\nBPMN Diagram Data:\n{diagram_data}\n" if diagram_data else ""
        prompt = f"""
        Analyze the following business process description and BPMN diagram.
        Identify potential bottlenecks, inefficiencies, or areas for improvement based on the process steps, pain points, stated goals, and the diagram structure.
        If verified information is provided, use it to refine your analysis and inform your hypotheses.

        For each suspected bottleneck:
        1. State the 'location' (specific step or area in the process).
        2. Propose a 'reason_hypothesis' for why it's a bottleneck.
        3. List specific 'info_needed' (questions or data points) to confirm this bottleneck or to find effective solutions.

        Process Name: {process_desc.name}
        Steps: {', '.join(process_desc.steps)}
        Pain Points: {', '.join(process_desc.pain_points) if process_desc.pain_points else 'None specified'}
        Goal: {process_desc.goal}
        {info_context}
        {diagram_context}

        Provide the output as a JSON list of BottleneckHypothesis objects:
        ```json
        [
            {{
                "location": "...",
                "reason_hypothesis": "...",
                "info_needed": ["...", "..."]
            }},
            // Add more BottleneckHypothesis objects if multiple bottlenecks are identified
        ]
        ```
        Ensure the JSON is perfectly valid and can be directly parsed. Do not add any extra text outside the JSON block.
        If no obvious bottlenecks are identified, return an empty list `[]`.
        """
        logger.info(f"BottleneckAnalysisAgent: Sending prompt to LLM for process '{process_desc.name}'.")
        response_json_str = self.llm_caller(prompt, temperature=0.5, max_output_tokens=20000)
        print(response_json_str)
        logger.debug(f"BottleneckAnalysisAgent: Raw LLM response: {response_json_str}")
        try:
            if response_json_str.strip().startswith("```json"):
                response_json_str = response_json_str.strip()[len("```json"):].strip()
            if response_json_str.strip().endswith("```"):
                response_json_str = response_json_str.strip()[:-len("```")].strip()
            bottlenecks_data = eval(response_json_str)
            return [BottleneckHypothesis.model_validate(item) for item in bottlenecks_data]
        except ValidationError as e:
            logger.error(f"BottleneckAnalysisAgent: Pydantic validation error parsing LLM output: {e}\nRaw output: {response_json_str}")
            return []
        except Exception as e:
            logger.error(f"BottleneckAnalysisAgent: General error parsing LLM output: {e}\nRaw output: {response_json_str}")
            return []

    def process(self, process_desc: ProcessDescription, verified_info: Optional[VerifiedInformation] = None, diagram_data: str = None) -> List[BottleneckHypothesis]:
        return self.identify_bottlenecks(process_desc, verified_info, diagram_data)