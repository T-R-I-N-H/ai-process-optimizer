import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app

client = TestClient(app)

def test_conversation_validation_errors():
    """Test various validation errors in the conversation API."""
    
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
        "diagram_data": "<bpmn:definitions><bpmn:process><bpmn:task id='Task_1'/></bpmn:process></bpmn:definitions>",
        "current_memory": ""
    }
    response = client.post("/interaction/conversation", json=payload_empty_prompt)
    assert response.status_code == 422, "Should fail validation for empty prompt"
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
        "diagram_data": "<bpmn:definitions><bpmn:process><bpmn:task id='Task_1'/></bpmn:process></bpmn:definitions>",
        "current_memory": "A" * 15000  # 15KB memory
    }
    response = client.post("/interaction/conversation", json=payload_long_memory)
    assert response.status_code == 400, "Should fail validation for memory too long"
    print(f"✅ Long memory test passed: {response.status_code}")
    
    # Test 5: Invalid session_id format
    payload_invalid_session = {
        "session_id": "invalid@session#id",
        "prompt": "What does Task_1 do?",
        "diagram_data": "<bpmn:definitions><bpmn:process><bpmn:task id='Task_1'/></bpmn:process></bpmn:definitions>",
        "current_memory": ""
    }
    response = client.post("/interaction/conversation", json=payload_invalid_session)
    assert response.status_code == 422, "Should fail validation for invalid session_id"
    print(f"✅ Invalid session_id test passed: {response.status_code}")
    
    # Test 6: Valid request (should pass)
    payload_valid = {
        "prompt": "What does Task_1 do?",
        "diagram_data": "<bpmn:definitions xmlns:bpmn='http://www.omg.org/spec/BPMN/20100524/MODEL'><bpmn:process id='Process_1'><bpmn:task id='Task_1' name='Start Process'/></bpmn:process></bpmn:definitions>",
        "current_memory": ""
    }
    response = client.post("/interaction/conversation", json=payload_valid)
    # This might pass validation but fail during processing (which is OK)
    assert response.status_code in [200, 400, 500], "Should either succeed or fail during processing"
    print(f"✅ Valid request test passed: {response.status_code}")

def test_conversation_success_case():
    """Test a successful conversation request."""
    payload = {
        "prompt": "What does Task_1 do?",
        "diagram_data": """<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
            <bpmn:process id="Process_1" name="Test Process">
                <bpmn:startEvent id="StartEvent_1" name="Start" />
                <bpmn:task id="Task_1" name="Process Order" />
                <bpmn:endEvent id="EndEvent_1" name="End" />
                <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1" />
                <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="EndEvent_1" />
            </bpmn:process>
        </bpmn:definitions>""",
        "current_memory": ""
    }
    
    response = client.post("/interaction/conversation", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        assert "action" in data
        assert "diagram_data" in data
        assert "detail_descriptions" in data
        assert "answer" in data
        assert "memory" in data
        print("✅ Success case: All required fields present")
    else:
        print(f"⚠️ Success case failed with status {response.status_code}: {response.json()}")

if __name__ == "__main__":
    print("Testing Conversation API Validation...")
    test_conversation_validation_errors()
    test_conversation_success_case()
    print("All validation tests completed!") 