import os
import mesop as me
from decouple import Config, RepositoryEnv

def get_config():
    """Load configuration from environment or config file"""
    # Try to load from mounted config file first
    config_path = '/srv/mesop-app/config/config.ini'
    
    if os.path.exists(config_path):
        return Config(RepositoryEnv(config_path))
    
    # Fallback to environment variables
    return Config()

config = get_config()

# Jira settings
JIRA_URL = os.getenv('JIRA_URL', '')
JIRA_EMAIL = os.getenv('JIRA_EMAIL', '')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN', '')

# Hugging Face settings
HF_TOKEN = os.getenv('HF_TOKEN', '')

# Example prompts for the UI
EXAMPLE_PROMPTS = [
    "Triage ticket PROJ-123",
    "Show me all high priority bugs",
    "List open tickets assigned to me",
    "Find tickets related to authentication",
    "What are the blockers for this sprint?",
]

# Mesop State class for UI
@me.stateclass
class State:
    input: str = ""
    output: str = ""
    in_progress: bool = False
