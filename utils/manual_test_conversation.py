#!/usr/bin/env python3
"""
Manual Testing Script for Conversation API

This script provides interactive testing capabilities for the Conversation API.
It includes sample data and curl commands for testing various scenarios.
"""

import json
import requests
import time
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# API Configuration
API_BASE_URL = "http://localhost:8000"
CONVERSATION_ENDPOINT = f"{API_BASE_URL}/interaction/conversation"

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

def print_curl_command(endpoint, payload, description):
    """Print a curl command for manual testing"""
    print(f"\n🔧 {description}")
    print("=" * 60)
    print(f"curl -X POST {endpoint} \\")
    print("  -H 'Content-Type: application/json' \\")
    print(f"  -d '{json.dumps(payload, indent=2)}'")
    print("=" * 60)

def test_api_with_requests(payload, description):
    """Test the API using the requests library"""
    print(f"\n🧪 Testing: {description}")
    print("-" * 40)
    
    try:
        response = requests.post(
            CONVERSATION_ENDPOINT,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"Action: {data.get('action', 'N/A')}")
            print(f"Answer: {data.get('answer', 'N/A')[:100]}...")
            print(f"Memory Length: {len(data.get('memory', ''))}")
            print(f"Detail Descriptions: {len(data.get('detail_descriptions', {}))} items")
            return data
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def interactive_test():
    """Interactive testing mode"""
    print("\n🎯 Interactive Testing Mode")
    print("Enter 'quit' to exit, 'help' for commands")
    
    memory = ""
    session_id = None
    
    while True:
        print(f"\nCurrent Memory Length: {len(memory)}")
        print(f"Session ID: {session_id or 'Auto-generated'}")
        
        user_input = input("\nEnter your prompt (or command): ").strip()
        
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'help':
            print_help()
            continue
        elif user_input.lower() == 'clear':
            memory = ""
            session_id = None
            print("✅ Memory and session cleared")
            continue
        elif user_input.lower() == 'sample':
            user_input = "What does the Task_1 node do in this process?"
            print(f"Using sample prompt: {user_input}")
        
        payload = {
            "prompt": user_input,
            "diagram_data": SAMPLE_BPMN_XML,
            "current_memory": memory
        }
        
        if session_id:
            payload["session_id"] = session_id
        
        result = test_api_with_requests(payload, f"Interactive: {user_input}")
        
        if result:
            memory = result.get('memory', memory)
            # Extract session_id from response if available
            if 'session_id' in result:
                session_id = result['session_id']

def print_help():
    """Print help information"""
    print("\n📖 Available Commands:")
    print("  help     - Show this help")
    print("  quit     - Exit interactive mode")
    print("  clear    - Clear memory and session")
    print("  sample   - Use a sample prompt")
    print("\n📝 Sample Prompts:")
    print("  - What does Task_1 do?")
    print("  - Add a new task after Process Order")
    print("  - What is the purpose of this process?")
    print("  - How many tasks are in this diagram?")

def run_test_scenarios():
    """Run predefined test scenarios"""
    print("🚀 Running Predefined Test Scenarios")
    print("=" * 50)
    
    # Test 1: Question about diagram
    test1_payload = {
        "prompt": "What does the Task_1 node do in this process?",
        "diagram_data": SAMPLE_BPMN_XML,
        "current_memory": ""
    }
    print_curl_command(CONVERSATION_ENDPOINT, test1_payload, "Test 1: Question about diagram")
    test_api_with_requests(test1_payload, "Question about diagram")
    
    # Test 2: Diagram modification
    test2_payload = {
        "prompt": "Add a new task called 'Send Confirmation Email' after the 'Process Order' task",
        "diagram_data": SAMPLE_BPMN_XML,
        "current_memory": ""
    }
    print_curl_command(CONVERSATION_ENDPOINT, test2_payload, "Test 2: Diagram modification")
    test_api_with_requests(test2_payload, "Diagram modification")
    
    # Test 3: Invalid BPMN XML
    test3_payload = {
        "prompt": "What does this do?",
        "diagram_data": "This is not valid BPMN XML",
        "current_memory": ""
    }
    print_curl_command(CONVERSATION_ENDPOINT, test3_payload, "Test 3: Invalid BPMN XML (should fail)")
    test_api_with_requests(test3_payload, "Invalid BPMN XML")
    
    # Test 4: Empty prompt
    test4_payload = {
        "prompt": "",
        "diagram_data": SAMPLE_BPMN_XML,
        "current_memory": ""
    }
    print_curl_command(CONVERSATION_ENDPOINT, test4_payload, "Test 4: Empty prompt (should fail)")
    test_api_with_requests(test4_payload, "Empty prompt")

def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ API is running and healthy")
            return True
        else:
            print(f"⚠️ API responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API is not accessible: {e}")
        print(f"Make sure the server is running on {API_BASE_URL}")
        return False

def main():
    """Main function"""
    print("🧪 Conversation API Manual Testing Tool")
    print("=" * 50)
    
    # Check API health
    if not check_api_health():
        print("\n💡 To start the API server, run:")
        print("cd ai-process-optimizer")
        print("python main.py")
        return
    
    print("\nChoose testing mode:")
    print("1. Run predefined test scenarios")
    print("2. Interactive testing mode")
    print("3. Show curl commands only")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        run_test_scenarios()
    elif choice == "2":
        interactive_test()
    elif choice == "3":
        run_test_scenarios()
    else:
        print("Invalid choice. Running predefined scenarios...")
        run_test_scenarios()

if __name__ == "__main__":
    main() 