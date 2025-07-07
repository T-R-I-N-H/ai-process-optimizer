import unittest
from unittest.mock import MagicMock, patch
from agents.context_agent import ContextAgent
from agents.bottleneck_agent import BottleneckAnalysisAgent
from agents.information_retrieval_agent import InformationRetrievalAgent
from agents.solution_generation_agent import SolutionGenerationAgent
from core.models import ProcessDescription, BottleneckHypothesis, VerifiedInformation, ImprovedProcess, ProposedImprovement

class TestAgents(unittest.TestCase):

    def setUp(self):
        # Mock the LLM caller for predictable results
        self.mock_llm_caller = MagicMock()

    def test_context_agent_success(self):
        self.mock_llm_caller.return_value = '{"name": "Order Process", "steps": ["Receive order", "Process payment", "Ship product"], "inputs": ["Customer Order"], "outputs": ["Shipped Product"], "pain_points": [], "metrics": {}, "goal": "Automate order fulfillment"}'
        agent = ContextAgent(self.mock_llm_caller)
        query = "Automate our order processing workflow."
        result = agent.process_query(query)

        self.assertIsInstance(result, ProcessDescription)
        self.assertEqual(result.name, "Order Process")
        self.assertIn("Receive order", result.steps)
        self.mock_llm_caller.assert_called_once()

    def test_bottleneck_agent_success(self):
        self.mock_llm_caller.return_value = '''
        [
            {
                "location": "Process payment",
                "reason_hypothesis": "Manual verification causing delays.",
                "info_needed": ["Average payment processing time", "Fraud detection tools"]
            }
        ]
        '''
        agent = BottleneckAnalysisAgent(self.mock_llm_caller)
        process_desc = ProcessDescription(name="Order Process", steps=["Receive order", "Process payment", "Ship product"], goal="Speed up")
        result = agent.identify_bottlenecks(process_desc)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIsInstance(result[0], BottleneckHypothesis)
        self.assertEqual(result[0].location, "Process payment")
        self.mock_llm_caller.assert_called_once()

    def test_information_retrieval_agent_simulated(self):
        # This agent is mocked internally, so no LLM call mock needed
        agent = InformationRetrievalAgent(self.mock_llm_caller) # LLM caller is not used by current IRVA logic
        query = "best practices for reducing wait times in customer support"
        result = agent.retrieve_and_verify(query)

        self.assertIsInstance(result, VerifiedInformation)
        self.assertEqual(result.query, query)
        self.assertEqual(result.confidence, "High")
        self.assertIn("chatbots", result.summary)

    def test_solution_generation_agent_success(self):
        self.mock_llm_caller.return_value = '''
        {
            "name": "Improved Order Process",
            "original_process": {"name": "Order Process", "steps": ["Receive order", "Process payment", "Ship product"], "inputs": [], "outputs": [], "pain_points": [], "metrics": {}, "goal": ""},
            "improvements": [
                {
                    "step_number": 1,
                    "description": "Implement automated payment gateway.",
                    "expected_impact": "Reduce payment processing time by 80%.",
                    "tools_or_tech": ["Stripe API"],
                    "actors_involved": ["IT", "Finance"]
                }
            ],
            "improved_steps": ["Receive order", "Automated payment processing", "Ship product"],
            "summary_of_changes": "Automated payment processing to speed up workflow."
        }
        '''
        agent = SolutionGenerationAgent(self.mock_llm_caller)
        process_desc = ProcessDescription(name="Order Process", steps=["Receive order", "Process payment", "Ship product"], goal="Speed up")
        bottlenecks = [BottleneckHypothesis(location="Process payment", reason_hypothesis="Manual", info_needed=[])]
        verified_info = [VerifiedInformation(query="automated payments", sources=[], summary="Automated payments are fast", confidence="High", relevance="Direct")]

        result = agent.generate_solutions(process_desc, bottlenecks, verified_info)

        self.assertIsInstance(result, ImprovedProcess)
        self.assertEqual(result.name, "Improved Order Process")
        self.assertGreater(len(result.improvements), 0)
        self.assertIn("Automated payment processing", result.improved_steps)
        self.mock_llm_caller.assert_called_once()

if __name__ == '__main__':
    unittest.main()