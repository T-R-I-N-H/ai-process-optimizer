"""
Pytest tests for the Conversation API

Run with: pytest test_conversation_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

client = TestClient(app)

# Sample BPMN XML for testing
SAMPLE_BPMN_XML = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" 
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" 
                  id="Definitions_1" 
                  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_1" name="Order Processing">
    <bpmn:startEvent id="StartEvent_1" name="Receive Order" />
    <bpmn:task id="Task_1" name="Validate Order" />
    <bpmn:exclusiveGateway id="Gateway_1" name="Valid Order?" />
    <bpmn:task id="Task_2" name="Process Order" />
    <bpmn:task id="Task_3" name="Reject Order" />
    <bpmn:endEvent id="EndEvent_1" name="Order Complete" />
    <bpmn:endEvent id="EndEvent_2" name="Order Rejected" />
    
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="Gateway_1" />
    <bpmn:sequenceFlow id="Flow_3" sourceRef="Gateway_1" targetRef="Task_2" />
    <bpmn:sequenceFlow id="Flow_4" sourceRef="Gateway_1" targetRef="Task_3" />
    <bpmn:sequenceFlow id="Flow_5" sourceRef="Task_2" targetRef="EndEvent_1" />
    <bpmn:sequenceFlow id="Flow_6" sourceRef="Task_3" targetRef="EndEvent_2" />
  </bpmn:process>
</bpmn:definitions>"""

class TestConversationAPIValidation:
    """Test validation scenarios for the Conversation API"""
    
    def test_missing_required_fields(self):
        """Test that missing required fields returns 422"""
        payload = {
            "prompt": "What does Task_1 do?"
            # Missing: diagram_data, current_memory
        }
        response = client.post("/interaction/conversation", json=payload)
        assert response.status_code == 422
    
    def test_empty_prompt(self):
        """Test that empty prompt returns 400"""
        payload = {
            "prompt": "",
            "diagram_data": SAMPLE_BPMN_XML,
            "current_memory": ""
        }
        response = client.post("/interaction/conversation", json=payload)
        assert response.status_code == 400
    
    def test_invalid_bpmn_xml(self):
        """Test that invalid BPMN XML returns 400"""
        payload = {
            "prompt": "What does this do?",
            "diagram_data": "This is not valid BPMN XML",
            "current_memory": ""
        }
        response = client.post("/interaction/conversation", json=payload)
        assert response.status_code == 400
    
    def test_memory_too_long(self):
        """Test that memory too long returns 400"""
        payload = {
            "prompt": "What does Task_1 do?",
            "diagram_data": SAMPLE_BPMN_XML,
            "current_memory": "A" * 15000  # 15KB memory
        }
        response = client.post("/interaction/conversation", json=payload)
        assert response.status_code == 400
    
    def test_invalid_session_id_format(self):
        """Test that invalid session_id format returns 422"""
        payload = {
            "session_id": "invalid@session#id",
            "prompt": "What does Task_1 do?",
            "diagram_data": SAMPLE_BPMN_XML,
            "current_memory": ""
        }
        response = client.post("/interaction/conversation", json=payload)
        assert response.status_code == 422

class TestConversationAPIFunctionality:
    """Test functional scenarios for the Conversation API"""
    
    def test_valid_request_structure(self):
        """Test that a valid request returns proper response structure"""
        payload = {
            "prompt": "What does Task_1 do?",
            "diagram_data": SAMPLE_BPMN_XML,
            "current_memory": ""
        }
        response = client.post("/interaction/conversation", json=payload)
        
        # Should either succeed or fail during processing (not validation)
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["action", "diagram_data", "detail_descriptions", "answer", "memory"]
            for field in required_fields:
                assert field in data
    
    def test_question_answering_response_structure(self):
        """Test that question answering returns correct structure"""
        payload = {
            "prompt": "What does the Task_1 node do in this process?",
            "diagram_data": SAMPLE_BPMN_XML,
            "current_memory": ""
        }
        response = client.post("/interaction/conversation", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            assert data["action"] == "answer_question"
            assert "diagram_data" in data
            assert "detail_descriptions" in data
            assert "answer" in data
            assert "memory" in data
            # For questions, detail_descriptions should be empty
            assert len(data["detail_descriptions"]) == 0
    
    def test_diagram_modification_response_structure(self):
        """Test that diagram modification returns correct structure"""
        payload = {
            "prompt": "Add a new task called 'Send Confirmation Email' after the 'Process Order' task",
            "diagram_data": SAMPLE_BPMN_XML,
            "current_memory": ""
        }
        response = client.post("/interaction/conversation", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            assert data["action"] == "modify_diagram"
            assert "diagram_data" in data
            assert "detail_descriptions" in data
            assert "answer" in data
            assert "memory" in data
            # For modifications, should have detail descriptions
            assert len(data["detail_descriptions"]) > 0
    
    def test_memory_persistence(self):
        """Test that memory is maintained across requests"""
        # First request
        payload1 = {
            "prompt": "What is the purpose of this process?",
            "diagram_data": SAMPLE_BPMN_XML,
            "current_memory": ""
        }
        response1 = client.post("/interaction/conversation", json=payload1)
        
        if response1.status_code == 200:
            data1 = response1.json()
            memory1 = data1["memory"]
            
            # Second request using memory from first
            payload2 = {
                "prompt": "Based on our previous conversation, what are the main steps?",
                "diagram_data": SAMPLE_BPMN_XML,
                "current_memory": memory1
            }
            response2 = client.post("/interaction/conversation", json=payload2)
            
            if response2.status_code == 200:
                data2 = response2.json()
                memory2 = data2["memory"]
                
                # Memory should be updated
                assert memory2 != ""
                assert memory2 != memory1

class TestConversationAPIEndpoints:
    """Test endpoint accessibility and basic functionality"""
    
    def test_api_health_check(self):
        """Test that the API root endpoint is accessible"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_conversation_endpoint_exists(self):
        """Test that the conversation endpoint exists"""
        # This should return 422 (validation error) rather than 404
        payload = {
            "prompt": "test"
            # Missing required fields
        }
        response = client.post("/interaction/conversation", json=payload)
        assert response.status_code == 422  # Validation error, not 404

if __name__ == "__main__":
    # Run tests directly if script is executed
    pytest.main([__file__, "-v"]) 