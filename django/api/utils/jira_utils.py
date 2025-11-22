from jira import JIRA
import requests
import os
from decouple import config

# Initialize Jira client
def get_jira_client():
    """Get authenticated Jira client using API v3"""
    jira_url = os.getenv('JIRA_URL') or config('JIRA_URL')
    jira_email = os.getenv('JIRA_EMAIL') or config('JIRA_EMAIL')
    jira_api_token = os.getenv('JIRA_API_TOKEN') or config('JIRA_API_TOKEN')
    
    return JIRA(
        server=jira_url,
        basic_auth=(jira_email, jira_api_token)
    )

def get_jira_auth():
    """Get Jira authentication credentials"""
    jira_email = os.getenv('JIRA_EMAIL') or config('JIRA_EMAIL')
    jira_api_token = os.getenv('JIRA_API_TOKEN') or config('JIRA_API_TOKEN')
    return (jira_email, jira_api_token)

def get_jira_url():
    """Get Jira base URL"""
    url = os.getenv('JIRA_URL') or config('JIRA_URL')
    # Remove trailing slashes
    return url.rstrip('/')

def search_jira_issues(jql, max_results=50):
    """
    Search for Jira issues using JQL with the new API endpoint
    
    Args:
        jql: JQL query string
        max_results: Maximum number of results to return
        
    Returns:
        List of Jira issues
    """
    try:
        # Use the new /rest/api/3/search/jql endpoint
        base_url = get_jira_url()
        auth = get_jira_auth()
        
        url = f"{base_url}/rest/api/3/search/jql"
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        payload = {
            "jql": jql,
            "maxResults": max_results,
            "fields": ["summary", "status", "priority", "assignee", "reporter", "issuetype", "description"]
        }
        
        # Disable SSL verification for now (not recommended for production)
        # Better solution: install proper certificates in Docker
        response = requests.post(
            url, 
            json=payload, 
            auth=auth, 
            headers=headers,
            verify=True,  # Keep verification on
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Convert to JIRA issue-like objects for compatibility
        class JiraIssue:
            def __init__(self, issue_data):
                self.key = issue_data['key']
                self.fields = type('obj', (object,), {
                    'summary': issue_data['fields'].get('summary', ''),
                    'status': type('obj', (object,), {'name': issue_data['fields'].get('status', {}).get('name', 'Unknown')}),
                    'priority': type('obj', (object,), {'name': issue_data['fields'].get('priority', {}).get('name', 'None')}) if issue_data['fields'].get('priority') else None,
                    'issuetype': type('obj', (object,), {'name': issue_data['fields'].get('issuetype', {}).get('name', 'Unknown')}),
                })
        
        issues = [JiraIssue(issue) for issue in data.get('issues', [])]
        return issues
        
    except requests.exceptions.SSLError as e:
        print(f"SSL Error: {e}")
        print("Retrying with SSL verification disabled...")
        try:
            # Retry with SSL verification disabled
            response = requests.post(
                url, 
                json=payload, 
                auth=auth, 
                headers=headers,
                verify=False,  # Disable SSL verification
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            class JiraIssue:
                def __init__(self, issue_data):
                    self.key = issue_data['key']
                    self.fields = type('obj', (object,), {
                        'summary': issue_data['fields'].get('summary', ''),
                        'status': type('obj', (object,), {'name': issue_data['fields'].get('status', {}).get('name', 'Unknown')}),
                        'priority': type('obj', (object,), {'name': issue_data['fields'].get('priority', {}).get('name', 'None')}) if issue_data['fields'].get('priority') else None,
                        'issuetype': type('obj', (object,), {'name': issue_data['fields'].get('issuetype', {}).get('name', 'Unknown')}),
                    })
            
            issues = [JiraIssue(issue) for issue in data.get('issues', [])]
            return issues
        except Exception as retry_error:
            print(f"Retry also failed: {retry_error}")
            return []
    except Exception as e:
        print(f"Error searching Jira issues: {e}")
        return []

def get_all_tickets():
    """Get all tickets from Jira"""
    try:
        # Use JQL to get recent tickets
        issues = search_jira_issues('ORDER BY created DESC', max_results=1000)
        
        tickets = {}
        for issue in issues:
            tickets[issue.key] = {
                'summary': issue.fields.summary,
                'description': '',  # Description not included in search
                'status': issue.fields.status.name,
                'priority': issue.fields.priority.name if issue.fields.priority else 'None',
            }
        return tickets
    except Exception as e:
        print(f"Error getting all tickets: {e}")
        return {}

def get_ticket_data(ticket_number):
    """
    Get data for a specific ticket
    
    Args:
        ticket_number: Jira ticket key (e.g., 'PROJ-123')
        
    Returns:
        Tuple of (issue_key, issue_data_string)
    """
    try:
        jira = get_jira_client()
        issue = jira.issue(ticket_number)
        
        issue_data = f"""
        Summary: {issue.fields.summary}
        Description: {issue.fields.description or 'No description'}
        Status: {issue.fields.status.name}
        Priority: {issue.fields.priority.name if issue.fields.priority else 'None'}
        Assignee: {issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned'}
        Reporter: {issue.fields.reporter.displayName if issue.fields.reporter else 'Unknown'}
        """
        
        return issue.key, issue_data
    except Exception as e:
        print(f"Error getting ticket data: {e}")
        return ticket_number, f"Error: {str(e)}"

def link_jira_issue(primary_issue_key, related_issue_key):
    """
    Link two Jira issues together
    
    Args:
        primary_issue_key: Key of the primary issue
        related_issue_key: Key of the related issue
    """
    try:
        jira = get_jira_client()
        jira.create_issue_link(
            type="Relates",
            inwardIssue=primary_issue_key,
            outwardIssue=related_issue_key
        )
        print(f"Linked {primary_issue_key} to {related_issue_key}")
    except Exception as e:
        print(f"Error linking issues: {e}")

def add_jira_comment(issue_key, comment_text):
    """
    Add a comment to a Jira issue
    
    Args:
        issue_key: Jira ticket key
        comment_text: Comment text to add
    """
    try:
        jira = get_jira_client()
        jira.add_comment(issue_key, comment_text)
        print(f"Added comment to {issue_key}")
    except Exception as e:
        print(f"Error adding comment: {e}")

def extract_tag_helper(text, tag=None):
    """
    Extract content from XML-like tags
    
    Args:
        text: Text containing tags
        tag: Tag name to extract (optional)
        
    Returns:
        Extracted content or None
    """
    import re
    
    if not tag:
        # Try to extract any content between tags
        match = re.search(r'<([^>]+)>(.*?)</\1>', text, re.DOTALL)
        if match:
            return match.group(2).strip()
        return None
    
    pattern = f'<{tag}>(.*?)</{tag}>'
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    return None
