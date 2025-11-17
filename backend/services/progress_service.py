"""
Independent progress tracking service.
This module analyzes repository progress from commit history and README.
Can be used independently from the main FastAPI application.
"""

import logging
from typing import Dict, List, Optional, Any
import google.generativeai as genai
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("❌ GEMINI_API_KEY not found in environment variables!")
else:
    logger.info(f"✅ GEMINI_API_KEY configured: {GEMINI_API_KEY[:10]}...")
    genai.configure(api_key=GEMINI_API_KEY)

GEMINI_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")


def extract_text_from_response(response) -> str:
    """
    Safely extract text from Gemini response object.
    Handles both simple text responses and complex multi-part responses.
    
    Args:
        response: Gemini API response object
    
    Returns:
        str: Extracted text content
    """
    try:
        # Try simple text accessor first
        return response.text
    except (AttributeError, ValueError):
        # If that fails, use parts accessor
        try:
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    text_parts = []
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            text_parts.append(part.text)
                    return "\n".join(text_parts)
            return ""
        except Exception as e:
            logger.error(f"❌ Error extracting response text: {str(e)}")
            return ""


# Fallback template for progress summary
FALLBACK_SUMMARY = """## Project Progress Summary


### Status
Active repository with ongoing development and contributions.

### Key Metrics
- **Total Commits**: {total_commits}
- **Contributors**: {total_contributors}
- **Files Changed**: {total_files_changed}

### Contributions
The repository has received contributions from {total_contributors} developer(s):
{contributors_list}

### Focus Areas
- Continuous development and maintenance
- Code quality improvements
- Community contributions

### Next Steps
1. Continue monitoring repository activity
2. Encourage contributor participation
3. Review code quality metrics
"""

# Fallback template for last commit analysis
FALLBACK_LAST_COMMIT = {
    'author': 'Unknown',
    'message': 'No commit data available',
    'timestamp': None,
    'files_changed': [],
    'impact_summary': 'Unable to determine commit impact at this time.',
    'work_done': 'Analysis unavailable'
}


def generate_concise_progress_summary(
    readme_content: str,
    commits: List[Dict[str, Any]],
    project_name: str
) -> str:
    """
    Generate a 2-3 line concise progress update summary using Gemini AI.
    
    Args:
        readme_content: The README content from the repository
        commits: List of complete commit data including all fields
        project_name: Name of the project
    
    Returns:
        str: 2-3 line concise progress summary
    """
    try:
        logger.info(f"🤖 Generating concise progress summary for {project_name}...")
        
        if not commits:
            return f"📊 {project_name}: No commit history available yet. Repository is in initial setup phase."
        
        # Extract key metrics from commits
        total_commits = len(commits)
        total_additions = sum(c.get('additions', 0) for c in commits)
        total_deletions = sum(c.get('deletions', 0) for c in commits)
        unique_authors = len(set(c.get('author', 'Unknown') for c in commits))
        
        # Build context from recent commits
        recent_commits = commits[:10]
        commits_summary = "\n".join([
            f"- [{c.get('date', 'Unknown').split('T')[0] if c.get('date') else 'Unknown'}] "
            f"{c.get('author', 'Unknown')}: {c.get('message', 'No message').split(chr(10))[0][:60]}..."
            for c in recent_commits
        ])
        
        prompt = f"""Generate a CONCISE 2-3 sentence progress update for this GitHub repository. 
        
Repository: {project_name}
README Excerpt: {readme_content[:500]}

Commit Statistics:
- Total Commits: {total_commits}
- Contributors: {unique_authors}
- Total Changes: {total_additions} additions, {total_deletions} deletions
- Recent Commits:
{commits_summary}

Rules:
1. Keep it to exactly 2-3 sentences
2. Focus on current status and progress
3. Be actionable and clear
4. Use emoji sparingly (1-2 max)
5. Format: Start with emoji, then concise update

Example format:
📊 Project has achieved {total_commits}+ commits with steady development. {unique_authors} contributors actively working on implementation. Next focus: performance optimization and testing."""
        logger.info(f"📡 Using model: {GEMINI_MODEL}")
        model = genai.GenerativeModel(GEMINI_MODEL)
        logger.info(f"🔄 Sending prompt to Gemini (prompt length: {len(prompt)} chars)")
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(
            max_output_tokens=300,
            temperature=0.7
        ))
        
        summary_text = extract_text_from_response(response).strip()
        logger.info(f"✅ Concise summary generated: {summary_text[:100]}...")
        return summary_text
    
    except Exception as e:
        logger.error(f"❌ Gemini API Error: {type(e).__name__}: {str(e)}")
        logger.warning(f"⚠️  Could not generate concise summary with Gemini: {str(e)}")
        logger.info("📋 Using fallback concise summary")
        
        # Fallback: Generate simple concise summary
        total_commits = len(commits)
        unique_authors = len(set(c.get('author', 'Unknown') for c in commits))
        total_changes = sum(c.get('total_changes', 0) for c in commits)
        
        return f"📊 {project_name}: {total_commits} commits by {unique_authors} contributors with {total_changes} total changes. Actively maintained with ongoing development. Team focused on feature implementation and bug fixes."


def generate_progress_summary(
    readme_content: str,
    commits: List[Dict[str, Any]],
    project_name: str
) -> str:
    """
    Generate a progress summary using Gemini AI with fallback.
    
    Args:
        readme_content: The README content from the repository
        commits: List of commit data with author, message, files, timestamp
        project_name: Name of the project
    
    Returns:
        str: Formatted progress summary
    """
    try:
        logger.info(f"🤖 Generating progress summary for {project_name} using Gemini...")
        
        # Prepare commit summary
        commit_summary = "\n".join([
            f"- {c.get('author', 'Unknown')}: {c.get('message', 'No message')} "
            f"({len(c.get('files', []))} files changed)"
            for c in commits[:20]  # Last 20 commits
        ])
        
        if not commit_summary:
            commit_summary = "No commits available"
        
        prompt = f"""Analyze this repository and provide a concise progress summary.

Repository: {project_name}

README Content:
{readme_content[:2000]}

Recent Commits:
{commit_summary}

Provide a structured progress report with:
1. **Status**: Current state (active, stable, experimental, etc.)
2. **Metrics**: Key numbers (commits, contributors, files)
3. **Contributions**: Main contributors and their work
4. **Focus Areas**: Primary development areas
5. **Next Steps**: Recommended improvements

Keep the response concise and actionable."""
        logger.info(f"📡 Using model: {GEMINI_MODEL}")
        model = genai.GenerativeModel(GEMINI_MODEL)
        logger.info(f"🔄 Sending prompt to Gemini (prompt length: {len(prompt)} chars)")
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(
            max_output_tokens=1000,
            temperature=0.7
        ))
        
        summary_text = extract_text_from_response(response)
        logger.info("✅ Progress summary generated successfully")
        return summary_text
    
    except Exception as e:
        logger.error(f"❌ Gemini API Error: {type(e).__name__}: {str(e)}")
        logger.warning(f"⚠️  Could not generate summary with Gemini: {str(e)}")
        logger.info("📋 Using fallback template")
        
        # Use fallback template
        contributors_list = "\n".join([
            f"- {name}" for name in set(c.get('author', 'Unknown') for c in commits)
        ])
        
        return FALLBACK_SUMMARY.format(
            total_commits=len(commits),
            total_contributors=len(set(c.get('author', 'Unknown') for c in commits)),
            total_files_changed=sum(len(c.get('files', [])) for c in commits),
            contributors_list=contributors_list or "- No contributors data"
        )


def get_contributor_stats(commits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract contributor statistics from commit list.
    
    Args:
        commits: List of commit data
    
    Returns:
        dict: Statistics including total commits, contributors, and per-contributor data
    """
    try:
        logger.info("📊 Calculating contributor statistics...")
        
        if not commits:
            logger.warning("⚠️  No commits provided for statistics")
            return {
                'total_commits': 0,
                'total_contributors': 0,
                'total_files_changed': 0,
                'contributors': {},
                'top_contributor': None
            }
        
        contributors = {}
        total_files_changed = 0
        
        for commit in commits:
            author = commit.get('author', 'Unknown')
            files = commit.get('files', [])
            
            if author not in contributors:
                contributors[author] = {
                    'commits': 0,
                    'files_changed': 0,
                    'last_commit': None
                }
            
            contributors[author]['commits'] += 1
            contributors[author]['files_changed'] += len(files)
            contributors[author]['last_commit'] = commit.get('timestamp', None)
            total_files_changed += len(files)
        
        # Find top contributor
        top_contributor = max(
            contributors.items(),
            key=lambda x: x[1]['commits']
        )[0] if contributors else None
        
        logger.info(f"✅ Statistics calculated: {len(contributors)} contributors, "
                   f"{len(commits)} commits, {total_files_changed} files changed")
        
        return {
            'total_commits': len(commits),
            'total_contributors': len(contributors),
            'total_files_changed': total_files_changed,
            'contributors': contributors,
            'top_contributor': top_contributor
        }
    
    except Exception as e:
        logger.error(f"❌ Error calculating statistics: {str(e)}")
        return {
            'total_commits': len(commits),
            'total_contributors': 0,
            'total_files_changed': 0,
            'contributors': {},
            'top_contributor': None,
            'error': str(e)
        }


def format_summary_for_display(
    summary: str,
    stats: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Format summary and statistics for API response.
    
    Args:
        summary: Progress summary text
        stats: Statistics dictionary
    
    Returns:
        dict: Formatted response with summary and stats
    """
    try:
        logger.info("📦 Formatting summary for API response...")
        
        return {
            'summary': summary,
            'statistics': stats,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Error formatting summary: {str(e)}")
        return {
            'summary': summary,
            'statistics': stats,
            'generated_at': datetime.utcnow().isoformat(),
            'error': str(e)
        }


def analyze_last_commit_impact(
    last_commit: Dict[str, Any],
    readme_content: str,
    project_name: str
) -> Dict[str, Any]:
    """
    Analyze the last commit and compare with README to determine work done.
    Uses LLM to provide insights on commit impact.
    
    Args:
        last_commit: Last commit data with author, message, files, timestamp
        readme_content: Project README content
        project_name: Project name
    
    Returns:
        dict: Commit analysis with impact summary and work done description
    """
    try:
        if not last_commit or not last_commit.get('message'):
            logger.warning("⚠️  No last commit data available")
            return FALLBACK_LAST_COMMIT
        
        logger.info(f"🔍 Analyzing last commit impact for {project_name}...")
        
        files_list = "\n".join(last_commit.get('files', [])[:20])  # Top 20 files
        
        prompt = f"""Analyze this commit and provide a brief summary of work done.

Project: {project_name}

README Context:
{readme_content[:1500]}

Last Commit Details:
- Author: {last_commit.get('author', 'Unknown')}
- Message: {last_commit.get('message', 'No message')}
- Files Changed ({len(last_commit.get('files', []))} total):
{files_list if files_list else 'No files data'}
- Timestamp: {last_commit.get('timestamp', 'Unknown')}

Based on the commit message, files changed, and project README, provide:
1. **Impact**: How impactful is this commit? (critical, major, minor, trivial)
2. **Work Done**: 1-2 sentence summary of what was accomplished
3. **Scope**: Was this a bug fix, feature, refactor, or documentation change?

Keep it concise and technical."""
        logger.info(f"📡 Using model: {GEMINI_MODEL}")
        model = genai.GenerativeModel(GEMINI_MODEL)
        logger.info(f"🔄 Sending prompt to Gemini (prompt length: {len(prompt)} chars)")
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(
            max_output_tokens=500,
            temperature=0.7
        ))
        
        impact_summary = extract_text_from_response(response)
        logger.info("✅ Last commit analysis completed")
        
        return {
            'author': last_commit.get('author', 'Unknown'),
            'message': last_commit.get('message', 'No message'),
            'timestamp': last_commit.get('timestamp'),
            'files_changed': last_commit.get('files', []),
            'impact_summary': impact_summary,
            'work_done': impact_summary.split('\n')[0] if impact_summary else 'Analysis complete'
        }
    
    except Exception as e:
        logger.warning(f"⚠️  Could not analyze last commit with LLM: {str(e)}")
        logger.info("📋 Using fallback commit data")
        
        return {
            'author': last_commit.get('author', 'Unknown') if last_commit else 'Unknown',
            'message': last_commit.get('message', 'No message') if last_commit else 'No message',
            'timestamp': last_commit.get('timestamp') if last_commit else None,
            'files_changed': last_commit.get('files', []) if last_commit else [],
            'impact_summary': 'Work: Unable to generate detailed analysis. See commit message and files for details.',
            'work_done': last_commit.get('message', 'No message') if last_commit else 'No data'
        }


# Convenience function for complete analysis
def analyze_repository(
    readme_content: str,
    commits: List[Dict[str, Any]],
    project_name: str,
    last_commit: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Complete repository analysis pipeline including last commit analysis.
    
    Args:
        readme_content: Repository README content
        commits: List of commits
        project_name: Project name
        last_commit: Last commit data (optional)
    
    Returns:
        dict: Complete analysis with summary, statistics, and last commit impact
    """
    logger.info(f"🔍 Starting complete analysis for {project_name}")
    
    summary = generate_progress_summary(readme_content, commits, project_name)
    stats = get_contributor_stats(commits)
    
    # Analyze last commit if provided
    last_commit_analysis = None
    if last_commit:
        last_commit_analysis = analyze_last_commit_impact(last_commit, readme_content, project_name)
    
    result = format_summary_for_display(summary, stats)
    
    if last_commit_analysis:
        result['last_commit'] = last_commit_analysis
    
    logger.info("✅ Complete analysis finished")
    return result
