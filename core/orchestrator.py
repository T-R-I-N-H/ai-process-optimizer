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
from agents.visualization_agent import VisualizationAgent
from core.llm_interface import call_gemini
from services.visualize_api_client import VisualizeApiClient
from utils.language import detect_language
import re
import json

logger = logging.getLogger(__name__)

LANGUAGE_INSTRUCTIONS = {
    'vi': 'Trả lời người dùng bằng tiếng Việt. Tất cả giải thích, tóm tắt, và mô tả phải sử dụng tiếng Việt.',
    'en': 'Answer the user in English. All explanations, summaries, and descriptions must be in English.'
}
def get_language_instruction(language: str) -> str:
    return LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS['en'])

class WorkflowOrchestrator:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {} # Session ID -> session_data
        self.context_agent = ContextAgent(call_gemini)
        self.bottleneck_agent = BottleneckAnalysisAgent(call_gemini)
        self.ir_agent = InformationRetrievalAgent(call_gemini)
        self.solution_agent = SolutionGenerationAgent(call_gemini)
        self.visualization_agent = VisualizationAgent(call_gemini)

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

    def determine_user_intent(self, query: str) -> str:
        """
        Determine the user's intent from their query.
        Returns: 'visualize', 'improve', 'analyze', or 'conversation'
        """
        intent_prompt = f"""
        Analyze the following user query and determine their primary intent:
        
        Query: "{query}"
        
        Classify the intent as one of:
        - "visualize": User wants to create/generate a BPMN diagram from a process description
        - "improve": User wants to improve/optimize an existing process
        - "analyze": User wants to analyze a process for bottlenecks or issues
        - "conversation": User is asking questions about an existing diagram, requesting modifications, or providing additional information
        
        Look for keywords like:
        - "conversation": "what is", "how does", "explain", "modify", "add", "change", "update", "question", "why", "when", "where"
        - "visualize": "create diagram", "generate BPMN", "draw", "visualize", "show me"
        - "improve": "improve", "optimize", "better", "faster", "cheaper", "enhance"
        - "analyze": "analyze", "bottleneck", "problem", "issue", "slow", "expensive"
        
        Return only the intent word (visualize, improve, analyze, or conversation).
        """
        
        try:
            intent = self.context_agent.llm_caller(intent_prompt, temperature=0.1, max_output_tokens=50).strip().lower()
            if intent in ['visualize', 'improve', 'analyze', 'conversation']:
                return intent
            else:
                # Default to conversation if unclear (safer default)
                return 'conversation'
        except Exception as e:
            logger.error(f"Error determining user intent: {e}")
            return 'conversation'

    def visualize_process_only(self, session_id: str, query: str, file_texts: Optional[str] = None, file_type: Optional[str] = None) -> Dict:
        """
        Direct visualization workflow - only generates BPMN diagram without process improvement.
        """
        session_data = self.sessions.get(session_id)
        if not session_data:
            logger.error(f"Session {session_id} not found during visualize_process_only.")
            return {"status": "error", "message": "Invalid session ID."}

        session_data["query"] = query
        session_data["original_file_texts"] = file_texts
        session_data["original_file_type"] = file_type
        session_data["status"] = "Processing Visualization"
        session_data["last_step_completed"] = None

        logger.info(f"[{session_id}] Processing visualization request: '{query[:50]}...'")

        try:
            # 1. Context Agent - extract process information
            logger.info(f"[{session_id}] Calling Context Agent for visualization...")
            process_desc = self.context_agent.process_query(query)
            session_data["process_desc"] = process_desc
            session_data["last_step_completed"] = "context_analysis"
            logger.info(f"[{session_id}] Context Agent processed. Process: {process_desc.name}")

            if not process_desc.name or not process_desc.steps:
                session_data["status"] = "Clarification Needed"
                session_data["data"] = {"clarification_message": "Could not understand the process to visualize. Please provide more details about the process steps."}
                logger.warning(f"[{session_id}] Context Agent needs clarification for visualization.")
                return {"status": "clarification_needed", "message": "More details needed to understand the process.", "session_id": session_id, "data": session_data["data"]}

            # 2. Visualization Agent - generate BPMN diagram
            logger.info(f"[{session_id}] Calling Visualization Agent...")
            viz_result = self.visualization_agent.generate_diagram(
                process_name=process_desc.name,
                process_steps=process_desc.steps,
                process_description=f"Goal: {process_desc.goal}. Inputs: {', '.join(process_desc.inputs)}. Outputs: {', '.join(process_desc.outputs)}",
                file_context=file_texts or ""
            )

            session_data["diagram_data"] = viz_result["diagram_data"]
            session_data["diagram_description"] = viz_result["diagram_description"]
            session_data["detail_descriptions"] = viz_result["detail_descriptions"]
            
            # Generate memory for visualization workflow
            visualization_memory = f"""
            Visualization Session Memory:
            - Process Name: {process_desc.name}
            - Process Steps: {len(process_desc.steps)} steps
            - Process Goal: {process_desc.goal or 'Not specified'}
            - Process Inputs: {', '.join(process_desc.inputs) if process_desc.inputs else 'None'}
            - Process Outputs: {', '.join(process_desc.outputs) if process_desc.outputs else 'None'}
            - Generated Diagram: {viz_result.get("diagram_name", "Process Diagram")}
            - Diagram Description: {viz_result.get("diagram_description", "Generated BPMN diagram")}
            - Number of Diagram Elements: {len(viz_result.get("detail_descriptions", {}))}
            - Visualization Timestamp: {__import__('datetime').datetime.now().isoformat()}
            """
            session_data["visualization_memory"] = visualization_memory.strip()
            
            session_data["last_step_completed"] = "visualization_complete"
            logger.info(f"[{session_id}] Visualization Agent generated diagram.")

            session_data["status"] = "completed"
            session_data["message"] = "Process visualization complete!"
            session_data["data"] = {
                "process_name": process_desc.name,
                "process_steps": process_desc.steps,
                "diagram_data": session_data["diagram_data"],
                "diagram_name": viz_result["diagram_name"],
                "diagram_description": session_data["diagram_description"],
                "detail_descriptions": session_data["detail_descriptions"],
                "memory": session_data["visualization_memory"]  # Return the memory
            }
            return {"status": "completed", "message": "Process visualization complete!", "session_id": session_id, "data": session_data["data"]}

        except Exception as e:
            session_data["status"] = "error"
            session_data["message"] = f"An error occurred during visualization: {e}"
            logger.exception(f"[{session_id}] Critical error during visualize_process_only.")
            return {"status": "error", "message": f"An error occurred: {e}", "session_id": session_id}

    def handle_conversation(self, session_id: str, query: str, diagram_data: str = "", memory: str = "") -> Dict:
        """
        Handle conversation workflow - answer questions about diagrams or modify them.
        """
        session_data = self.sessions.get(session_id)
        if not session_data:
            logger.error(f"Session {session_id} not found during handle_conversation.")
            return {"status": "error", "message": "Invalid session ID."}

        session_data["query"] = query
        session_data["status"] = "Processing Conversation"
        session_data["last_step_completed"] = None

        logger.info(f"[{session_id}] Processing conversation: '{query[:50]}...'")

        try:
            # Determine if this is a question or modification request
            conversation_type = self._determine_conversation_type(query)
            logger.info(f"[{session_id}] Conversation type: {conversation_type}")

            language = detect_language(query)

            if conversation_type == "question":
                # Handle question about diagram
                answer = self._answer_diagram_question(query, diagram_data, memory, session_data, language)
                session_data["conversation_memory"] = memory + f"\nQ: {query}\nA: {answer}"
                
                session_data["status"] = "completed"
                session_data["message"] = "Question answered successfully!"
                session_data["data"] = {
                    "action": "answer_question",
                    "diagram_data": diagram_data,  # Return original diagram
                    "detail_descriptions": {},  # Empty for questions
                    "answer": answer,
                    "memory": session_data["conversation_memory"]
                }
                return {"status": "completed", "message": "Question answered successfully!", "session_id": session_id, "data": session_data["data"]}

            elif conversation_type == "modification":
                # Handle diagram modification
                modified_diagram = self._modify_diagram(query, diagram_data, memory, session_data, language)
                modified_diagram_data = modified_diagram.get("diagram_data", diagram_data)
                detail_descriptions = modified_diagram.get("detail_descriptions", {})
                modification_summary = modified_diagram.get("summary", "Diagram modified")
                
                session_data["conversation_memory"] = memory + f"\nModification Request: {query}\nApplied: {modification_summary}"
                
                session_data["status"] = "completed"
                session_data["message"] = "Diagram modified successfully!"
                session_data["data"] = {
                    "action": "modify_diagram",
                    "diagram_data": modified_diagram_data,
                    "detail_descriptions": detail_descriptions,
                    "answer": modification_summary,
                    "memory": session_data["conversation_memory"]
                }
                return {"status": "completed", "message": "Diagram modified successfully!", "session_id": session_id, "data": session_data["data"]}

            else:
                # Handle information addition
                updated_memory = self._add_information(query, memory, session_data)
                session_data["conversation_memory"] = updated_memory
                
                session_data["status"] = "completed"
                session_data["message"] = "Information added to memory!"
                session_data["data"] = {
                    "action": "add_information",
                    "diagram_data": diagram_data,  # Return original diagram
                    "detail_descriptions": {},  # Empty for information addition
                    "answer": "Information has been added to the conversation memory for future reference.",
                    "memory": session_data["conversation_memory"]
                }
                return {"status": "completed", "message": "Information added to memory!", "session_id": session_id, "data": session_data["data"]}

        except Exception as e:
            session_data["status"] = "error"
            session_data["message"] = f"An error occurred during conversation: {e}"
            logger.exception(f"[{session_id}] Critical error during handle_conversation.")
            return {"status": "error", "message": f"An error occurred: {e}", "session_id": session_id}

    def handle_optimization(self, diagram_data: str, memory: str) -> Dict:
        """
        Optimizes a process diagram by analyzing it, generating solutions, and creating a new diagram.
        """
        try:
            logger.info("Starting optimization workflow...")
            language = detect_language(diagram_data + " " + memory)
            language_instruction = get_language_instruction(language)
            logger.info(f"Detected language: {language}")
            
            # 1. Use ContextAgent to understand the current process from the diagram
            logger.info("Step 1: Analyzing BPMN diagram with ContextAgent...")
            process_summary = self.context_agent.process_diagram(diagram_data, memory, language_instruction)
            logger.info(f"ContextAgent output: {process_summary[:200]}...")
            process_desc = ProcessDescription(name="Process from Diagram", goal="Optimize existing process", steps=[process_summary])

            # 2. Identify bottlenecks
            logger.info("Step 2: Identifying bottlenecks with BottleneckAnalysisAgent...")
            bottlenecks = self.bottleneck_agent.identify_bottlenecks(process_desc, diagram_data=diagram_data)
            logger.info(f"BottleneckAgent identified {len(bottlenecks)} bottlenecks")
            for i, bottleneck in enumerate(bottlenecks):
                logger.info(f" Bottleneck {i+1}: {bottleneck.location} - {bottleneck.reason_hypothesis}")

            # 3. Retrieve and verify information for process and bottlenecks
            logger.info("Step 3: Retrieving and verifying information with InformationRetrievalAgent...")
            info_queries = []
            for b in bottlenecks:
                if hasattr(b, 'info_needed') and b.info_needed:
                    info_queries.extend(b.info_needed)
            info_queries.insert(0, f"best practices for optimizing {process_desc.name}")
            logger.info(f"Information queries to process: {info_queries}")
            
            verified_info_list = []
            for i, query in enumerate(info_queries):
                logger.info(f"  Processing query {i+1}: {query}")
                info = self.ir_agent.retrieve_and_verify(query)
                logger.info(f"  Query {i+1} result - Confidence: {info.confidence}, Relevance: {info.relevance}")
                logger.info(f"  Query {i+1} summary: {info.summary[:100]}...")
                verified_info_list.append(info)

            # 4. Generate solutions
            logger.info("Step 4: Generating solutions with SolutionGenerationAgent...")
            improved_process = self.solution_agent.generate_solutions(process_desc, bottlenecks, verified_info_list, diagram_data=diagram_data)
            logger.info(f"SolutionAgent generated {len(improved_process.improvements)} improvements")
            logger.info(f"Improved process name: {improved_process.name}")
            logger.info(f"Summary of changes: {improved_process.summary_of_changes[:200]}...")
            # loger.info(f"Improve process: {improved_process}")
            # 5. Visualize the new process
            logger.info("Step 5: Generating visualization with VisualizationAgent...")
            viz_result = self.visualization_agent.generate_diagram(
                process_name=improved_process.name,
                process_steps=improved_process.improved_steps,
                process_description=improved_process.summary_of_changes,
                diagram_data=diagram_data
            )
            logger.info(f"VisualizationAgent generated diagram with {len(viz_result.get('detail_descriptions',[]))} elements")
            
            # 6. Format the response
            logger.info("Step 6: Formatting final response...")
            answer = improved_process.summary_of_changes
            
            optimization_detail = {
                (" ".join(imp.description.split()[:8]) + ("..." if len(imp.description.split()) > 8 else "")):
                    f"{imp.description} (Expected Impact: {imp.expected_impact})"
                for imp in improved_process.improvements
            }
            logger.info(f"Created {len(optimization_detail)} optimization details")

            updated_memory = memory + f"\n\n[Optimization Summary]\n" + answer
            logger.info("Optimization workflow completed successfully!")

            # Post-process detail_descriptions to use task/event names as keys if possible
            detail_descriptions = viz_result["detail_descriptions"]
            if detail_descriptions and isinstance(detail_descriptions, dict):
                # Try to map IDs to names using the BPMN XML
                id_to_name = self._extract_node_descriptions(viz_result["diagram_data"])
                # If mapping is successful and keys are IDs, replace them with names
                new_detail_descriptions = {}
                for k, v in detail_descriptions.items():
                    # If the key is an ID and exists in the mapping, use the name as key
                    if k in id_to_name:
                        new_detail_descriptions[id_to_name[k]] = v
                    else:
                        new_detail_descriptions[k] = v
                detail_descriptions = new_detail_descriptions

            return {
                "status": "completed",
                "message": "Process optimized successfully!",
                "data": {
                    "diagram_data": viz_result["diagram_data"],
                    "answer": answer,
                    "detail_descriptions": detail_descriptions,
                    "optimization_detail": optimization_detail,
                    "memory": updated_memory,
                },
            }

        except Exception as e:
            logger.exception("Error during optimization handling")
            return {"status": "error", "message": f"An error occurred during optimization: {str(e)}"}

    def _determine_conversation_type(self, query: str) -> str:
        """Determine if the conversation is a question, modification, or information addition."""
        type_prompt = f"""
        Analyze this query and determine the conversation type:
        
        Query: "{query}"
        
        Classify as:
        - "question": User is asking about the diagram (what, how, why, when, where, explain, describe)
        - "modification": User wants to change/modify the diagram (add, remove, change, modify, update, edit)
        - "information": User is providing additional information or context
        
        Return only: question, modification, or information
        """
        
        try:
            conv_type = self.context_agent.llm_caller(type_prompt, temperature=0.1, max_output_tokens=50).strip().lower()
            if conv_type in ['question', 'modification', 'information']:
                return conv_type
            else:
                return 'question'  # Default to question
        except Exception as e:
            logger.error(f"Error determining conversation type: {e}")
            return 'question'

    def _answer_diagram_question(self, query: str, diagram_data: str, memory: str, session_data: Dict, language: str) -> str:
        """Answer questions about the diagram."""
        context = f"""
        Diagram Data: {diagram_data}
        Conversation Memory: {memory}
        Current Session Data: {session_data.get('diagram_description', '')}
        """
        language_instruction = get_language_instruction(language)
        answer_prompt = f"""
        {language_instruction}
        Based on the following context, answer the user's question about the BPMN diagram.
        
        Context:
        {context}
        
        User Question: "{query}"
        
        Provide a clear, helpful answer about the diagram. If the question cannot be answered from the available information, say so politely.
        """
        
        try:
            answer = self.context_agent.llm_caller(answer_prompt, temperature=0.3, max_output_tokens=20000)
            return answer
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return "I'm sorry, I couldn't process your question at the moment. Please try again."

    def _modify_diagram(self, query: str, diagram_data: str, memory: str, session_data: Dict, language: str) -> Dict:
        context = f"""
        Original Diagram: {diagram_data}
        Conversation Memory: {memory}
        Current Session Data: {session_data.get('diagram_description', '')}
        """
        language_instruction = get_language_instruction(language)
        modification_prompt = f"""
        {language_instruction}
        Based on the following context, modify the BPMN diagram according to the user's request.
        
        Context:
        {context}
        
        User Modification Request: "{query}"
        
        Generate a modified BPMN 2.0 XML diagram that incorporates the requested changes.
        Also extract the node descriptions from the modified diagram.
        
        In the summary, concisely and naturally describe the changes in the same language as the user's request. Do not use generic phrases like 'Changes made:' or 'Diagram has been modified.'
        
        Return ONLY the following JSON object. Do not include any explanation, language instruction, or text outside the JSON. Do not repeat the language instruction in your output. Do not return anything except the JSON object.
        {{
            "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
            "detail_descriptions": {{
                "StartEvent_1": "Process starts",
                "Task_1": "Description of the first task",
                "Task_2": "Description of the second task",
                "EndEvent_1": "Process ends"
            }},
            "summary": "Detailed description of what was modified (e.g., 'Added a new quality check task after Task_2, renamed Task_1 to 'Order Processing')"
        }}
        
        Ensure the BPMN XML is valid and follows BPMN 2.0 standards.
        The summary should clearly explain what changes were made to the diagram.
        """
        try:
            response = self.visualization_agent.llm_caller(modification_prompt, temperature=0.0, max_output_tokens=20000)
            logger.info(f"Raw LLM output for modification: {response}")
            # Try to extract JSON block
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            json_str = json_match.group() if json_match else response
            # Auto-fix common JSON issues
            def fix_json(s):
                s = s.strip()
                # Replace single quotes with double quotes
                s = re.sub(r"'", '"', s)
                # Remove trailing commas before closing braces/brackets
                s = re.sub(r',([ \t\r\n]*[}\]])', r'\1', s)
                # Remove any leading/trailing text outside the outermost braces
                first = s.find('{')
                last = s.rfind('}')
                if first != -1 and last != -1:
                    s = s[first:last+1]
                return s
            try:
                result = json.loads(json_str)
            except Exception:
                try:
                    fixed = fix_json(json_str)
                    result = json.loads(fixed)
                except Exception:
                    # User-friendly error in user's language
                    fallback_summary = (
                        "Xin lỗi, tôi không thể xử lý yêu cầu của bạn. Vui lòng thử lại." if language == "vi" else
                        "Sorry, I could not process your request. Please try again."
                    )
                    return {
                        "diagram_data": diagram_data,
                        "detail_descriptions": {},
                        "summary": fallback_summary
                    }
            return {
                "diagram_data": result.get("diagram_data", diagram_data),
                "detail_descriptions": result.get("detail_descriptions", {}),
                "summary": result.get("summary", (
                    "Xin lỗi, tôi không thể xử lý yêu cầu của bạn. Vui lòng thử lại." if language == "vi" else
                    "Sorry, I could not process your request. Please try again."
                ))
            }
        except Exception as e:
            logger.error(f"Error modifying diagram: {e}")
            return {
                "diagram_data": diagram_data,
                "detail_descriptions": {},
                "summary": (
                    "Xin lỗi, tôi không thể xử lý yêu cầu của bạn. Vui lòng thử lại." if language == "vi" else
                    "Sorry, I could not process your request. Please try again."
                )
            }

    def _add_information(self, query: str, memory: str, session_data: Dict) -> str:
        """Add information to the conversation memory."""
        # Simply append the new information to existing memory
        if memory:
            updated_memory = memory + f"\nAdditional Information: {query}"
        else:
            updated_memory = f"Additional Information: {query}"
        
        return updated_memory

    def _extract_node_descriptions(self, diagram_data: str) -> Dict[str, str]:
        """Extract node descriptions from BPMN XML."""
        descriptions = {}
        try:
            # Remove default namespace for easier parsing
            diagram_data = diagram_data.replace('xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"', '')
            root = ET.fromstring(diagram_data)
            
            # Find all elements with an 'id' and 'name' attribute
            for element in root.findall(".//*[@id][@name]"):
                descriptions[element.attrib['id']] = element.attrib['name']
                
        except ET.ParseError as e:
            logger.error(f"Error parsing BPMN XML: {e}")
            return {"error": "Invalid BPMN XML provided."}
        except Exception as e:
            logger.error(f"An unexpected error occurred during node description extraction: {e}")
            return {"error": "Could not extract node descriptions."}
            
        return descriptions

    def process_user_query(self, session_id: str, query: str, file_texts: Optional[str] = None, file_type: Optional[str] = None, diagram_data: str = "", memory: str = "") -> Dict:
        """
        Main entry point that determines user intent and routes to appropriate workflow.
        """
        # Determine user intent
        intent = self.determine_user_intent(query)
        logger.info(f"[{session_id}] Determined user intent: {intent}")

        if intent == "visualize":
            # Direct visualization workflow
            return self.visualize_process_only(session_id, query, file_texts, file_type)
        elif intent == "conversation":
            # Conversation workflow
            return self.handle_conversation(session_id, query, diagram_data, memory)
        else:
            # Full process improvement workflow (existing logic)
            return self._process_improvement_workflow(session_id, query, file_texts, file_type)

    def _process_improvement_workflow(self, session_id: str, query: str, file_texts: Optional[str] = None, file_type: Optional[str] = None) -> Dict:
        """
        Full process improvement workflow (existing logic).
        """
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

            # 4. Visualization Agent - generate BPMN for improved process
            logger.info(f"[{session_id}] Calling Visualization Agent for improved process...")
            viz_result = self.visualization_agent.generate_diagram(
                process_name=improved_process.name,
                process_steps=improved_process.improved_steps,
                process_description=f"Improved process based on: {improved_process.summary_of_changes}",
                file_context=file_texts or ""
            )

            session_data["diagram_data"] = viz_result["diagram_data"]
            session_data["diagram_description"] = viz_result["diagram_description"]
            session_data["detail_descriptions"] = viz_result["detail_descriptions"]
            
            # Generate comprehensive memory for process improvement workflow
            improvement_memory = f"""
            Process Improvement Session Memory:
            - Original Process: {process_desc.name}
            - Original Steps: {len(process_desc.steps)} steps
            - Bottlenecks Identified: {len(session_data["bottlenecks"])}
            - Verified Information Sources: {len(session_data["verified_info"])}
            - Improvements Generated: {len(improved_process.improvements)}
            - Improved Process: {improved_process.name}
            - Improved Steps: {len(improved_process.improved_steps)} steps
            - Summary of Changes: {improved_process.summary_of_changes}
            - Generated Diagram: {viz_result.get("diagram_name", "Improved Process Diagram")}
            - Analysis Timestamp: {__import__('datetime').datetime.now().isoformat()}
            """
            session_data["visualization_memory"] = improvement_memory.strip()
            
            session_data["last_step_completed"] = "visualization_complete"
            logger.info(f"[{session_id}] Visualization Agent generated improved process diagram.")

            session_data["status"] = "completed"
            session_data["message"] = "Process analysis and improvement complete!"
            session_data["data"] = {
                "improved_process_summary": improved_process.summary_of_changes,
                "improved_process_steps": improved_process.improved_steps,
                "diagram_data": session_data["diagram_data"],
                "diagram_name": viz_result["diagram_name"],
                "diagram_description": session_data["diagram_description"],
                "detail_descriptions": session_data["detail_descriptions"],
                "memory": session_data["visualization_memory"]  # Return the memory
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