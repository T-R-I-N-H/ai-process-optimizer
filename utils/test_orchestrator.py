import unittest
from unittest.mock import MagicMock, patch
from core.orchestrator import WorkflowOrchestrator
from core.models import ProcessDescription, ImprovedProcess
from services.visualize_api_client import VisualizeApiClient # Import the actual client for mocking

class TestWorkflowOrchestrator(unittest.TestCase):

    @patch('agents.context_agent.ContextAgent.process_query')
    @patch('agents.bottleneck_agent.BottleneckAnalysisAgent.identify_bottlenecks')
    @patch('agents.information_retrieval_agent.InformationRetrievalAgent.retrieve_and_verify')
    @patch('agents.solution_generation_agent.SolutionGenerationAgent.generate_solutions')
    @patch('services.visualize_api_client.VisualizeApiClient.visualize')
    def test_full_workflow_success(self, mock_visualize, mock_generate_solutions,
                                   mock_retrieve_and_verify, mock_identify_bottlenecks,
                                   mock_process_query):
        # Mock agent behaviors
        mock_process_query.return_value = ProcessDescription(
            name="Test Process", steps=["Start", "Do A", "End"], goal="Improve speed"
        )
        mock_identify_bottlenecks.return_value = [
            MagicMock(location="Do A", reason_hypothesis="Slow manual step", info_needed=["How to automate A"])
        ]
        mock_retrieve_and_verify.return_value = MagicMock(
            summary="Automation tools available.", confidence="High", query="How to automate A", sources=[], relevance="Direct"
        )
        mock_generate_solutions.return_value = ImprovedProcess(
            name="Improved Test Process",
            original_process=ProcessDescription(name="Test Process", steps=["Start", "Do A", "End"]),
            improvements=[MagicMock()],
            improved_steps=["Start", "Automated A", "End"],
            summary_of_changes="Automated step A."
        )
        mock_visualize.return_value = {
            "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
            "Diagram_description": "A diagram of the improved process.",
            "detail_descriptions": [{"node_id": "1", "node_description": "Start"}],
            "Memory": "Visualization context memory."
        }

        orchestrator = WorkflowOrchestrator()
        user_id = "test_user"
        query = "Analyze my test process."

        session_id = orchestrator.start_new_session(user_id)
        result = orchestrator.process_user_query(session_id, query)

        self.assertEqual(result["status"], "completed")
        self.assertIn("diagram_data", result["data"])
        self.assertIn("<bpmn:definitions>", result["data"]["diagram_data"])

        # Verify agent calls
        mock_process_query.assert_called_once()
        mock_identify_bottlenecks.assert_called_once()
        mock_retrieve_and_verify.assert_called_once()
        mock_generate_solutions.assert_called_once()
        mock_visualize.assert_called_once()

        # Verify visualization_memory is stored
        session_data = orchestrator.get_session_status(session_id)
        # Note: 'visualization_memory' is internal to orchestrator's session_data,
        # not directly returned by get_session_status by default.
        # If you want to assert its content, you'd access orchestrator.sessions[session_id]['visualization_memory']
        self.assertEqual(orchestrator.sessions[session_id]['visualization_memory'], "Visualization context memory.")


    def test_clarification_needed_context(self):
        self.mock_llm_caller_context = MagicMock()
        self.mock_llm_caller_context.return_value = '{"name": "", "steps": [], "pain_points": [], "metrics": {}, "goal": ""}'
        
        # Patch individual agent methods used by orchestrator
        with patch('agents.context_agent.ContextAgent.process_query', return_value=ProcessDescription(name="", steps=[], goal="")) as mock_context_agent_query:
            orchestrator = WorkflowOrchestrator()
            user_id = "test_user_clarify"
            query = "I have a process, please optimize."

            session_id = orchestrator.start_new_session(user_id)
            result = orchestrator.process_user_query(session_id, query)

            self.assertEqual(result["status"], "clarification_needed")
            self.assertIn("Could not fully understand the process", result["message"])
            mock_context_agent_query.assert_called_once()

    @patch('agents.context_agent.ContextAgent.process_query')
    @patch('agents.bottleneck_agent.BottleneckAnalysisAgent.identify_bottlenecks')
    @patch('agents.information_retrieval_agent.InformationRetrievalAgent.retrieve_and_verify')
    @patch('agents.solution_generation_agent.SolutionGenerationAgent.generate_solutions')
    @patch('services.visualize_api_client.VisualizeApiClient.visualize')
    def test_resume_with_clarification(self, mock_visualize, mock_generate_solutions,
                                       mock_retrieve_and_verify, mock_identify_bottlenecks,
                                       mock_process_query):
        # First call, agent needs clarification
        mock_process_query.side_effect = [
            ProcessDescription(name="", steps=[], goal=""), # First call for clarification
            ProcessDescription(name="Revised Process", steps=["Step 1", "Step 2"], goal="Improved speed") # Second call after clarification
        ]
        mock_identify_bottlenecks.return_value = [
            MagicMock(location="Step 1", reason_hypothesis="Problem", info_needed=[])
        ]
        mock_retrieve_and_verify.return_value = MagicMock(summary="Info", confidence="High", query="", sources=[], relevance="Direct")
        mock_generate_solutions.return_value = ImprovedProcess(
            name="Improved Revised Process", original_process=MagicMock(), improvements=[], improved_steps=["New Step 1"], summary_of_changes=""
        )
        mock_visualize.return_value = {
            "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
            "Diagram_description": "", "detail_descriptions": [], "Memory": ""
        }

        orchestrator = WorkflowOrchestrator()
        user_id = "test_user_resume"
        query_initial = "Optimize my process."

        session_id = orchestrator.start_new_session(user_id)
        result_initial = orchestrator.process_user_query(session_id, query_initial)

        self.assertEqual(result_initial["status"], "clarification_needed")
        mock_process_query.assert_called_once() # Called once for initial query

        # Now, provide clarification and resume
        clarification = "The process involves: Step 1, Step 2. Goal is to be faster."
        result_resume = orchestrator.resume_session_with_clarification(session_id, clarification)

        self.assertEqual(result_resume["status"], "completed")
        self.assertIn("diagram_data", result_resume["data"])
        self.assertEqual(mock_process_query.call_count, 2) # Called again after resume

if __name__ == '__main__':
    unittest.main()