import requests
from typing import List

def send_teams_notification(webhook_url: str, project_name: str, repo_url: str, assignees: List[str]) -> bool:
    if not webhook_url:
        return False
    
    assignees_text = ", ".join([f"@{a}" for a in assignees])
    
    message = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": f"New Project: {project_name}",
        "themeColor": "0078D7",
        "title": f"🚀 New Project Created: {project_name}",
        "sections": [{
            "activityTitle": "Project Setup Complete",
            "facts": [
                {"name": "Repository:", "value": repo_url},
                {"name": "Assignees:", "value": assignees_text}
            ],
            "text": f"A new project has been created and you've been added as a collaborator. Check out the repository to get started!"
        }],
        "potentialAction": [{
            "@type": "OpenUri",
            "name": "View Repository",
            "targets": [{"os": "default", "uri": repo_url}]
        }]
    }
    
    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Teams notification failed: {e}")
        return False

def send_summary_notification(webhook_url: str, project_name: str, summary: str) -> bool:
    if not webhook_url:
        return False
    
    message = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": f"Progress Update: {project_name}",
        "themeColor": "28A745",
        "title": f"📊 Progress Summary: {project_name}",
        "sections": [{
            "text": summary
        }]
    }
    
    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Teams notification failed: {e}")
        return False

