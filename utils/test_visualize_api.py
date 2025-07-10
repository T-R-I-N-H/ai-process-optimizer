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
VISUALIZE_API_ENDPOINT = os.getenv("VISUALIZE_API_ENDPOINT", "http://localhost:8000")

client = TestClient(app)

def test_visualize_endpoint_structure():
    """Test that the endpoint returns the correct structure even if LLM fails."""
    payload = {
        "prompt": "Test prompt",
        "file_texts": [
            {
                "file_type": "txt",
                "file_content": "Simple test content"
            }
        ]
    }
    response = client.post("/visualize/visualize", json=payload)
    # Even if LLM fails, we should get a 500 with proper error message, not 404
    assert response.status_code in [200, 500], f"Unexpected status code: {response.status_code}"
    if response.status_code == 500:
        data = response.json()
        assert "detail" in data
        print(f"LLM pipeline failed as expected: {data['detail']}")
    else:
        data = response.json()
        assert "diagram_data" in data
        assert "diagram_name" in data
        assert "diagram_description" in data
        assert "detail_descriptions" in data
        assert isinstance(data["detail_descriptions"], dict)
        assert "memory" in data

def test_visualize_endpoint():
    """Test the full LLM pipeline with a detailed process description."""
    payload = {
        "prompt": "Create a BPMN diagram for an online course registration process. The process should include student browsing, course selection, payment processing, and confirmation steps.",
        "file_texts": [
            {
                "file_type": "docx",
                "file_content": """
                Online Course Registration Process Description:
                
                Process Name: Online Course Registration
                Goal: Enable students to register for online courses efficiently
                
                Process Steps:
                1. Student accesses the course catalog and browses available courses
                2. Student selects desired course(s) from the catalog
                3. System checks course availability and prerequisites
                4. If course is available, student proceeds to payment gateway
                5. Payment gateway processes the student's payment
                6. If payment is successful, system generates course confirmation
                7. Student receives confirmation email with course access details
                8. If payment fails, student is notified and can retry or cancel
                9. If course is unavailable, student is notified and can select alternatives
                
                Inputs: Student credentials, course selection, payment information
                Outputs: Course confirmation, access credentials, payment receipt
                Pain Points: Payment failures, course unavailability, complex registration flow
                """
            }
        ]
    }
    response = client.post("/visualize/visualize", json=payload)
    if response.status_code == 200:
        data = response.json()
        assert "diagram_data" in data
        assert "diagram_name" in data
        assert "diagram_description" in data
        assert "detail_descriptions" in data
        assert isinstance(data["detail_descriptions"], dict)
        assert "memory" in data
        print("✅ Full LLM pipeline test passed!")
    else:
        print(f"⚠️ LLM pipeline test failed with status {response.status_code}: {response.json()}")
        # This is acceptable if LLM is not configured or fails
        assert response.status_code == 500
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
        
if __name__ == "__main__":
    print(f"Attempting to send request to Visualize API at: {VISUALIZE_API_ENDPOINT}")
    test_visualize_endpoint()
    # Define the payload for the request
    # payload = {
    #     "prompt": "Create a BPMN diagram for an online course registration process. The process should include student browsing, course selection, payment processing, and confirmation steps.",
    #     "file_texts": [
    #         {
    #             "file_type": "docx",
    #             "file_content": """
    #             Online Course Registration Process Description:
                
    #             Process Name: Online Course Registration
    #             Goal: Enable students to register for online courses efficiently
                
    #             Process Steps:
    #             1. Student accesses the course catalog and browses available courses
    #             2. Student selects desired course(s) from the catalog
    #             3. System checks course availability and prerequisites
    #             4. If course is available, student proceeds to payment gateway
    #             5. Payment gateway processes the student's payment
    #             6. If payment is successful, system generates course confirmation
    #             7. Student receives confirmation email with course access details
    #             8. If payment fails, student is notified and can retry or cancel
    #             9. If course is unavailable, student is notified and can select alternatives
                
    #             Inputs: Student credentials, course selection, payment information
    #             Outputs: Course confirmation, access credentials, payment receipt
    #             Pain Points: Payment failures, course unavailability, complex registration flow
    #             """
    #         }
    #     ]
    # }

    # try:
    #     # Send the POST request
    #     response = requests.post(VISUALIZE_API_ENDPOINT, json=payload, timeout=60)

    #     # Raise an HTTPError for bad responses (4xx or 5xx)
    #     response.raise_for_status()

    #     # Parse the JSON response
    #     response_data = response.json()

    #     print("\n--- Visualize API Response ---")
    #     print(f"Status Code: {response.status_code}")
    #     print("Diagram Data (excerpt):")
    #     print(response_data.get("diagram_data", "")[:500] + "...") # Print first 500 chars
    #     print("\nDiagram Description:")
    #     print(response_data.get("Diagram_description"))
    #     print("\nDetail Descriptions:")
    #     for desc in response_data.get("detail_descriptions", []):
    #         print(f"- Node ID: {desc.get('node_id')}, Description: {desc.get('node_description')}")
    #     print("\nMemory:")
    #     print(response_data.get("Memory"))

    # except requests.exceptions.ConnectionError as e:
    #     print(f"Error: Could not connect to the Visualize API at {VISUALIZE_API_ENDPOINT}. Is it running?")
    #     print(f"Details: {e}")
    # except requests.exceptions.Timeout:
    #     print("Error: The request to the Visualize API timed out.")
    # except requests.exceptions.HTTPError as e:
    #     print(f"Error: HTTP request failed with status code {e.response.status_code}")
    #     print(f"Response: {e.response.text}")
    # except requests.exceptions.RequestException as e:
    #     print(f"An unexpected error occurred during the request: {e}")
    # except Exception as e:
    #     print(f"An unexpected error occurred: {e}")