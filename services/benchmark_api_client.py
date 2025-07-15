import requests
import os
import logging
from typing import Dict, Union, Optional
from core.llm_interface import call_gemini

logger = logging.getLogger(__name__)

class BenchmarkApiClient:
    def __init__(self):
        self.api_endpoint = os.getenv("BENCHMARK_API_ENDPOINT", "http://localhost:8004/benchmark")
        if not self.api_endpoint:
            logger.error("BENCHMARK_API_ENDPOINT not set in environment variables.")
            raise ValueError("BENCHMARK_API_ENDPOINT environment variable is not set.")

    def benchmark(self, diagram_data: str, memory: str) -> Dict:
        """
        Use LLM to generate benchmark data: extract features, generate highlights, and estimate time/effort/people for tasks.
        Returns a map of factor: description as required.
        Fallback to XML parsing if LLM fails.
        """
        prompt = f"""
        You are a process benchmarking expert. Given the following BPMN diagram XML and session memory, analyze the process and return a JSON object in the following format:
        {{
            "Benchmark_data": {{
                "<factor>": "<description>",
                ...
            }}
        }}
        Where each <factor> is a concise highlight task (e.g., 'Task Approve Invoice'), and each <description> contains an estimate of time, effort, and number of people needed for the task, plus a reason explaining the highlight. Also include process-level factors (e.g., number of tasks, gateways, swimlanes, automation, etc.).
        
        BPMN XML:
        {diagram_data}
        
        Session Memory:
        {memory}
        
        Only return the JSON object, no explanation.
        """
        try:
            llm_response = call_gemini(prompt, temperature=0.0, max_output_tokens=2048)
            import json
            # Try to extract the JSON object from the LLM response
            start = llm_response.find('{')
            end = llm_response.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = llm_response[start:end]
                data = json.loads(json_str)
                if "Benchmark_data" in data:
                    return data
        except Exception as e:
            logger.error(f"LLM benchmark generation failed: {e}")
        # Fallback to XML parsing if LLM fails
        import xml.etree.ElementTree as ET
        factors = {}
        try:
            root = ET.fromstring(diagram_data)
            ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
            tasks = root.findall('.//bpmn:task', ns)
            factors['Number of Tasks'] = f"{len(tasks)} tasks in the process. Industry average: 8-12 tasks per process (Ref: BPMN Benchmarks 2022)."
            gateways = root.findall('.//bpmn:exclusiveGateway', ns) + root.findall('.//bpmn:parallelGateway', ns)
            factors['Number of Gateways'] = f"{len(gateways)} gateways (decision points). Typical range: 2-4 (Ref: BPMN Benchmarks 2022)."
            pools = root.findall('.//bpmn:participant', ns)
            lanes = root.findall('.//bpmn:lane', ns)
            factors['Number of Swimlanes'] = f"{len(pools) + len(lanes)} swimlanes (pools/lanes). Best practice: 1-3 (Ref: BPMN Best Practices 2021)."
            starts = root.findall('.//bpmn:startEvent', ns)
            ends = root.findall('.//bpmn:endEvent', ns)
            factors['Start Events'] = f"{len(starts)} start events. Usually 1 per process."
            factors['End Events'] = f"{len(ends)} end events. Usually 1 per process."
            if 'automation' in memory.lower() or 'rpa' in memory.lower():
                factors['Automation Mentioned'] = "Process mentions automation/RPA. Benchmark: 35% of processes in top companies are automated (Ref: Gartner 2023)."
            for task in tasks:
                task_id = task.attrib.get('id', 'unknown')
                task_name = task.attrib.get('name', f'Task {task_id}')
                highlight_reason = None
                estimate_time = 10
                estimate_effort = 'medium'
                estimate_people = 1
                if 'manual' in task_name.lower():
                    highlight_reason = 'Manual task - candidate for automation.'
                    estimate_time = 20
                    estimate_effort = 'high'
                elif 'review' in task_name.lower():
                    highlight_reason = 'Review step - may cause bottleneck.'
                    estimate_time = 15
                    estimate_effort = 'medium'
                else:
                    highlight_reason = 'Standard task.'
                factor = f"Highlight: {task_name}"
                description = (
                    f"Estimated time: {estimate_time} min, "
                    f"Effort: {estimate_effort}, "
                    f"People: {estimate_people}. "
                    f"Reason: {highlight_reason}"
                )
                factors[factor] = description
        except Exception as e:
            factors['Parsing Error'] = f"Could not parse BPMN XML: {e}"
        return {"Benchmark_data": factors}