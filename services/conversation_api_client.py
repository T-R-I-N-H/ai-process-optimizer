import requests
import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class ConversationApiClient:
    def __init__(self):
        self.api_endpoint = os.getenv("CONVERSATION_API_ENDPOINT", "http://localhost:8002/conversation")
        if not self.api_endpoint:
            logger.error("CONVERSATION_API_ENDPOINT not set in environment variables.")
            raise ValueError("CONVERSATION_API_ENDPOINT environment variable is not set.")

    def interact(self, prompt: str, diagram_data: str, memory: str) -> Dict:
        """
        Calls the external Conversation API.

        Args:
            prompt: The user's question or modification request.
            diagram_data: The current BPMN XML diagram data.
            memory: The current conversational memory string.

        Returns:
            A dictionary containing action, data, answer, and memory.
        """
        payload = {
            "prompt": prompt,
            "diagram_data": diagram_data,
            "memory": memory
        }
        logger.info(f"Calling Conversation API at {self.api_endpoint} with prompt: {prompt[:50]}...")
        try:
            response = requests.post(self.api_endpoint, json=payload, timeout=60)
            response.raise_for_status()
            api_response = response.json()

            required_keys = ["Action", "Data", "Answer", "Memory"]
            if not all(key in api_response for key in required_keys):
                logger.error(f"Conversation API response missing required keys: {required_keys}. Response: {api_response}")
                raise ValueError("Invalid response structure from Conversation API.")

            return {
                "action": api_response["Action"],
                "data": api_response["Data"],
                "answer": api_response["Answer"],
                "memory": api_response["Memory"]
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Network or request error calling Conversation API: {e}")
            raise ConnectionError(f"Failed to connect to Conversation API: {e}")
        except ValueError as e:
            logger.error(f"Data validation error from Conversation API: {e}")
            raise ValueError(f"Invalid data from Conversation API: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred calling Conversation API: {e}")
            raise Exception(f"Unexpected error with Conversation API: {e}")