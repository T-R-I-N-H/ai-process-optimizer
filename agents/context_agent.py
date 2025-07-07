import logging
from typing import Callable, Dict
from pydantic import ValidationError

from agents.base_agent import BaseAgent
from core.models import ProcessDescription

logger = logging.getLogger(__name__)

class ContextAgent(BaseAgent):
    """
    The User Input & Context Agent (UICA).
    Analyzes user queries and extracts initial process context.
    """
    def process_query(self, user_query: str) -> ProcessDescription:
        """
        Processes a user query to extract a structured ProcessDescription.
        """
        prompt = f"""
        Analyze the following user query about a business process.
        Extract the process name, its key sequential steps (if mentioned or implied), primary inputs, primary outputs,
        any explicitly stated pain points or inefficiencies, and the user's main goal for this process improvement.
        If any information is missing or unclear, state what needs clarification in the pain_points or goal field,
        or just provide what is available.

        User Query: "{user_query}"

        Provide the output in a JSON format that matches the ProcessDescription Pydantic model:
        ```json
        {{
            "name": "...",
            "steps": ["...", "..."],
            "inputs": ["..."],
            "outputs": ["..."],
            "pain_points": ["..."],
            "metrics": {{}},
            "goal": "..."
        }}
        ```
        Ensure the JSON is perfectly valid and can be directly parsed. Do not add any extra text outside the JSON block.
        If steps are not explicitly listed, try to infer a simple start-to-end flow.
        """
        logger.info(f"ContextAgent: Sending prompt to LLM for query: '{user_query[:100]}...'")
        response_json_str = self.llm_caller(prompt, temperature=0.2, max_output_tokens=700) # Increased max_output_tokens
        logger.debug(f"ContextAgent: Raw LLM response: {response_json_str}")

        try:
            # Attempt to clean markdown if present
            if response_json_str.strip().startswith("```json"):
                response_json_str = response_json_str.strip()[len("```json"):].strip()
            if response_json_str.strip().endswith("```"):
                response_json_str = response_json_str.strip()[:-len("```")].strip()

            return ProcessDescription.model_validate_json(response_json_str)
        except ValidationError as e:
            logger.error(f"ContextAgent: Pydantic validation error parsing LLM output: {e}\nRaw output: {response_json_str}")
            # Fallback to a default or partially filled model if parsing fails
            return ProcessDescription(
                name="Unknown Process",
                steps=[],
                inputs=[],
                outputs=[],
                pain_points=[f"Error parsing context: {e}. Raw LLM output: {response_json_str}"],
                metrics={},
                goal="Clarification needed due to parsing error."
            )
        except Exception as e:
            logger.error(f"ContextAgent: General error parsing LLM output: {e}\nRaw output: {response_json_str}")
            return ProcessDescription(
                name="Unknown Process",
                steps=[],
                inputs=[],
                outputs=[],
                pain_points=[f"Error processing context: {e}. Raw LLM output: {response_json_str}"],
                metrics={},
                goal="Clarification needed due to processing error."
            )

    def process(self, user_query: str) -> ProcessDescription:
        """Generic process method for BaseAgent."""
        return self.process_query(user_query)