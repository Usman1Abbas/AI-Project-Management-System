"""
Test suite for GitHub webhook commit tracking functionality.
Tests the /api/github-webhook endpoint and Contribution tracking.
"""

import pytest
import json
from datetime import datetime
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, get_db
from database import Base
from models import Project, Contribution, ProjectCreate
from starlette.testclient import TestClient

# Setup test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def setup_database():
    """Create test database tables before each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(setup_database):
    """Create test client for each test."""
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_project(setup_database):
    """Create a test project in the database."""
    db = TestingSessionLocal()
    project = Project(
        name="test-project",
        type="web",
        repo_url="https://github.com/testuser/test-project"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    project_id = project.id
    db.close()
    return project_id


class TestGitHubWebhook:
    """Test suite for GitHub webhook endpoint."""

    def test_webhook_with_single_commit(self, client, test_project):
        """Test webhook receiving a single commit."""
        payload = {
            "repository": {
                "html_url": "https://github.com/testuser/test-project"
            },
            "commits": [
                {
                    "author": {
                        "name": "John Doe",
                        "email": "john@example.com"
                    },
                    "message": "Initial commit"
                }
            ]
        }

        response = client.post("/api/github-webhook", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["commits_processed"] == 1

        # Verify contribution was recorded
        db = TestingSessionLocal()
        contribution = db.query(Contribution).filter(
            Contribution.email == "john@example.com"
        ).first()
        assert contribution is not None
        assert contribution.author == "John Doe"
        assert contribution.commit_count == 1
        db.close()

    def test_webhook_with_multiple_commits(self, client, test_project):
        """Test webhook receiving multiple commits from different authors."""
        payload = {
            "repository": {
                "html_url": "https://github.com/testuser/test-project"
            },
            "commits": [
                {
                    "author": {
                        "name": "John Doe",
                        "email": "john@example.com"
                    },
                    "message": "Feature: Add login"
                },
                {
                    "author": {
                        "name": "Jane Smith",
                        "email": "jane@example.com"
                    },
                    "message": "Feature: Add database"
                },
                {
                    "author": {
                        "name": "John Doe",
                        "email": "john@example.com"
                    },
                    "message": "Fix: Bug in login"
                }
            ]
        }

        response = client.post("/api/github-webhook", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["commits_processed"] == 3

        # Verify contributions were recorded correctly
        db = TestingSessionLocal()
        
        john_contribution = db.query(Contribution).filter(
            Contribution.email == "john@example.com"
        ).first()
        assert john_contribution is not None
        assert john_contribution.commit_count == 2

        jane_contribution = db.query(Contribution).filter(
            Contribution.email == "jane@example.com"
        ).first()
        assert jane_contribution is not None
        assert jane_contribution.commit_count == 1
        
        db.close()

    def test_webhook_increments_existing_contributor(self, client, test_project):
        """Test that webhook increments commit count for existing contributors."""
        # First webhook call
        payload1 = {
            "repository": {
                "html_url": "https://github.com/testuser/test-project"
            },
            "commits": [
                {
                    "author": {
                        "name": "John Doe",
                        "email": "john@example.com"
                    },
                    "message": "First commit"
                }
            ]
        }
        response1 = client.post("/api/github-webhook", json=payload1)
        assert response1.status_code == 200

        # Second webhook call from same author
        payload2 = {
            "repository": {
                "html_url": "https://github.com/testuser/test-project"
            },
            "commits": [
                {
                    "author": {
                        "name": "John Doe",
                        "email": "john@example.com"
                    },
                    "message": "Second commit"
                }
            ]
        }
        response2 = client.post("/api/github-webhook", json=payload2)
        assert response2.status_code == 200

        # Verify commit count is incremented
        db = TestingSessionLocal()
        contribution = db.query(Contribution).filter(
            Contribution.email == "john@example.com"
        ).first()
        assert contribution.commit_count == 2
        db.close()

    def test_webhook_ignores_missing_commits(self, client, test_project):
        """Test that webhook ignores payloads without commits."""
        payload = {
            "repository": {
                "html_url": "https://github.com/testuser/test-project"
            }
        }

        response = client.post("/api/github-webhook", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"

    def test_webhook_ignores_missing_repository(self, client, test_project):
        """Test that webhook ignores payloads without repository info."""
        payload = {
            "commits": [
                {
                    "author": {
                        "name": "John Doe",
                        "email": "john@example.com"
                    },
                    "message": "Test commit"
                }
            ]
        }

        response = client.post("/api/github-webhook", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"

    def test_webhook_project_not_found(self, client, setup_database):
        """Test webhook when project doesn't exist in database."""
        payload = {
            "repository": {
                "html_url": "https://github.com/unknown/unknown-project"
            },
            "commits": [
                {
                    "author": {
                        "name": "John Doe",
                        "email": "john@example.com"
                    },
                    "message": "Test commit"
                }
            ]
        }

        response = client.post("/api/github-webhook", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "project not found"

    def test_webhook_empty_commits_list(self, client, test_project):
        """Test webhook with empty commits list."""
        payload = {
            "repository": {
                "html_url": "https://github.com/testuser/test-project"
            },
            "commits": []
        }

        response = client.post("/api/github-webhook", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["commits_processed"] == 0

    def test_webhook_special_characters_in_commit_message(self, client, test_project):
        """Test webhook handles special characters in commit messages."""
        payload = {
            "repository": {
                "html_url": "https://github.com/testuser/test-project"
            },
            "commits": [
                {
                    "author": {
                        "name": "John Döe",
                        "email": "john@example.com"
                    },
                    "message": 'Fix: "Bug" fix with special chars & symbols™'
                }
            ]
        }

        response = client.post("/api/github-webhook", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["commits_processed"] == 1

    def test_contribution_project_relationship(self, client, test_project):
        """Test that contributions are correctly linked to projects."""
        payload = {
            "repository": {
                "html_url": "https://github.com/testuser/test-project"
            },
            "commits": [
                {
                    "author": {
                        "name": "John Doe",
                        "email": "john@example.com"
                    },
                    "message": "Test commit"
                }
            ]
        }

        response = client.post("/api/github-webhook", json=payload)
        assert response.status_code == 200

        # Verify contribution is linked to correct project
        db = TestingSessionLocal()
        contribution = db.query(Contribution).filter(
            Contribution.email == "john@example.com"
        ).first()
        assert contribution.project_id == test_project
        
        project = db.query(Project).filter(Project.id == test_project).first()
        assert project.name == "test-project"
        assert len(project.contributions) == 1
        db.close()


class TestContributionTracking:
    """Test suite for contribution tracking functionality."""

    def test_get_project_contributions(self, client, test_project):
        """Test retrieving all contributions for a project."""
        payload = {
            "repository": {
                "html_url": "https://github.com/testuser/test-project"
            },
            "commits": [
                {
                    "author": {
                        "name": "Alice",
                        "email": "alice@example.com"
                    },
                    "message": "Commit 1"
                },
                {
                    "author": {
                        "name": "Bob",
                        "email": "bob@example.com"
                    },
                    "message": "Commit 2"
                }
            ]
        }

        client.post("/api/github-webhook", json=payload)

        db = TestingSessionLocal()
        contributions = db.query(Contribution).filter(
            Contribution.project_id == test_project
        ).all()
        assert len(contributions) == 2
        db.close()

    def test_contribution_count_accuracy(self, client, test_project):
        """Test that contribution counts are accurate over multiple webhooks."""
        # Simulate multiple webhook calls
        for i in range(3):
            payload = {
                "repository": {
                    "html_url": "https://github.com/testuser/test-project"
                },
                "commits": [
                    {
                        "author": {
                            "name": "Developer",
                            "email": "dev@example.com"
                        },
                        "message": f"Commit {i+1}"
                    }
                ]
            }
            response = client.post("/api/github-webhook", json=payload)
            assert response.status_code == 200

        db = TestingSessionLocal()
        contribution = db.query(Contribution).filter(
            Contribution.email == "dev@example.com"
        ).first()
        assert contribution.commit_count == 3
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
