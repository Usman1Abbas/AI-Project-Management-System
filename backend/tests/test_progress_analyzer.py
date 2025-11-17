"""
Tests for the progress analyzer endpoint.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import after path is set
import httpx
from main import app


@pytest.fixture
def test_app():
    """Provide test app"""
    return app


class TestProgressAnalyzerEndpoint:
    """Test the /api/progress/analyze endpoint"""
    
    @pytest.mark.asyncio
    @patch('services.progress_routes.Github')
    @patch('services.progress_routes.generate_progress_summary')
    @patch('services.progress_routes.get_contributor_stats')
    async def test_analyze_valid_github_url(self, mock_stats, mock_summary, mock_github, test_app):
        """Test analyzing a valid GitHub repository"""
        # Setup mocks
        mock_repo = MagicMock()
        mock_repo.full_name = "testuser/testrepo"
        mock_repo.name = "testrepo"
        mock_repo.description = "Test repository"
        
        # Mock commits
        mock_commit = MagicMock()
        mock_commit.commit.author.name = "Test User"
        mock_commit.commit.message = "Test commit"
        mock_commit.files = [MagicMock(filename="file.py")]
        mock_commit.commit.author.date = MagicMock()
        mock_commit.commit.author.date.isoformat.return_value = "2024-01-01T00:00:00"
        
        mock_repo.get_commits.return_value = [mock_commit]
        
        # Mock README
        mock_readme = MagicMock()
        mock_readme.decoded_content = b"# Test Repo\n\nA test repository"
        mock_repo.get_readme.return_value = mock_readme
        
        # Setup Github mock
        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance
        
        # Setup progress service mocks
        mock_summary.return_value = "## Progress\n\nTest progress"
        mock_stats.return_value = {
            'total_commits': 1,
            'total_contributors': 1,
            'total_files_changed': 1,
            'contributors': {'Test User': {'commits': 1, 'files_changed': 1}},
            'top_contributor': 'Test User'
        }
        
        # Make request
        response = client.post(
            "/api/progress/analyze",
            json={"repo_url": "https://github.com/testuser/testrepo"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert 'summary' in data
        assert 'statistics' in data
        assert 'timestamp' in data
        assert data['summary'] == "## Progress\n\nTest progress"
        assert data['statistics']['total_commits'] == 1
    
    def test_analyze_empty_url(self, client):
        """Test analyzing with empty repository URL"""
        response = client.post(
            "/api/progress/analyze",
            json={"repo_url": ""}
        )
        
        assert response.status_code == 400
        assert "cannot be empty" in response.json()['detail']
    
    @patch('services.progress_routes.Github')
    def test_analyze_invalid_url_format(self, mock_github, client):
        """Test analyzing with invalid URL format"""
        response = client.post(
            "/api/progress/analyze",
            json={"repo_url": "invalid-url"}
        )
        
        # Should still process - uses direct repo path
        assert response.status_code in [404, 500]
    
    @patch('services.progress_routes.Github')
    def test_analyze_repo_not_found(self, mock_github, client):
        """Test analyzing a non-existent repository"""
        from github import GithubException
        
        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.side_effect = GithubException(
            404, {"message": "Not Found"}
        )
        mock_github.return_value = mock_github_instance
        
        response = client.post(
            "/api/progress/analyze",
            json={"repo_url": "https://github.com/nonexistent/repo"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()['detail'].lower()
    
    @patch('services.progress_routes.Github')
    @patch('services.progress_routes.generate_progress_summary')
    @patch('services.progress_routes.get_contributor_stats')
    def test_analyze_with_shorthand_url(self, mock_stats, mock_summary, mock_github, client):
        """Test analyzing with shorthand GitHub URL (username/repo)"""
        # Setup mocks
        mock_repo = MagicMock()
        mock_repo.full_name = "testuser/testrepo"
        mock_repo.name = "testrepo"
        mock_repo.get_commits.return_value = []
        mock_repo.get_readme.return_value = MagicMock(
            decoded_content=b"# Test"
        )
        
        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance
        
        mock_summary.return_value = "## Progress"
        mock_stats.return_value = {
            'total_commits': 0,
            'total_contributors': 0,
            'total_files_changed': 0,
            'contributors': {},
            'top_contributor': None
        }
        
        response = client.post(
            "/api/progress/analyze",
            json={"repo_url": "testuser/testrepo"}
        )
        
        assert response.status_code == 200
        mock_github_instance.get_repo.assert_called_with("testuser/testrepo")
    
    @patch('services.progress_routes.Github')
    @patch('services.progress_routes.generate_progress_summary')
    @patch('services.progress_routes.get_contributor_stats')
    def test_analyze_with_graceful_readme_fallback(self, mock_stats, mock_summary, mock_github, client):
        """Test that endpoint handles missing README gracefully"""
        mock_repo = MagicMock()
        mock_repo.full_name = "testuser/testrepo"
        mock_repo.name = "testrepo"
        mock_repo.description = "Test description"
        mock_repo.get_commits.return_value = []
        mock_repo.get_readme.side_effect = Exception("README not found")
        
        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance
        
        mock_summary.return_value = "## Progress"
        mock_stats.return_value = {
            'total_commits': 0,
            'total_contributors': 0,
            'total_files_changed': 0,
            'contributors': {},
            'top_contributor': None
        }
        
        response = client.post(
            "/api/progress/analyze",
            json={"repo_url": "https://github.com/testuser/testrepo"}
        )
        
        assert response.status_code == 200
        # Should create fallback README
        assert mock_summary.called
    
    def test_health_check_endpoint(self, client):
        """Test that health check endpoint works"""
        response = client.get("/api/progress/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'progress-analyzer'


class TestProgressAnalyzerIntegration:
    """Integration tests with ProgressChecker frontend"""
    
    @patch('services.progress_routes.Github')
    @patch('services.progress_routes.generate_progress_summary')
    @patch('services.progress_routes.get_contributor_stats')
    def test_full_analysis_workflow(self, mock_stats, mock_summary, mock_github, client):
        """Test complete analysis workflow"""
        # Setup comprehensive mocks
        mock_repo = MagicMock()
        mock_repo.full_name = "awesome/project"
        mock_repo.name = "project"
        mock_repo.description = "An awesome project"
        
        # Multiple commits
        commits = []
        for i in range(3):
            commit = MagicMock()
            commit.commit.author.name = f"Developer {i+1}"
            commit.commit.message = f"Commit {i+1}"
            commit.files = [MagicMock(filename=f"file{i+1}.py")]
            commit.commit.author.date = MagicMock()
            commit.commit.author.date.isoformat.return_value = f"2024-01-0{i+1}T00:00:00"
            commits.append(commit)
        
        mock_repo.get_commits.return_value = commits
        mock_readme = MagicMock()
        mock_readme.decoded_content = b"# Project\n\nAwesome project"
        mock_repo.get_readme.return_value = mock_readme
        
        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance
        
        mock_summary.return_value = "## Status\n- Active development\n- 3 contributors"
        mock_stats.return_value = {
            'total_commits': 3,
            'total_contributors': 3,
            'total_files_changed': 3,
            'contributors': {
                'Developer 1': {'commits': 1, 'files_changed': 1},
                'Developer 2': {'commits': 1, 'files_changed': 1},
                'Developer 3': {'commits': 1, 'files_changed': 1},
            },
            'top_contributor': 'Developer 1'
        }
        
        response = client.post(
            "/api/progress/analyze",
            json={"repo_url": "https://github.com/awesome/project"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure matches ProgressChecker expectations
        assert 'summary' in data
        assert 'statistics' in data
        assert 'timestamp' in data
        
        stats = data['statistics']
        assert stats['total_commits'] == 3
        assert stats['total_contributors'] == 3
        assert len(stats['contributors']) == 3
        assert stats['top_contributor'] == 'Developer 1'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
