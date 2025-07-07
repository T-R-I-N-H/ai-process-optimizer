import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

    # External API Endpoints (ensure these are set in your .env or actual service URLs)
    VISUALIZE_API_ENDPOINT: str = os.getenv("VISUALIZE_API_ENDPOINT", "http://localhost:8001/visualize")
    CONVERSATION_API_ENDPOINT: str = os.getenv("CONVERSATION_API_ENDPOINT", "http://localhost:8002/conversation")
    OPTIMIZE_API_ENDPOINT: str = os.getenv("OPTIMIZE_API_ENDPOINT", "http://localhost:8003/optimize")
    BENCHMARK_API_ENDPOINT: str = os.getenv("BENCHMARK_API_ENDPOINT", "http://localhost:8004/benchmark")

    # Database settings (if you implement persistent memory)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db") # Example for SQLite

settings = Settings()