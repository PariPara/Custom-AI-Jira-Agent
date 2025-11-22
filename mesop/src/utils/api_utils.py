import os
import requests
from typing import Optional, Dict, List

def get_django_api_url():
    """Get Django API URL based on environment"""
    if os.getenv('DOCKER_RUNNING') == 'true':
        return "http://django:8000"
    return "http://localhost:8000"

BASE_URL = get_django_api_url()

def call_jira_agent(user_input: str) -> str:
    """
    Call the Jira Agent API with user input
    
    Args:
        user_input: User's natural language query or command
        
    Returns:
        Agent's response as a string
    """
    try:
        response = requests.post(
            f"{BASE_URL}/api/jira-agent/",
            json={"request": user_input},  # Changed to "request"
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        # Handle different response formats
        if isinstance(result, dict):
            return result.get("output") or result.get("response") or result.get("result") or str(result)
        return str(result)
        
    except requests.exceptions.HTTPError as e:
        # Get error details from response
        try:
            error_detail = e.response.json()
            return f"API Error: {error_detail}"
        except:
            return f"API Error: {e.response.status_code} - {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"Error communicating with API: {str(e)}"

def call_jira_assistant(user_query: str) -> Dict:
    """
    Call the Jira Assistant API
    
    Args:
        user_query: User's natural language query
        
    Returns:
        API response containing JQL, Jira data, and analysis
    """
    try:
        response = requests.post(
            f"{BASE_URL}/api/jira-assistant/",
            json={"query": user_query},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "jql": None,
            "jira_data": None,
            "analysis": f"Error communicating with API: {str(e)}"
        }

def chat_with_assistant(message: str, conversation_history: Optional[List[Dict]] = None) -> str:
    """
    General chat with the assistant
    
    Args:
        message: User's message
        conversation_history: Previous conversation messages
        
    Returns:
        Assistant's response
    """
    try:
        payload = {"message": message}
        if conversation_history:
            payload["history"] = conversation_history
            
        response = requests.post(
            f"{BASE_URL}/api/chat/",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("response", "No response received")
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"

def health_check() -> bool:
    """Check if Django API is healthy"""
    try:
        response = requests.get(f"{BASE_URL}/api/health-check/", timeout=5)
        return response.status_code == 200
    except:
        return False
