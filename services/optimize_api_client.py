import requests
import os
import logging
from typing import Dict, Union, Optional

logger = logging.getLogger(__name__)

class OptimizeApiClient:
    def __init__(self):
        self.api_endpoint = os.getenv("OPTIMIZE_API_ENDPOINT", "http://localhost:8003/optimize")
        if not self.api_endpoint:
            logger.error("OPTIMIZE_API_ENDPOINT not set in environment variables.")
            raise ValueError("OPTIMIZE_API_ENDPOINT environment variable is not set.")

    def optimize(self, diagram_data: str, optimization_goals: str, original_process_metrics: Optional[Dict[str, Union[str, float]]] = None) -> Dict:
        """
        Calls the external Optimize API.
        """
        payload = {
            "diagram_data": diagram_data,
            "optimization_goals": optimization_goals,
            "original_process_metrics": original_process_metrics
        }
        logger.info(f"Calling Optimize API at {self.api_endpoint} with goals: {optimization_goals[:50]}...")
        try:
            response = requests.post(self.api_endpoint, json=payload, timeout=120)
            response.raise_for_status()
            api_response = response.json()

            required_keys = ["optimized_diagram_data", "predicted_improvements", "trade_offs"]
            if not all(key in api_response for key in required_keys):
                logger.error(f"Optimize API response missing required keys: {required_keys}. Response: {api_response}")
                raise ValueError("Invalid response structure from Optimize API.")

            return api_response

        except requests.exceptions.RequestException as e:
            logger.error(f"Network or request error calling Optimize API: {e}")
            raise ConnectionError(f"Failed to connect to Optimize API: {e}")
        except ValueError as e:
            logger.error(f"Data validation error from Optimize API: {e}")
            raise ValueError(f"Invalid data from Optimize API: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred calling Optimize API: {e}")
            raise Exception(f"Unexpected error with Optimize API: {e}")