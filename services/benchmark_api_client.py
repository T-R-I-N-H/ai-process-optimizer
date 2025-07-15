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

    def benchmark(self, diagram_data: str, memory: str) -> Dict:
        """
        Local benchmark logic: extract features from BPMN XML and memory, and return a map of factors to descriptions with mock benchmark numbers.
        """
        import xml.etree.ElementTree as ET
        factors = {}
        try:
            root = ET.fromstring(diagram_data)
            ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
            # Count tasks
            tasks = root.findall('.//bpmn:task', ns)
            factors['Number of Tasks'] = f"{len(tasks)} tasks in the process. Industry average: 8-12 tasks per process (Ref: BPMN Benchmarks 2022)."
            # Count gateways
            gateways = root.findall('.//bpmn:exclusiveGateway', ns) + root.findall('.//bpmn:parallelGateway', ns)
            factors['Number of Gateways'] = f"{len(gateways)} gateways (decision points). Typical range: 2-4 (Ref: BPMN Benchmarks 2022)."
            # Count swimlanes (pools/lanes)
            pools = root.findall('.//bpmn:participant', ns)
            lanes = root.findall('.//bpmn:lane', ns)
            factors['Number of Swimlanes'] = f"{len(pools) + len(lanes)} swimlanes (pools/lanes). Best practice: 1-3 (Ref: BPMN Best Practices 2021)."
            # Count start and end events
            starts = root.findall('.//bpmn:startEvent', ns)
            ends = root.findall('.//bpmn:endEvent', ns)
            factors['Start Events'] = f"{len(starts)} start events. Usually 1 per process."
            factors['End Events'] = f"{len(ends)} end events. Usually 1 per process."
            # Memory-based feature: if 'automation' or 'RPA' in memory
            if 'automation' in memory.lower() or 'rpa' in memory.lower():
                factors['Automation Mentioned'] = "Process mentions automation/RPA. Benchmark: 35% of processes in top companies are automated (Ref: Gartner 2023)."
            # Add more features as needed
        except Exception as e:
            factors['Parsing Error'] = f"Could not parse BPMN XML: {e}"
        return {"Benchmark_data": factors}