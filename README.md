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
3. **Start the Conversation API (in a new terminal):**
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
- Access the main API docs at: [http://localhost:8000/docs](http://localhost:8000/docs)
- Access the Conversation API docs at: [http://localhost:8002/docs](http://localhost:8002/docs)

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

## Docker Hub
To publish your image:
1. **Login to Docker Hub:**
   ```bash
   docker login
   ```
2. **Tag and push:**
   ```bash
   docker tag ai-process-optimizer yourdockerhubusername/ai-process-optimizer:latest
   docker push yourdockerhubusername/ai-process-optimizer:latest
   ```

Others can then pull and run:
```bash
docker pull yourdockerhubusername/ai-process-optimizer:latest
docker run --env-file .env -p 8000:8000 yourdockerhubusername/ai-process-optimizer:latest uvicorn main:app --host 0.0.0.0 --port 8000
```

## License
MIT
