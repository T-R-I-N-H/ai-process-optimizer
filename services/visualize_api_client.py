import logging

logger = logging.getLogger(__name__)

class VisualizeApiClient:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def visualize(self, prompt: str, file_texts: str) -> dict:
        """
        Use the LLM agent pipeline to generate BPMN XML and related info from prompt and file_texts.
        """
        # For stateless use, create a dummy session
        session_id = self.orchestrator.start_new_session(user_id="visualize_api")
        # Use the prompt as the query, and file_texts as the context
        response = self.orchestrator.process_user_query(session_id, prompt, file_texts=file_texts, file_type=None)
        if response["status"] != "completed":
            logger.error(f"VisualizeApiClient: LLM pipeline did not complete successfully: {response}")
            raise Exception(f"LLM pipeline error: {response.get('message')}")
        data = response["data"]
        # Compose detail_descriptions from improved_steps (simulate node_id as step index)
        detail_descriptions = [
            {"node_id": f"Step_{i+1}", "node_description": step}
            for i, step in enumerate(data.get("improved_process_steps", []))
        ]
        return {
            "diagram_data": data.get("diagram_data", "<bpmn:definitions>...</bpmn:definitions>"),
            "Diagram_description": data.get("diagram_description", "Improved process diagram."),
            "detail_descriptions": detail_descriptions,
            "Memory": ""
        }