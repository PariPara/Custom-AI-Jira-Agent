import json 
import concurrent.futures
import os 
import re
from huggingface_hub import InferenceClient

# local imports
from api.utils import jira_utils

# Load system prompts
with open("./api/utils/system_prompts.json") as f:
    system_prompts = json.load(f)
with open("./api/utils/example_prompts.json") as f:
    example_prompts = json.load(f)

# Initialize Hugging Face client
def get_hf_client():
    hf_token = os.getenv('HF_TOKEN')
    if not hf_token:
        raise ValueError("HF_TOKEN environment variable is required")
    return InferenceClient(token=hf_token)

def chat_completion(messages, model="meta-llama/Llama-3.2-3B-Instruct", temperature=0.7, max_tokens=2000):
    """Call Hugging Face Inference API for chat completion"""
    client = get_hf_client()
    
    try:
        # Use the chat completions API (OpenAI-compatible)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling Hugging Face API: {e}")
        raise

class LLMTask:
    def __init__(self, system_prompt, examples):
        self.system_prompt = system_prompt
        self.examples = examples

    def construct_messages(self, input_text):
        """Construct messages array for chat completion"""
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add few-shot examples
        for example in self.examples:
            messages.append({"role": "user", "content": example["input"]})
            messages.append({"role": "assistant", "content": example["output"]})
        
        # Add current input
        messages.append({"role": "user", "content": input_text})
        
        return messages
  
    def run_llm(self, input_text):
        """Run LLM with few-shot prompting"""
        messages = self.construct_messages(input_text)
        return chat_completion(messages, temperature=0)

product_model = LLMTask(
    system_prompts.get("system_prompt_product"), 
    example_prompts.get("examples_product")
)
linking_model = LLMTask(
    system_prompts.get("system_prompt_linking"), 
    example_prompts.get("examples_linking")
)

def check_issue_and_link_helper(args):
    key, data, primary_issue_key, primary_issue_data = args
    if key != primary_issue_key and \
    llm_check_ticket_match(primary_issue_data, data):
        jira_utils.link_jira_issue(primary_issue_key, key) 

def find_related_tickets(primary_issue_key, primary_issue_data, issues):
    args = [(key, data, primary_issue_key, primary_issue_data) for key, data in issues.items()]
    with concurrent.futures.ThreadPoolExecutor(os.cpu_count()) as executor:
        executor.map(check_issue_and_link_helper, args)

def llm_check_ticket_match(ticket1, ticket2):
    llm_result = linking_model.run_llm(f"<ticket1>{ticket1}<ticket1><ticket2>{ticket2}<ticket2>")
    if ((result := jira_utils.extract_tag_helper(llm_result))) \
    and (result == 'True'):
        return True 
    
def user_stories_acceptance_criteria_priority(primary_issue_key, primary_issue_data):
    if llm_result := product_model.run_llm(f"<description>{primary_issue_data}<description>"):
        print(f"llm_result: {llm_result}")
        user_stories = jira_utils.extract_tag_helper(llm_result,"user_stories") or ''
        acceptance_criteria = jira_utils.extract_tag_helper(llm_result,"acceptance_criteria") or ''
        priority = jira_utils.extract_tag_helper(llm_result,"priority") or ''
        thought = jira_utils.extract_tag_helper(llm_result,"thought") or ''
        comment = f"user_stories: {user_stories}\nacceptance_criteria: {acceptance_criteria}\npriority: {priority}\nthought: {thought}"
        jira_utils.add_jira_comment(primary_issue_key, comment) 

def triage(ticket_number: str) -> str:
    """Triage a given ticket and link related tickets"""
    ticket_number = str(ticket_number)
    all_tickets = jira_utils.get_all_tickets()
    primary_issue_key, primary_issue_data = jira_utils.get_ticket_data(ticket_number)
    find_related_tickets(primary_issue_key, primary_issue_data, all_tickets)
    user_stories_acceptance_criteria_priority(primary_issue_key, primary_issue_data)
    return "Task complete"

def search_tickets(query: str) -> str:
    """Search for Jira tickets based on natural language query"""
    try:
        # Simple keyword-based JQL generation
        jql = ""
        
        if "open" in query.lower() or "opened" in query.lower():
            jql = "status != Done AND status != Closed"
        
        if "bug" in query.lower():
            if jql:
                jql += " AND type = Bug"
            else:
                jql = "type = Bug"
        
        if "high priority" in query.lower():
            if jql:
                jql += " AND priority = High"
            else:
                jql = "priority = High"
        
        # If no JQL generated, get all tickets
        if not jql:
            jql = "ORDER BY created DESC"
        
        print(f"Generated JQL: {jql}")
        
        # Execute JQL query
        tickets = jira_utils.search_jira_issues(jql)
        
        if not tickets:
            return "No tickets found matching your query."
        
        # Format results
        result = f"Found {len(tickets)} ticket(s):\n\n"
        for issue in tickets[:10]:  # Limit to 10 results
            result += f"- {issue.key}: {issue.fields.summary} (Status: {issue.fields.status.name})\n"
        
        if len(tickets) > 10:
            result += f"\n... and {len(tickets) - 10} more tickets."
        
        return result
    except Exception as e:
        return f"Error searching tickets: {str(e)}"

# Simplified agent implementation
class SimpleAgent:
    def __init__(self, tools, max_iterations=3):
        self.tools = tools
        self.max_iterations = max_iterations
    
    def invoke(self, input_dict):
        """Execute agent - simplified to handle general queries"""
        user_input = input_dict.get("input", "")
        
        # Check if input is a triage command
        if "triage" in user_input.lower():
            # Extract ticket number
            ticket_match = re.search(r'[A-Z]+-\d+', user_input)
            if ticket_match:
                ticket_number = ticket_match.group(0)
                result = self.tools["triage"](ticket_number)
                return {"output": f"Successfully triaged ticket {ticket_number}. {result}"}
            else:
                return {"output": "Please provide a valid ticket number (e.g., PROJ-123)"}
        
        # Check if input is a search/list command
        search_keywords = ["list", "show", "find", "search", "get", "all"]
        if any(keyword in user_input.lower() for keyword in search_keywords):
            result = self.tools["search_tickets"](user_input)
            return {"output": result}
        
        # For general queries, use direct chat completion
        messages = [
            {"role": "system", "content": "You are a helpful Jira assistant. Help users with their Jira-related questions and tasks."},
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = chat_completion(messages, max_tokens=500)
            return {"output": response}
        except Exception as e:
            return {"output": f"I encountered an error: {str(e)}. Please try rephrasing your question."}

# Initialize agent with available tools
jira_tools = {
    "triage": triage,
    "search_tickets": search_tickets,
}

agent = SimpleAgent(tools=jira_tools, max_iterations=3)

if __name__ == '__main__':
    pass
