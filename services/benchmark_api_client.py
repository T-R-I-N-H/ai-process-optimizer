import requests
import os
import logging
from typing import Dict, Union, Optional

logger = logging.getLogger(__name__)

class BenchmarkApiClient:
    def __init__(self):
        self.api_endpoint = os.getenv("BENCHMARK_API_ENDPOINT", "http://localhost:8004/benchmark")
        if not self.api_endpoint:
            logger.error("BENCHMARK_API_ENDPOINT not set in environment variables.")
            raise ValueError("BENCHMARK_API_ENDPOINT environment variable is not set.")

    def benchmark(self, diagram_data: str, target_metrics: Dict[str, Union[str, float]], industry_data: Optional[str] = None) -> Dict:
        """
        Calls the external Benchmark API.
        """
        payload = {
            "diagram_data": diagram_data,
            "target_metrics": target_metrics,
            "industry_data": industry_data
        }
        logger.info(f"Calling Benchmark API at {self.api_endpoint} with target metrics: {target_metrics}...")
        try:
            response = requests.post(self.api_endpoint, json=payload, timeout=60)
            response.raise_for_status()
            api_response = response.json()

            required_keys = ["benchmark_report", "performance_gaps"]
            if not all(key in api_response for key in required_keys):
                logger.error(f"Benchmark API response missing required keys: {required_keys}. Response: {api_response}")
                raise ValueError("Invalid response structure from Benchmark API.")

            return api_response

        except requests.exceptions.RequestException as e:
            logger.error(f"Network or request error calling Benchmark API: {e}")
            raise ConnectionError(f"Failed to connect to Benchmark API: {e}")
        except ValueError as e:
            logger.error(f"Data validation error from Benchmark API: {e}")
            raise ValueError(f"Invalid data from Benchmark API: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred calling Benchmark API: {e}")
            raise Exception(f"Unexpected error with Benchmark API: {e}")