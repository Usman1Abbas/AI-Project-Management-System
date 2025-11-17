"""
Progress analysis endpoint for checking repository progress.
This module provides API endpoints to analyze GitHub repositories.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from github import Github, GithubException
import os

from services.progress_service import (
    generate_progress_summary,
    generate_concise_progress_summary,
    get_contributor_stats,
    analyze_last_commit_impact
)
from services.github_service import get_complete_commit_log

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/progress", tags=["progress"])


class ProgressAnalysisRequest(BaseModel):
    """Request model for progress analysis"""
    repo_url: str


class ProgressAnalysisResponse(BaseModel):
    """Response model for progress analysis"""
    summary: str
    concise_summary: Optional[str] = None
    statistics: dict
    commits_log: Optional[List[Dict[str, Any]]] = None
    readme_content: Optional[str] = None
    timestamp: Optional[str] = None
    last_commit: Optional[dict] = None


@router.post("/analyze", response_model=ProgressAnalysisResponse)
async def analyze_repository_progress(request: ProgressAnalysisRequest):
    """
    Analyze repository progress by checking commit history and README.
    Returns complete commit log, README content, and concise progress summary.
    
    Args:
        request: ProgressAnalysisRequest with repo_url
    
    Returns:
        ProgressAnalysisResponse with summary, statistics, and commit data
    """
    try:
        repo_url = request.repo_url.strip()
        
        if not repo_url:
            raise HTTPException(status_code=400, detail="Repository URL cannot be empty")
        
        logger.info(f"🔄 Analyzing repository: {repo_url}")
        
        # Parse GitHub URL
        try:
            # Extract owner/repo from URL
            if "github.com/" in repo_url:
                parts = repo_url.split("github.com/")[1].rstrip("/").split("/")
                if len(parts) < 2:
                    raise ValueError("Invalid GitHub URL format")
                repo_path = f"{parts[0]}/{parts[1]}"
            else:
                repo_path = repo_url
            
            logger.info(f"📌 Repository path: {repo_path}")
        except Exception as e:
            logger.error(f"❌ URL parsing error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid repository URL format: {str(e)}"
            )
        
        # Fetch repository data from GitHub
        try:
            g = Github(os.getenv("GITHUB_TOKEN"))
            repo = g.get_repo(repo_path)
            
            logger.info(f"✅ Repository found: {repo.full_name}")
            
            # Fetch complete commit log using new function
            complete_commits_log = []
            try:
                logger.info("📥 Fetching complete commit log...")
                complete_commits_log = get_complete_commit_log(repo_url, max_commits=100)
                logger.info(f"✅ Retrieved {len(complete_commits_log)} commits with full details")
            except Exception as e:
                logger.warning(f"⚠️  Could not fetch complete commit log: {str(e)}")
                complete_commits_log = []
            
            # Prepare simplified commits list for summary generation
            commits = []
            last_commit = None
            for idx, commit in enumerate(repo.get_commits()[:50]):  # Get last 50 commits
                try:
                    # Get stats from commit (additions, deletions)
                    stats = commit.stats
                    additions = stats.additions if stats else 0
                    deletions = stats.deletions if stats else 0
                except:
                    additions = 0
                    deletions = 0
                
                commit_data = {
                    'author': commit.commit.author.name or "Unknown",
                    'message': commit.commit.message.split('\n')[0],  # First line only
                    'files': [f.filename for f in commit.files],
                    'timestamp': commit.commit.author.date.isoformat() if commit.commit.author.date else None,
                    'additions': additions,
                    'deletions': deletions,
                    'total_changes': additions + deletions
                }
                commits.append(commit_data)
                
                # Capture the very first (most recent) commit
                if idx == 0:
                    last_commit = commit_data
            
            logger.info(f"📊 Retrieved {len(commits)} commits for analysis")
            
            # Get README
            readme_content = None
            try:
                readme = repo.get_readme()
                readme_content = readme.decoded_content.decode('utf-8')
                logger.info("📖 README retrieved")
            except Exception as e:
                logger.warning(f"⚠️  Could not fetch README: {str(e)}")
                readme_content = f"# {repo.name}\n\n{repo.description or 'Repository'}"
            
            # Generate progress summary (existing feature)
            try:
                logger.info("🔄 Generating full progress summary...")
                summary = generate_progress_summary(
                    readme_content=readme_content,
                    commits=commits,
                    project_name=repo.name
                )
                logger.info("✅ Full summary generated")
            except Exception as e:
                logger.error(f"❌ Summary generation error: {str(e)}")
                summary = f"## Progress Summary\n\nRepository: {repo.full_name}\n\nUnable to generate detailed summary at this time."
            
            # Generate concise progress summary (NEW feature)
            concise_summary = None
            try:
                logger.info("🔄 Generating concise progress summary...")
                concise_summary = generate_concise_progress_summary(
                    readme_content=readme_content,
                    commits=commits,
                    project_name=repo.name
                )
                logger.info(f"✅ Concise summary generated: {concise_summary[:80]}...")
            except Exception as e:
                logger.warning(f"⚠️  Could not generate concise summary: {str(e)}")
                concise_summary = None
            
            # Get contributor statistics
            try:
                logger.info("📊 Calculating contributor statistics...")
                stats = get_contributor_stats(commits)
                logger.info(f"✅ Stats calculated: {stats['total_contributors']} contributors")
            except Exception as e:
                logger.error(f"❌ Statistics calculation error: {str(e)}")
                stats = {
                    'total_commits': len(commits),
                    'total_contributors': 0,
                    'total_files_changed': 0,
                    'contributors': {},
                    'top_contributor': None,
                    'error': str(e)
                }
            
            # Analyze last commit impact
            last_commit_analysis = None
            try:
                if last_commit:
                    logger.info("📝 Analyzing last commit impact...")
                    last_commit_analysis = analyze_last_commit_impact(
                        last_commit=last_commit,
                        readme_content=readme_content,
                        project_name=repo.name
                    )
                    logger.info("✅ Last commit analysis completed")
            except Exception as e:
                logger.warning(f"⚠️  Could not analyze last commit: {str(e)}")
            
            from datetime import datetime
            
            logger.info("✅ Repository analysis completed successfully")
            
            response_data = {
                "summary": summary,
                "concise_summary": concise_summary,
                "statistics": stats,
                "commits_log": complete_commits_log if complete_commits_log else None,
                "readme_content": readme_content if readme_content else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if last_commit_analysis:
                response_data["last_commit"] = last_commit_analysis
            
            return ProgressAnalysisResponse(**response_data)
        
        except GithubException as e:
            logger.error(f"❌ GitHub API error: {e.status} - {e.data.get('message', str(e))}")
            
            if e.status == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Repository not found: {repo_path}"
                )
            else:
                raise HTTPException(
                    status_code=e.status,
                    detail=f"GitHub API error: {e.data.get('message', str(e))}"
                )
        
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching repository data: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in analyze endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for progress analyzer"""
    return {
        "status": "healthy",
        "service": "progress-analyzer",
        "version": "1.0.0"
    }
