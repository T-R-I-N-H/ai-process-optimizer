import logging
import re
import json
from typing import Callable, List, Optional
from pydantic import ValidationError

from agents.base_agent import BaseAgent
from core.models import ProcessDescription, BottleneckHypothesis, VerifiedInformation, ImprovedProcess

logger = logging.getLogger(__name__)

class SolutionGenerationAgent(BaseAgent):
    """
    The Process Improvement & Solution Generation Agent (PISGA).
    Generates concrete solutions and outlines improved process steps.
    """
    def generate_solutions(self, process_desc: ProcessDescription, bottlenecks: List[BottleneckHypothesis], verified_info: List[VerifiedInformation], diagram_data: str = None) -> ImprovedProcess:
        bottleneck_summary = "\n".join([f"- Location: {b.location}, Reason: {b.reason_hypothesis}. Info needed: {', '.join(b.info_needed)}" for b in bottlenecks])
        verified_info_summary = "\n".join([f"- Query: {v.query}, Info: {v.summary} (Confidence: {v.confidence})" for v in verified_info])
        diagram_context = f"\nBPMN Diagram Data:\n{diagram_data}\n" if diagram_data else ""
        prompt = f"""
        Based on the following original process description, identified bottlenecks, verified information, and BPMN diagram, propose concrete, actionable solutions to improve the process. Then, describe the sequential steps of the NEW, IMPROVED process.

        Aim for practical, actionable improvements that directly address the bottlenecks and align with the user's goal.
        Consider using the verified information (best practices, data) and the diagram structure to inform your solutions.

        Original Process Name: {process_desc.name}
        Original Steps: {process_desc.steps}
        Original Pain Points: {', '.join(process_desc.pain_points) if hasattr(process_desc, 'pain_points') and process_desc.pain_points else 'None'}
        Goal: {process_desc.goal}
        {diagram_context}

        Identified Bottlenecks:
        {bottleneck_summary if bottleneck_summary else 'No specific bottlenecks identified. Focus on general optimization based on pain points.'}

        Verified Information (Relevant Best Practices/Data):
        {verified_info_summary if verified_info_summary else 'No additional verified information.'}

        IMPORTANT: Return your answer as a JSON object with the following keys and types, and do not include any text outside the JSON block:

        {{
          "name": string,  // Name of the improved process
          "original_process": {{
            "name": string,
            "steps": list of strings,  // REQUIRED: must be present
            "inputs": list of strings,
            "outputs": list of strings,
            "pain_points": list of strings,
            "metrics": object (string keys and values),
            "goal": string
          }},
          "improvements": [
            {{
              "step_number": integer or null,  // REQUIRED: must be an integer (e.g., 1, 2) or null if not applicable. DO NOT use strings.
              "description": string,
              "expected_impact": string,
              "tools_or_tech": list of strings,  // REQUIRED: must be a list, not a comma-separated string
              "actors_involved": list of strings  // REQUIRED: must be a list, not a comma-separated string
            }}
          ],
          "improved_steps": list of strings,
          "summary_of_changes": string
        }}
        
        STRICTLY follow this schema. DO NOT use keys like 'improved_process_name'. DO NOT use strings for step_number. DO NOT use comma-separated strings for tools_or_tech or actors_involved—use lists.
        """
        logger.info(f"SolutionGenerationAgent: Sending prompt to LLM for process '{process_desc.name}'.")
        response = self.llm_caller(prompt, temperature=0.7, max_output_tokens=65000)
        logger.debug(f"SolutionGenerationAgent: Raw LLM response: {response}")
        # if not response or "ERROR:" in response or "No content generated" in response:
        #     logger.error(f"SolutionGenerationAgent: LLM returned error response: {response}")
        #     return self._create_fallback_improved_process(process_desc, "LLM service unavailable")
        json_str = self._extract_json(response)
        if not json_str:
            logger.error(f"SolutionGenerationAgent: Could not extract valid JSON from response")
            return self._create_fallback_improved_process(process_desc, "Invalid JSON response")
        try:
            return ImprovedProcess.model_validate_json(json_str)
        except ValidationError as e:
            logger.error(f"SolutionGenerationAgent: Pydantic validation error parsing LLM output: {e}\nRaw output: {json_str}")
            return self._create_fallback_improved_process(process_desc, f"Validation error: {e}")
        except Exception as e:
            logger.error(f"SolutionGenerationAgent: General error parsing LLM output: {e}\nRaw output: {json_str}")
            return self._create_fallback_improved_process(process_desc, f"Parsing error: {e}")

    def _extract_json(self, response: str) -> str:
        # Remove markdown code blocks
        response = response.strip()
        if response.startswith("```json"):
            response = response[len("```json"):].strip()
        if response.startswith("```"):
            response = response[len("```"):].strip()
        if response.endswith("```"):
            response = response[:-len("```")].strip()
        # Find JSON object
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            json_str = match.group()
            # Try to fix common JSON issues
            try:
                json.loads(json_str)
                return json_str
            except Exception:
                # Try to fix single quotes and trailing commas
                fixed = json_str.replace("'", '"')
                fixed = re.sub(r',([ \t\r\n]*[}\]])', r'\1', fixed)
                try:
                    json.loads(fixed)
                    return fixed
                except Exception:
                    return ""
        return ""

    def _create_fallback_improved_process(self, process_desc: ProcessDescription, error_msg: str) -> ImprovedProcess:
            return ImprovedProcess(
                name=f"Error Improved {process_desc.name}",
                original_process=process_desc,
                improvements=[],
            improved_steps=[
                "Review current process steps",
                "Identify improvement opportunities",
                "Implement recommended changes",
                "Monitor and measure results"
            ],
            summary_of_changes=f"Process optimization could not be completed due to: {error_msg}. Please review the process manually and consider general best practices for improvement."
            )

    def process(self, process_desc: ProcessDescription, bottlenecks: List[BottleneckHypothesis], verified_info: List[VerifiedInformation], diagram_data: str = None) -> ImprovedProcess:
        return self.generate_solutions(process_desc, bottlenecks, verified_info, diagram_data)