import unittest
import requests_mock
from services.visualize_api_client import VisualizeApiClient
from services.conversation_api_client import ConversationApiClient
from services.benchmark_api_client import BenchmarkApiClient
import os

# Set dummy environment variables for testing clients
os.environ["VISUALIZE_API_ENDPOINT"] = "http://mock-visualize.com/visualize"
os.environ["CONVERSATION_API_ENDPOINT"] = "http://mock-conversation.com/conversation"
os.environ["BENCHMARK_API_ENDPOINT"] = "http://mock-benchmark.com/benchmark"

class TestApiClients(unittest.TestCase):

    def test_visualize_api_client_success(self):
        client = VisualizeApiClient()
        with requests_mock.Mocker() as m:
            m.post(client.api_endpoint, json={
                "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
                "Diagram_description": "A test diagram.",
                "detail_descriptions": [],
                "Memory": "Viz memory"
            }, status_code=200)

            response = client.visualize("test prompt", "test file text")
            self.assertIn("diagram_data", response)
            self.assertEqual(response["Memory"], "Viz memory")

    def test_visualize_api_client_failure(self):
        client = VisualizeApiClient()
        with requests_mock.Mocker() as m:
            m.post(client.api_endpoint, status_code=500)
            with self.assertRaises(ConnectionError): # Or whatever specific error your client raises
                client.visualize("test prompt", "test file text")

    def test_conversation_api_client_success(self):
        client = ConversationApiClient()
        with requests_mock.Mocker() as m:
            m.post(client.api_endpoint, json={
                "Action": "answer_question",
                "Data": "<diagram>",
                "Answer": "Hello!",
                "Memory": "New memory"
            }, status_code=200)

            response = client.interact("prompt", "<diag>", "old mem")
            self.assertEqual(response["action"], "answer_question")
            self.assertEqual(response["answer"], "Hello!")
            self.assertEqual(response["memory"], "New memory")

    def test_benchmark_api_client_success(self):
        client = BenchmarkApiClient()
        with requests_mock.Mocker() as m:
            m.post(client.api_endpoint, json={
                "Benchmark_data": {"factor1": "desc1", "factor2": "desc2"}
            }, status_code=200)

            response = client.benchmark("<diag>", "memory string")
            self.assertIn("Benchmark_data", response)
            self.assertEqual(response["Benchmark_data"], {"factor1": "desc1", "factor2": "desc2"})

if __name__ == '__main__':
    unittest.main()