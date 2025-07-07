import logging
from typing import Callable, List
from pydantic import ValidationError

from agents.base_agent import BaseAgent
from core.models import ProcessDescription, BottleneckHypothesis, VerifiedInformation, ImprovedProcess, ProposedImprovement

logger = logging.getLogger(__name__)

class SolutionGenerationAgent(BaseAgent):
    """
    The Process Improvement & Solution Generation Agent (PISGA).
    Generates concrete solutions and outlines improved process steps.
    """
    def generate_solutions(self, process_desc: ProcessDescription, bottlenecks: List[BottleneckHypothesis], verified_info: List[VerifiedInformation]) -> ImprovedProcess:
        """
        Generates improvement solutions and outlines the improved process based on analysis.
        """
        bottleneck_summary = "\n".join([f"- Location: {b.location}, Reason: {b.reason_hypothesis}. Info needed: {', '.join(b.info_needed)}" for b in bottlenecks])
        verified_info_summary = "\n".join([f"- Query: {v.query}, Info: {v.summary} (Confidence: {v.confidence})" for v in verified_info])

        prompt = f"""
        Based on the following original process description, identified bottlenecks, and verified information,
        propose concrete, actionable solutions to improve the process.
        Then, describe the sequential steps of the NEW, IMPROVED process.

        Aim for practical, actionable improvements that directly address the bottlenecks and align with the user's goal.
        Consider using the verified information (best practices, data) to inform your solutions.

        Original Process Name: {process_desc.name}
        Original Steps: {process_desc.steps}
        Original Pain Points: {', '.join(process_desc.pain_points) if process_desc.pain_points else 'None'}
        Goal: {process_desc.goal}

        Identified Bottlenecks:
        {bottleneck_summary if bottleneck_summary else 'No specific bottlenecks identified. Focus on general optimization based on pain points.'}

        Verified Information (Relevant Best Practices/Data):
        {verified_info_summary if verified_info_summary else 'No additional verified information.'}

        Provide the output in a JSON format that strictly matches the ImprovedProcess Pydantic model:
        ```json
        {{
            "name": "Improved {process_desc.name}",
            "original_process": {process_desc.model_dump_json()},
            "improvements": [
                {{
                    "step_number": null,
                    "description": "A detailed description of the proposed change (e.g., 'Implement an automated chatbot for initial customer queries').",
                    "expected_impact": "Expected benefits (e.g., 'Reduce initial response time by 50%', 'Decrease manual effort by 20%', 'Improve customer satisfaction').",
                    "tools_or_tech": ["Tools or technologies recommended, e.g., 'Zendesk Chatbot', 'Power Automate'"],
                    "actors_involved": ["Roles or departments involved, e.g., 'Customer Support', 'IT Department'"]
                }},
                // Add more ProposedImprovement objects for each distinct solution
            ],
            "improved_steps": ["Step 1 of improved process", "Step 2 of improved process", "..."],
            "summary_of_changes": "A high-level summary of all proposed changes and their overall impact."
        }}
        ```
        Ensure the JSON is perfectly valid and can be directly parsed. Do not add any extra text outside the JSON block.
        Ensure 'improved_steps' is a clear, concise, sequential list representing the new flow.
        """
        logger.info(f"SolutionGenerationAgent: Sending prompt to LLM for process '{process_desc.name}'.")
        response_json_str = self.llm_caller(prompt, temperature=0.7, max_output_tokens=1800) # Increased max_output_tokens
        logger.debug(f"SolutionGenerationAgent: Raw LLM response: {response_json_str}")

        try:
            # Attempt to clean markdown if present
            if response_json_str.strip().startswith("```json"):
                response_json_str = response_json_str.strip()[len("```json"):].strip()
            if response_json_str.strip().endswith("```"):
                response_json_str = response_json_str.strip()[:-len("```")].strip()

            return ImprovedProcess.model_validate_json(response_json_str)
        except ValidationError as e:
            logger.error(f"SolutionGenerationAgent: Pydantic validation error parsing LLM output: {e}\nRaw output: {response_json_str}")
            # Fallback to a default or partially filled model if parsing fails
            return ImprovedProcess(
                name=f"Error Improved {process_desc.name}",
                original_process=process_desc,
                improvements=[],
                improved_steps=["Error in generating improved steps due to parsing issue."],
                summary_of_changes=f"Could not generate complete improvements due to an error: {e}. Raw output: {response_json_str}"
            )
        except Exception as e:
            logger.error(f"SolutionGenerationAgent: General error parsing LLM output: {e}\nRaw output: {response_json_str}")
            return ImprovedProcess(
                name=f"Error Improved {process_desc.name}",
                original_process=process_desc,
                improvements=[],
                improved_steps=["Error in generating improved steps due to processing issue."],
                summary_of_changes=f"An unexpected error occurred while generating improvements: {e}. Raw output: {response_json_str}"
            )

    def process(self, process_desc: ProcessDescription, bottlenecks: List[BottleneckHypothesis], verified_info: List[VerifiedInformation]) -> ImprovedProcess:
        """Generic process method for BaseAgent."""
        return self.generate_solutions(process_desc, bottlenecks, verified_info)