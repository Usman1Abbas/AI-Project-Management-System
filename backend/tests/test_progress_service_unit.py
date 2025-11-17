"""
Simple integration tests for progress analyzer using sync approach.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test the progress service module directly
from services.progress_service import (
    generate_progress_summary,
    get_contributor_stats,
    analyze_repository,
    analyze_last_commit_impact
)


class TestProgressService:
    """Test the progress service module independently"""
    
    @patch('services.progress_service.genai.GenerativeModel')
    def test_generate_summary_with_llm(self, mock_genai):
        """Test summary generation with LLM"""
        # Mock response
        mock_response = MagicMock()
        mock_response.text = "## Progress\n\nTest repository summary"
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model
        
        commits = [
            {'author': 'John', 'message': 'Initial commit', 'files': ['file1.py']},
            {'author': 'Jane', 'message': 'Add feature', 'files': ['file2.py']}
        ]
        
        readme = "# Test Repo\nA test repository"
        
        result = generate_progress_summary(readme, commits, "test-project")
        
        assert "Progress" in result
        assert mock_model.generate_content.called
    
    def test_generate_summary_fallback(self):
        """Test summary generation with fallback"""
        commits = [
            {'author': 'John', 'message': 'Initial commit', 'files': ['file1.py']},
            {'author': 'Jane', 'message': 'Add feature', 'files': ['file2.py']}
        ]
        
        readme = "# Test Repo"
        
        result = generate_progress_summary(readme, commits, "test-project")
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Either LLM or fallback, we should get a summary
        assert "commit" in result.lower() or "progress" in result.lower()
    
    def test_get_contributor_stats_empty(self):
        """Test contributor stats with empty commits"""
        result = get_contributor_stats([])
        
        assert result['total_commits'] == 0
        assert result['total_contributors'] == 0
        assert result['total_files_changed'] == 0
        assert result['contributors'] == {}
    
    def test_get_contributor_stats_single_contributor(self):
        """Test contributor stats with single contributor"""
        commits = [
            {'author': 'Alice', 'message': 'First', 'files': ['a.py', 'b.py']},
            {'author': 'Alice', 'message': 'Second', 'files': ['c.py']},
        ]
        
        result = get_contributor_stats(commits)
        
        assert result['total_commits'] == 2
        assert result['total_contributors'] == 1
        assert result['total_files_changed'] == 3
        assert result['top_contributor'] == 'Alice'
        assert result['contributors']['Alice']['commits'] == 2
        assert result['contributors']['Alice']['files_changed'] == 3
    
    def test_get_contributor_stats_multiple_contributors(self):
        """Test contributor stats with multiple contributors"""
        commits = [
            {'author': 'Alice', 'message': 'First', 'files': ['a.py']},
            {'author': 'Bob', 'message': 'Second', 'files': ['b.py', 'c.py']},
            {'author': 'Alice', 'message': 'Third', 'files': ['d.py']},
        ]
        
        result = get_contributor_stats(commits)
        
        assert result['total_commits'] == 3
        assert result['total_contributors'] == 2
        assert result['total_files_changed'] == 4
        assert result['top_contributor'] == 'Alice'  # Alice has 2 commits
        
        assert result['contributors']['Alice']['commits'] == 2
        assert result['contributors']['Alice']['files_changed'] == 2
        assert result['contributors']['Bob']['commits'] == 1
        assert result['contributors']['Bob']['files_changed'] == 2
    
    def test_get_contributor_stats_with_missing_fields(self):
        """Test contributor stats handles missing fields gracefully"""
        commits = [
            {'author': 'Alice'},  # Missing message and files
            {'author': 'Bob', 'message': 'Commit', 'files': ['file.py']},
        ]
        
        result = get_contributor_stats(commits)
        
        # Should still work with missing fields
        assert result['total_commits'] == 2
        assert result['total_contributors'] == 2
        assert result['contributors']['Alice']['commits'] == 1
        assert result['contributors']['Alice']['files_changed'] == 0
    
    def test_analyze_repository_complete_workflow(self):
        """Test complete analysis workflow"""
        commits = [
            {'author': 'Developer', 'message': 'First commit', 'files': ['main.py']},
        ]
        
        readme = "# My Project\nA simple project"
        
        result = analyze_repository(readme, commits, "my-project")
        
        assert 'summary' in result
        assert 'statistics' in result
        assert 'generated_at' in result
        
        stats = result['statistics']
        assert stats['total_commits'] == 1
        assert stats['total_contributors'] == 1
        assert stats['top_contributor'] == 'Developer'


class TestProgressServiceEdgeCases:
    """Test edge cases in progress service"""
    
    def test_special_characters_in_author_name(self):
        """Test handling special characters"""
        commits = [
            {'author': 'José García', 'message': 'Commit', 'files': ['file.py']},
            {'author': 'François', 'message': 'Commit', 'files': ['file.py']},
        ]
        
        result = get_contributor_stats(commits)
        
        assert result['total_contributors'] == 2
        assert 'José García' in result['contributors']
        assert 'François' in result['contributors']
    
    def test_large_commit_history(self):
        """Test handling large commit history"""
        commits = [
            {'author': f'Developer {i % 5}', 'message': f'Commit {i}', 'files': [f'file{i}.py']}
            for i in range(100)
        ]
        
        result = get_contributor_stats(commits)
        
        assert result['total_commits'] == 100
        assert result['total_contributors'] == 5
        assert result['total_files_changed'] == 100
    
    def test_timestamp_format(self):
        """Test timestamp format in response"""
        commits = [
            {'author': 'Dev', 'message': 'Commit', 'files': [], 'timestamp': '2024-01-01T00:00:00'}
        ]
        
        result = analyze_repository("# Test", commits, "test")
        
        assert 'generated_at' in result
        # Should be ISO format
        assert 'T' in result['generated_at']


class TestLastCommitAnalysis:
    """Test last commit impact analysis"""
    
    @patch('services.progress_service.genai.GenerativeModel')
    def test_analyze_last_commit_with_llm(self, mock_genai):
        """Test last commit analysis with LLM"""
        mock_response = MagicMock()
        mock_response.text = "**Impact**: Major\n**Work Done**: Implemented new feature\n**Scope**: Feature"
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model
        
        last_commit = {
            'author': 'Developer',
            'message': 'Add new feature',
            'files': ['feature.py', 'test_feature.py'],
            'timestamp': '2024-01-15T10:00:00'
        }
        
        result = analyze_last_commit_impact(
            last_commit=last_commit,
            readme_content="# Project",
            project_name="test-project"
        )
        
        assert result['author'] == 'Developer'
        assert result['message'] == 'Add new feature'
        assert len(result['files_changed']) == 2
        assert 'impact_summary' in result
        assert 'work_done' in result
    
    def test_analyze_last_commit_fallback(self):
        """Test last commit analysis with fallback"""
        last_commit = {
            'author': 'Developer',
            'message': 'Bug fix',
            'files': ['bug.py'],
            'timestamp': '2024-01-15T10:00:00'
        }
        
        result = analyze_last_commit_impact(
            last_commit=last_commit,
            readme_content="# Project",
            project_name="test-project"
        )
        
        assert result['author'] == 'Developer'
        assert result['message'] == 'Bug fix'
        assert 'impact_summary' in result
        assert 'work_done' in result
        assert isinstance(result['files_changed'], list)
    
    def test_analyze_last_commit_empty(self):
        """Test last commit analysis with empty data"""
        result = analyze_last_commit_impact(
            last_commit=None,
            readme_content="# Project",
            project_name="test-project"
        )
        
        assert result['author'] == 'Unknown'
        assert 'No' in result['message']  # Could be "No message" or "No commit data available"
        assert result['timestamp'] is None
    
    def test_analyze_repository_with_last_commit(self):
        """Test complete analysis including last commit"""
        commits = [
            {'author': 'Dev1', 'message': 'Latest commit', 'files': ['file.py'], 'timestamp': '2024-01-15T10:00:00'},
            {'author': 'Dev2', 'message': 'Previous commit', 'files': ['other.py'], 'timestamp': '2024-01-14T10:00:00'},
        ]
        
        last_commit = commits[0]  # Most recent
        
        result = analyze_repository(
            readme_content="# Project",
            commits=commits,
            project_name="test-project",
            last_commit=last_commit
        )
        
        assert 'summary' in result
        assert 'statistics' in result
        assert 'last_commit' in result
        assert result['last_commit']['author'] == 'Dev1'
        assert result['last_commit']['message'] == 'Latest commit'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
