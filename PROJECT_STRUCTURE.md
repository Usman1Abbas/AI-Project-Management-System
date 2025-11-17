# Project Structure

```
LPAI/
│
├── backend/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_service.py          # OpenAI/Claude integration
│   │   ├── github_service.py       # GitHub API operations
│   │   └── teams_service.py        # Microsoft Teams webhooks
│   │
│   ├── main.py                     # FastAPI application & endpoints
│   ├── models.py                   # SQLAlchemy & Pydantic models
│   ├── database.py                 # Database configuration
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Environment variables template
│   ├── start.sh                    # Unix startup script
│   └── start.bat                   # Windows startup script
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Main React component
│   │   ├── App.css                 # Styles
│   │   ├── api.js                  # API client
│   │   └── main.jsx                # Entry point
│   │
│   ├── index.html                  # HTML template
│   ├── package.json                # Node dependencies
│   ├── vite.config.js              # Vite configuration
│   └── .env.example                # Frontend env template
│
├── README.md                       # Full documentation
├── QUICKSTART.md                   # Quick start guide
├── PROJECT_STRUCTURE.md            # This file
└── .gitignore                      # Git ignore rules
```

## Key Components

### Backend Services

**llm_service.py**
- `generate_project_structure()` - Creates project files using LLM
- `generate_progress_summary()` - Analyzes commits and generates reports

**github_service.py**
- `create_repository()` - Creates repo, pushes files, adds collaborators
- `get_repository_readme()` - Fetches README for analysis

**teams_service.py**
- `send_teams_notification()` - Sends project creation alerts
- `send_summary_notification()` - Posts progress summaries

### API Endpoints

- `POST /api/projects` - Create new project
- `POST /api/github-webhook` - Receive GitHub webhook events
- `GET /api/projects/{id}/summary` - Get latest summary
- `POST /api/projects/{id}/generate-summary` - Generate new summary
- `GET /api/projects` - List all projects

### Database Models

**Project**: id, name, type, repo_url, created_at
**Contribution**: id, project_id, author, email, commit_count
**Summary**: id, project_id, summary_text, timestamp

### Frontend

**App.jsx**: Single-page form for project creation
**api.js**: Axios client for backend communication
**App.css**: Modern gradient UI styling

## Data Flow

1. User submits form → Frontend
2. Frontend POST → Backend `/api/projects`
3. Backend → LLM (generate structure)
4. Backend → GitHub API (create repo)
5. Backend → Teams (send notification)
6. GitHub push → Webhook → Backend
7. Backend stores commits in DB
8. User requests summary → Backend → LLM → Teams

