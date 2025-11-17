import os
from github import Github, GithubException
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def get_complete_commit_log(repo_url: str, max_commits: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieve complete commit log from a GitHub repository.
    
    Args:
        repo_url: GitHub repository URL or owner/repo format
        max_commits: Maximum number of commits to retrieve (default 100)
    
    Returns:
        List of commit dictionaries with detailed information:
        - message: Full commit message
        - author: Author name
        - date: Commit date (ISO format)
        - files_changed: Number of files changed
        - additions: Total lines added
        - deletions: Total lines deleted
        - files: List of changed files with patch details
    """
    try:
        logger.info(f"📥 Fetching complete commit log from {repo_url}")
        
        # Parse GitHub URL to get owner/repo
        if "github.com/" in repo_url:
            parts = repo_url.split("github.com/")[1].rstrip("/").split("/")
            if len(parts) < 2:
                raise ValueError("Invalid GitHub URL format")
            repo_path = f"{parts[0]}/{parts[1]}"
        else:
            repo_path = repo_url
        
        g = Github(os.getenv("GITHUB_TOKEN"))
        repo = g.get_repo(repo_path)
        
        commits_data = []
        commit_count = 0
        
        for commit in repo.get_commits():
            if commit_count >= max_commits:
                break
            
            try:
                # Extract file information (convert PaginatedList to list)
                files_info = []
                files_count = 0
                for file in commit.files:
                    files_info.append({
                        'filename': file.filename,
                        'status': file.status,  # 'added', 'modified', 'deleted'
                        'additions': file.additions,
                        'deletions': file.deletions,
                        'changes': file.changes
                    })
                    files_count += 1
                
                commit_data = {
                    'sha': commit.sha[:7],  # Short SHA
                    'message': commit.commit.message,
                    'author': commit.commit.author.name or "Unknown",
                    'email': commit.commit.author.email or "",
                    'date': commit.commit.author.date.isoformat() if commit.commit.author.date else None,
                    'files_changed': files_count,
                    'additions': commit.stats.additions if commit.stats else 0,
                    'deletions': commit.stats.deletions if commit.stats else 0,
                    'total_changes': (commit.stats.additions if commit.stats else 0) + (commit.stats.deletions if commit.stats else 0),
                    'files': files_info,
                    'html_url': commit.html_url
                }
                
                commits_data.append(commit_data)
                commit_count += 1
                
            except Exception as e:
                logger.warning(f"⚠️  Could not process commit: {str(e)}")
                continue
        
        logger.info(f"✅ Retrieved {len(commits_data)} commits successfully")
        return commits_data
    
    except GithubException as e:
        logger.error(f"❌ GitHub API error: {e.status} - {e.data.get('message', str(e))}")
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching commit log: {str(e)}")
        raise


def create_repository(project_name: str, project_structure: Dict, assignees: List[str]) -> Dict:
    try:
        g = Github(os.getenv("GITHUB_TOKEN"))
        user = g.get_user()
        
        repo = user.create_repo(
            name=project_name,
            description=f"Auto-generated {project_name} project",
            private=True,
            auto_init=False
        )
        
        for file_path, content in project_structure.get("files", {}).items():
            repo.create_file(
                path=file_path,
                message=f"Initial commit: Add {file_path}",
                content=content
            )
        
        for assignee in assignees:
            try:
                repo.add_to_collaborators(assignee, permission="push")
            except GithubException:
                pass
        
        webhook = repo.create_hook(
            name="web",
            config={
                "url": os.getenv("WEBHOOK_URL", "http://localhost:8000/api/github-webhook"),
                "content_type": "json"
            },
            events=["push"],
            active=True
        )
        
        return {
            "repo_url": repo.html_url,
            "clone_url": repo.clone_url,
            "webhook_id": webhook.id,
            "assignees_added": assignees
        }
    
    except Exception as e:
        raise Exception(f"GitHub API error: {str(e)}")

def get_repository_readme(repo_url: str) -> str:
    try:
        g = Github(os.getenv("GITHUB_TOKEN"))
        repo_name = repo_url.split("github.com/")[-1]
        repo = g.get_repo(repo_name)
        
        try:
            readme = repo.get_readme()
            return readme.decoded_content.decode('utf-8')
        except:
            return f"# {repo.name}\n\nNo README found."
    
    except Exception as e:
        return f"Error fetching README: {str(e)}"

def create_webhook(repo, webhook_url=None):
    if webhook_url is None or "localhost" in webhook_url:
        print("⚠️  Skipping webhook creation (localhost not publicly accessible)")
        return None
    
    try:
        hook = repo.create_hook(
            name="web",
            config={"url": webhook_url, "content_type": "json"},
            events=["push"],
            active=True
        )
        return hook
    except GithubException as e:
        raise Exception(f"Webhook creation failed: {e}")