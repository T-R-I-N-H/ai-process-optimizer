# AI Process Optimizer

A multi-agent pipeline for business process analysis, improvement, and BPMN diagram generation using Google Gemini LLM. Includes:
- Process context extraction
- Bottleneck analysis
- Solution generation
- BPMN XML generation
- Advanced conversation API for Q&A and diagram modification

## Features
- FastAPI backend for process analysis and visualization
- Conversation API microservice for advanced BPMN Q&A and modification
- Google Gemini LLM integration
- Modular agent architecture

## Requirements
- Python 3.8+
- Docker (for containerized deployment)
- Google Gemini API key

## Environment Variables
Create a `.env` file in the project root with:
```
GEMINI_API_KEY=your_actual_api_key_here
```

## Running Locally
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Start the main app:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```
3. **Start the Conversation API:**
   ```bash
   uvicorn conversation_api:app --port 8002
   ```

## Running with Docker
1. **Build the Docker image:**
   ```bash
   docker build -t ai-process-optimizer .
   ```
2. **Run the main app:**
   ```bash
   docker run --env-file .env -p 8000:8000 ai-process-optimizer uvicorn main:app --host 0.0.0.0 --port 8000
   ```
3. **Run the Conversation API:**
   ```bash
   docker run --env-file .env -p 8002:8002 ai-process-optimizer uvicorn conversation_api:app --host 0.0.0.0 --port 8002
   ```

## Usage
- Access the Visualize API docs at: [http://localhost:8000/docs](http://localhost:8000/docs)
- Access the Conversation API docs at: [http://localhost:8002/docs](http://localhost:8002/docs)

### Example: Test the Visualize API
```bash
curl -X POST http://localhost:8000/visualize/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Generate a BPMN diagram for a simple order process.",
    "file_texts": "Order Process: 1. Customer places order. 2. System processes order. 3. Order shipped. 4. Order delivered."
  }'
```

### Example: Test the Conversation API
```bash
curl -X POST http://localhost:8002/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What does this diagram represent?",
    "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
    "memory": ""
  }'
```
