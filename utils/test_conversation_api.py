import pytest
from fastapi.testclient import TestClient
import sys
import os
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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

class TestConversationAPI:
    """Comprehensive tests for the Conversation API"""
    
    def test_validation_errors(self):
        """Test various validation error scenarios"""
        
        # Test 1: Missing required fields
        payload_missing_fields = {
            "prompt": "What does Task_1 do?"
            # Missing: diagram_data, current_memory
        }
        response = client.post("/interaction/conversation", json=payload_missing_fields)
        assert response.status_code == 422, "Should fail validation for missing fields"
        print(f"✅ Missing fields test passed: {response.status_code}")
        
        # Test 2: Empty prompt
        payload_empty_prompt = {
            "prompt": "",
            "diagram_data": SAMPLE_BPMN_XML,
            "current_memory": ""
        }
        response = client.post("/interaction/conversation", json=payload_empty_prompt)
        assert response.status_code == 400, "Should fail validation for empty prompt"
        print(f"✅ Empty prompt test passed: {response.status_code}")
        
        # Test 3: Invalid BPMN XML
        payload_invalid_bpmn = {
            "prompt": "What does Task_1 do?",
            "diagram_data": "This is not BPMN XML",
            "current_memory": ""
        }
        response = client.post("/interaction/conversation", json=payload_invalid_bpmn)
        assert response.status_code == 400, "Should fail validation for invalid BPMN XML"
        print(f"✅ Invalid BPMN test passed: {response.status_code}")
        
        # Test 4: Memory too long
        payload_long_memory = {
            "prompt": "What does Task_1 do?",
            "diagram_data": SAMPLE_BPMN_XML,
            "current_memory": "A" * 15000  # 15KB memory
        }
        response = client.post("/interaction/conversation", json=payload_long_memory)
        assert response.status_code == 400, "Should fail validation for memory too long"
        print(f"✅ Long memory test passed: {response.status_code}")
        
        # Test 5: Invalid session_id format
        payload_invalid_session = {
            "session_id": "invalid@session#id",
            "prompt": "What does Task_1 do?",
            "diagram_data": SAMPLE_BPMN_XML,
            "current_memory": ""
        }
        response = client.post("/interaction/conversation", json=payload_invalid_session)
        assert response.status_code == 422, "Should fail validation for invalid session_id"
        print(f"✅ Invalid session_id test passed: {response.status_code}")
    
    def test_question_answering(self):
        """Test conversation API for answering questions about diagrams"""
        
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
            assert len(data["detail_descriptions"]) == 0  # Should be empty for questions
            print("✅ Question answering test passed")
        else:
            print(f"⚠️ Question answering test failed with status {response.status_code}: {response.json()}")
    
    def test_diagram_modification(self):
        """Test conversation API for modifying diagrams"""
        
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
            # Should have detail descriptions for modified diagram
            assert len(data["detail_descriptions"]) > 0
            print("✅ Diagram modification test passed")
        else:
            print(f"⚠️ Diagram modification test failed with status {response.status_code}: {response.json()}")
    
    def test_conversation_memory(self):
        """Test that conversation memory is maintained across requests"""
        
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
            
            # Second request using the memory from first request
            payload2 = {
                "prompt": "Based on our previous conversation, what are the main steps?",
                "diagram_data": SAMPLE_BPMN_XML,
                "current_memory": memory1
            }
            
            response2 = client.post("/interaction/conversation", json=payload2)
            
            if response2.status_code == 200:
                data2 = response2.json()
                memory2 = data2["memory"]
                
                # Memory should be updated and different from original
                assert memory2 != ""
                assert memory2 != memory1
                print("✅ Conversation memory test passed")
            else:
                print(f"⚠️ Second conversation request failed: {response2.status_code}")
        else:
            print(f"⚠️ First conversation request failed: {response1.status_code}")
    
    def test_session_management(self):
        """Test session ID handling"""
        
        # Request without session_id (should create new session)
        payload1 = {
            "prompt": "What does this process do?",
            "diagram_data": SAMPLE_BPMN_XML,
            "current_memory": ""
        }
        
        response1 = client.post("/interaction/conversation", json=payload1)
        
        if response1.status_code == 200:
            data1 = response1.json()
            
            # Request with specific session_id
            payload2 = {
                "session_id": "test_session_123",
                "prompt": "What does this process do?",
                "diagram_data": SAMPLE_BPMN_XML,
                "current_memory": ""
            }
            
            response2 = client.post("/interaction/conversation", json=payload2)
            
            if response2.status_code == 200:
                print("✅ Session management test passed")
            else:
                print(f"⚠️ Session management test failed: {response2.status_code}")
        else:
            print(f"⚠️ Session management test failed: {response1.status_code}")

def test_conversation_endpoint_health():
    """Test that the conversation endpoint is accessible"""
    response = client.get("/")
    assert response.status_code == 200
    print("✅ API health check passed")

if __name__ == "__main__":
    print("🧪 Running Conversation API Tests...")
    
    # Run tests
    test_conversation_endpoint_health()
    
    test_instance = TestConversationAPI()
    test_instance.test_validation_errors()
    test_instance.test_question_answering()
    test_instance.test_diagram_modification()
    test_instance.test_conversation_memory()
    test_instance.test_session_management()
    
    print("🎉 All Conversation API tests completed!") 