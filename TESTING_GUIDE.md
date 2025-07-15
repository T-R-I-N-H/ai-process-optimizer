# Testing Guide for Conversation API

This guide provides comprehensive instructions for testing the updated Conversation API in the AI Process Optimizer.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Starting the API Server](#starting-the-api-server)
3. [Testing Methods](#testing-methods)
4. [Test Scenarios](#test-scenarios)
5. [Troubleshooting](#troubleshooting)

## Prerequisites

Before testing, ensure you have:

1. **Python 3.8+** installed
2. **Required dependencies** installed:
   ```bash
   cd ai-process-optimizer
   pip install -r requirements.txt
   ```
3. **Environment variables** configured (if needed for LLM services)

## Starting the API Server

1. **Navigate to the project directory:**
   ```bash
   cd ai-process-optimizer
   ```

2. **Start the FastAPI server:**
   ```bash
   python main.py
   ```
   
   The server will start on `http://localhost:8000`

3. **Verify the server is running:**
   ```bash
   curl http://localhost:8000/
   ```
   
   Expected response: `{"message": "AI Process Optimizer API is running!"}`

## Testing Methods

### 1. Automated Tests (Recommended)

#### Run Pytest Tests
```bash
# Run all conversation API tests
pytest test_conversation_api.py -v

# Run specific test classes
pytest test_conversation_api.py::TestConversationAPIValidation -v
pytest test_conversation_api.py::TestConversationAPIFunctionality -v

# Run with coverage
pytest test_conversation_api.py --cov=. --cov-report=html
```

#### Run Custom Test Script
```bash
# Run the comprehensive test script
python utils/test_conversation_api.py
```

### 2. Manual Testing Script

#### Interactive Testing
```bash
# Run the interactive testing tool
python utils/manual_test_conversation.py
```

This tool provides:
- Interactive conversation testing
- Predefined test scenarios
- Curl command generation
- Real-time API health checks

### 3. Direct API Testing

#### Using curl
```bash
# Test a question about a diagram
curl -X POST http://localhost:8000/interaction/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What does Task_1 do?",
    "diagram_data": "<bpmn:definitions><bpmn:process><bpmn:task id=\"Task_1\" name=\"Validate Order\"/></bpmn:process></bpmn:definitions>",
    "current_memory": ""
  }'
```

#### Using Python requests
```python
import requests

url = "http://localhost:8000/interaction/conversation"
payload = {
    "prompt": "What does Task_1 do?",
    "diagram_data": "<bpmn:definitions><bpmn:process><bpmn:task id=\"Task_1\" name=\"Validate Order\"/></bpmn:process></bpmn:definitions>",
    "current_memory": ""
}

response = requests.post(url, json=payload)
print(response.json())
```

### 4. FastAPI Interactive Documentation

1. **Open your browser** and go to `http://localhost:8000/docs`
2. **Find the conversation endpoint** under "External API Interactions"
3. **Click "Try it out"** and test with sample data
4. **View the interactive API documentation** and test directly in the browser

## Test Scenarios

### Validation Tests

#### 1. Missing Required Fields
```json
{
  "prompt": "What does Task_1 do?"
  // Missing: diagram_data, current_memory
}
```
**Expected:** 422 Unprocessable Entity

#### 2. Empty Prompt
```json
{
  "prompt": "",
  "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
  "current_memory": ""
}
```
**Expected:** 400 Bad Request

#### 3. Invalid BPMN XML
```json
{
  "prompt": "What does this do?",
  "diagram_data": "This is not valid BPMN XML",
  "current_memory": ""
}
```
**Expected:** 400 Bad Request

#### 4. Memory Too Long
```json
{
  "prompt": "What does Task_1 do?",
  "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
  "current_memory": "A".repeat(15000)
}
```
**Expected:** 400 Bad Request

#### 5. Invalid Session ID Format
```json
{
  "session_id": "invalid@session#id",
  "prompt": "What does Task_1 do?",
  "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
  "current_memory": ""
}
```
**Expected:** 422 Unprocessable Entity

### Functional Tests

#### 1. Question Answering
```json
{
  "prompt": "What does the Task_1 node do in this process?",
  "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
  "current_memory": ""
}
```
**Expected Response:**
```json
{
  "action": "answer_question",
  "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
  "detail_descriptions": {},
  "answer": "Task_1 is responsible for...",
  "memory": "Session context: User asked about Task_1..."
}
```

#### 2. Diagram Modification
```json
{
  "prompt": "Add a new task called 'Send Confirmation Email' after the 'Process Order' task",
  "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
  "current_memory": ""
}
```
**Expected Response:**
```json
{
  "action": "modify_diagram",
  "diagram_data": "<bpmn:definitions>...<bpmn:task id=\"Task_4\" name=\"Send Confirmation Email\"/>...</bpmn:definitions>",
  "detail_descriptions": {
    "Task_1": "Validates incoming orders",
    "Task_2": "Processes valid orders",
    "Task_4": "Sends confirmation emails to customers"
  },
  "answer": "I've added a new task 'Send Confirmation Email' after the 'Process Order' task...",
  "memory": "Session context: User requested diagram modification..."
}
```

#### 3. Conversation Memory
```json
{
  "prompt": "Based on our previous conversation, what are the main steps?",
  "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
  "current_memory": "Previous session memory string..."
}
```
**Expected:** Response should reference previous conversation context

### Sample BPMN XML for Testing

Use this sample BPMN XML for testing:

```xml
<?xml version="1.0" encoding="UTF-8"?>
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
</bpmn:definitions>
```

## Troubleshooting

### Common Issues

#### 1. Server Won't Start
**Error:** `ModuleNotFoundError: No module named 'api'`
**Solution:** Ensure you're running from the `ai-process-optimizer` directory

#### 2. Import Errors
**Error:** `ImportError: cannot import name 'WorkflowOrchestrator'`
**Solution:** Check that all dependencies are installed and the orchestrator is properly initialized

#### 3. LLM Service Errors
**Error:** `500 Internal Server Error` during conversation processing
**Solution:** 
- Check LLM service configuration
- Verify API keys are set correctly
- Check logs for specific error messages

#### 4. Validation Errors
**Error:** `422 Unprocessable Entity`
**Solution:** 
- Ensure all required fields are present
- Check BPMN XML format
- Verify field lengths are within limits

### Debug Mode

To run the server in debug mode with detailed logging:

```bash
# Set debug environment variable
export DEBUG=true

# Start server with debug logging
python main.py
```

### Log Analysis

Check the server logs for detailed error information:

```bash
# View real-time logs
tail -f logs/app.log

# Search for specific errors
grep "ERROR" logs/app.log
```

## Performance Testing

### Load Testing

Use tools like Apache Bench or wrk for load testing:

```bash
# Test with 100 requests, 10 concurrent
ab -n 100 -c 10 -p test_payload.json -T application/json http://localhost:8000/interaction/conversation
```

### Memory Testing

Test memory persistence across multiple requests:

```bash
# Run the memory persistence test
python utils/test_conversation_api.py
```

## Integration Testing

### Frontend Integration

1. **Test with your frontend application**
2. **Verify CORS is working correctly**
3. **Test session management**
4. **Verify real-time updates**

### API Integration

1. **Test with other API endpoints**
2. **Verify data consistency**
3. **Test error handling**

## Continuous Integration

Add these tests to your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run Conversation API Tests
  run: |
    cd ai-process-optimizer
    pip install -r requirements.txt
    pytest test_conversation_api.py -v
```

## Support

If you encounter issues:

1. **Check the logs** for detailed error messages
2. **Verify your environment** matches the prerequisites
3. **Test with the provided sample data**
4. **Review the API documentation** at `http://localhost:8000/docs`

For additional help, refer to the project documentation or create an issue in the repository. 