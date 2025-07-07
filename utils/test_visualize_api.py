# test_visualize_api.py
import requests
import os
from dotenv import load_dotenv
import pytest
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app

# Load environment variables from .env file
load_dotenv()

# Get the Visualize API endpoint from environment variables
VISUALIZE_API_ENDPOINT = os.getenv("VISUALIZE_API_ENDPOINT", "http://localhost:8001/visualize")

client = TestClient(app)

def test_visualize_endpoint():
    payload = {
        "prompt": "Generate a BPMN diagram for a simple order process.",
        "file_texts": "Order Process: 1. Customer places order. 2. System processes order. 3. Order shipped. 4. Order delivered."
    }
    response = client.post("/visualize/visualize", json=payload)
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    data = response.json()
    assert "diagram_data" in data
    assert "diagram_description" in data
    assert "detail_descriptions" in data
    assert isinstance(data["detail_descriptions"], list)
    assert "memory" in data

if __name__ == "__main__":
    print(f"Attempting to send request to Visualize API at: {VISUALIZE_API_ENDPOINT}")

    # Define the payload for the request
    payload = {
        "prompt": "Generate a BPMN diagram for a typical online course registration process, including steps for selection, payment, and confirmation.",
        "file_texts": """
        Online Course Registration Process:
        1. Student browses courses.
        2. Student selects desired course(s).
        3. System checks course availability.
        4. If available, student proceeds to payment.
        5. Payment gateway processes payment.
        6. If payment is successful, student receives course confirmation and access.
        7. If payment fails, student is notified and can retry or cancel.
        8. If course is unavailable, student is notified.
        """
    }

    try:
        # Send the POST request
        response = requests.post(VISUALIZE_API_ENDPOINT, json=payload, timeout=60)

        # Raise an HTTPError for bad responses (4xx or 5xx)
        response.raise_for_status()

        # Parse the JSON response
        response_data = response.json()

        print("\n--- Visualize API Response ---")
        print(f"Status Code: {response.status_code}")
        print("Diagram Data (excerpt):")
        print(response_data.get("diagram_data", "")[:500] + "...") # Print first 500 chars
        print("\nDiagram Description:")
        print(response_data.get("Diagram_description"))
        print("\nDetail Descriptions:")
        for desc in response_data.get("detail_descriptions", []):
            print(f"- Node ID: {desc.get('node_id')}, Description: {desc.get('node_description')}")
        print("\nMemory:")
        print(response_data.get("Memory"))

    except requests.exceptions.ConnectionError as e:
        print(f"Error: Could not connect to the Visualize API at {VISUALIZE_API_ENDPOINT}. Is it running?")
        print(f"Details: {e}")
    except requests.exceptions.Timeout:
        print("Error: The request to the Visualize API timed out.")
    except requests.exceptions.HTTPError as e:
        print(f"Error: HTTP request failed with status code {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"An unexpected error occurred during the request: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")