import os
import uuid
import logging
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

from core.models import ProcessDescription, BottleneckHypothesis, VerifiedInformation, ImprovedProcess
from agents.context_agent import ContextAgent
from agents.bottleneck_agent import BottleneckAnalysisAgent
from agents.information_retrieval_agent import InformationRetrievalAgent
from agents.solution_generation_agent import SolutionGenerationAgent
from core.llm_interface import call_gemini

logger = logging.getLogger(__name__)

class WorkflowOrchestrator:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {} # Session ID -> session_data
        self.context_agent = ContextAgent(call_gemini)
        self.bottleneck_agent = BottleneckAnalysisAgent(call_gemini)
        self.ir_agent = InformationRetrievalAgent(call_gemini)
        self.solution_agent = SolutionGenerationAgent(call_gemini)

    def start_new_session(self, user_id: str) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "user_id": user_id,
            "query": None,
            "original_file_texts": None,
            "original_file_type": None,
            "process_desc": None,
            "bottlenecks": [],
            "verified_info": [],
            "improved_process": None,
            "diagram_data": None,
            "diagram_description": None,
            "detail_descriptions": [],
            "visualization_memory": "",  # To store memory from the Visualize API
            "conversation_memory": "",   # For Conversation API
            "status": "Initialized",
            "last_step_completed": None
        }
        logger.info(f"New session started for user {user_id}: {session_id}")
        return session_id

    def process_user_query(self, session_id: str, query: str, file_texts: Optional[str] = None, file_type: Optional[str] = None) -> Dict:
        session_data = self.sessions.get(session_id)
        if not session_data:
            logger.error(f"Session {session_id} not found during process_user_query.")
            return {"status": "error", "message": "Invalid session ID."}

        session_data["query"] = query
        session_data["original_file_texts"] = file_texts
        session_data["original_file_type"] = file_type
        session_data["status"] = "Processing Query"
        session_data["last_step_completed"] = None

        logger.info(f"[{session_id}] Processing user query: '{query[:50]}...' with file_type: {file_type}")

        try:
            # 1. Context Agent
            logger.info(f"[{session_id}] Calling Context Agent...")
            process_desc = self.context_agent.process_query(query)
            session_data["process_desc"] = process_desc
            session_data["last_step_completed"] = "context_analysis"
            logger.info(f"[{session_id}] Context Agent processed. Process: {process_desc.name}")

            if not process_desc.name or not process_desc.steps:
                session_data["status"] = "Clarification Needed"
                session_data["data"] = {"clarification_message": "Could not fully understand the process. Please provide more details about its steps, inputs, or outputs."}
                logger.warning(f"[{session_id}] Context Agent needs clarification.")
                return {"status": "clarification_needed", "message": "More details needed to understand the process.", "session_id": session_id, "data": session_data["data"]}

            # 2. Process Analysis & Bottleneck Identification Agent (with IRVA loop)
            logger.info(f"[{session_id}] Calling Bottleneck Analysis Agent...")
            bottleneck_hypotheses = self.bottleneck_agent.identify_bottlenecks(process_desc)
            session_data["bottlenecks"] = bottleneck_hypotheses
            session_data["last_step_completed"] = "bottleneck_hypotheses"
            logger.info(f"[{session_id}] Bottleneck Agent identified initial hypotheses: {len(bottleneck_hypotheses)}")

            if not bottleneck_hypotheses:
                session_data["status"] = "Clarification Needed"
                session_data["data"] = {"clarification_message": "Could not identify clear bottlenecks. Can you elaborate on the problems or specific areas of slowness/cost?"}
                logger.warning(f"[{session_id}] Bottleneck Agent needs clarification.")
                return {"status": "clarification_needed", "message": "No clear bottlenecks identified.", "session_id": session_id, "data": session_data["data"]}

            verified_info_list = []
            if bottleneck_hypotheses:
                for info_need in bottleneck_hypotheses[0].info_needed:
                    logger.info(f"[{session_id}] IRVA: Retrieving info for '{info_need}'...")
                    info = self.ir_agent.retrieve_and_verify(info_need)
                    verified_info_list.append(info)
                    session_data["verified_info"].append(info)
                    logger.info(f"[{session_id}] IRVA: Retrieved info. Confidence: {info.confidence}")

            if verified_info_list:
                refined_bottlenecks = self.bottleneck_agent.identify_bottlenecks(process_desc, verified_info_list[0])
                if refined_bottlenecks:
                    session_data["bottlenecks"] = refined_bottlenecks
                    logger.info(f"[{session_id}] Bottleneck Agent refined hypotheses using verified info.")

            session_data["last_step_completed"] = "bottleneck_analysis_complete"

            # 3. Process Improvement & Solution Generation Agent
            logger.info(f"[{session_id}] Calling Solution Agent...")
            improved_process = self.solution_agent.generate_solutions(
                process_desc=session_data["process_desc"],
                bottlenecks=session_data["bottlenecks"],
                verified_info=session_data["verified_info"]
            )
            session_data["improved_process"] = improved_process
            session_data["last_step_completed"] = "solution_generation"
            logger.info(f"[{session_id}] Solution Agent proposed improvements.")

            # 4. Visualization (Use LLM to generate BPMN XML)
            logger.info(f"[{session_id}] Generating BPMN XML and descriptions by LLM.")
            # Use LLM to generate BPMN XML
            bpmn_prompt = (
                f"Generate a BPMN 2.0 XML diagram for the following improved process. "
                f"The process name is: '{improved_process.name}'. "
                f"The steps are: " + ", ".join(improved_process.improved_steps) + ". "
                f"Return only the BPMN XML content, no explanation."
            )
            bpmn_xml = call_gemini(bpmn_prompt, temperature=0.2, max_output_tokens=2048)
            diagram_description = f"This BPMN diagram represents the improved process '{improved_process.name}' with {len(improved_process.improved_steps)} steps."
            detail_descriptions = [
                {"node_id": f"Step_{i+1}", "node_description": step}
                for i, step in enumerate(improved_process.improved_steps)
            ]
            session_data["diagram_data"] = bpmn_xml
            session_data["diagram_description"] = diagram_description
            session_data["detail_descriptions"] = detail_descriptions
            session_data["visualization_memory"] = ""  # No external memory
            session_data["last_step_completed"] = "visualization_complete"
            logger.info(f"[{session_id}] BPMN XML and descriptions generated by LLM.")

            session_data["status"] = "completed"
            session_data["message"] = "Process analysis and improvement complete!"
            session_data["data"] = {
                "improved_process_summary": improved_process.summary_of_changes,
                "improved_process_steps": improved_process.improved_steps,
                "diagram_data": session_data["diagram_data"],
                "diagram_description": session_data["diagram_description"],
                "detail_descriptions": session_data["detail_descriptions"]
            }
            return {"status": "completed", "message": "Process analysis and improvement complete!", "session_id": session_id, "data": session_data["data"]}

        except Exception as e:
            session_data["status"] = "error"
            session_data["message"] = f"An error occurred during processing: {e}"
            logger.exception(f"[{session_id}] Critical error during process_user_query.")
            return {"status": "error", "message": f"An error occurred: {e}", "session_id": session_id}


    def resume_session_with_clarification(self, session_id: str, clarification_response: str) -> Dict:
        session_data = self.sessions.get(session_id)
        if not session_data:
            logger.error(f"Session {session_id} not found during resume_session_with_clarification.")
            return {"status": "error", "message": "Invalid session ID."}

        if session_data["status"] != "Clarification Needed":
            logger.warning(f"[{session_id}] Attempted to clarify a session not in 'Clarification Needed' state. Current status: {session_data['status']}")
            return {"status": "error", "message": "Session is not awaiting clarification."}

        session_data["query"] += f"\n\nUser Clarification: {clarification_response}"
        logger.info(f"[{session_id}] Resuming session with clarification: '{clarification_response[:50]}...'")

        return self.process_user_query(
            session_id=session_id,
            query=session_data["query"],
            file_texts=session_data["original_file_texts"],
            file_type=session_data["original_file_type"]
        )

    def get_session_status(self, session_id: str) -> Dict:
        session_data = self.sessions.get(session_id)
        if not session_data:
            return {"status": "error", "message": "Session not found."}

        if session_data["status"] == "completed":
            return {
                "status": "completed",
                "message": session_data["message"],
                "data": {
                    "improved_process_summary": session_data["improved_process"].summary_of_changes,
                    "improved_process_steps": session_data["improved_process"].improved_steps,
                    "diagram_data": session_data["diagram_data"],
                    "diagram_description": session_data["diagram_description"],
                    "detail_descriptions": session_data["detail_descriptions"],
                    # 'visualization_memory' and 'conversation_memory' are for BE, not returned directly here in status
                }
            }
        elif session_data["status"] == "Clarification Needed":
            return {
                "status": "clarification_needed",
                "message": session_data["data"]["clarification_message"],
                "data": {"clarification_message": session_data["data"]["clarification_message"]}
            }
        else:
            return {
                "status": session_data["status"],
                "message": session_data["message"],
                "data": {"last_step": session_data["last_step_completed"]}
            }

    def end_session(self, session_id: str) -> Dict:
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"[{session_id}] Session ended.")
            return {"status": "success", "message": "Session ended."}
        return {"status": "error", "message": "Session not found."}