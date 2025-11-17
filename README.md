# AI-Driven Project Automation System

An intelligent system that automates project creation, tracks commits, and generates progress summaries using AI.

## Features

- 🤖 **AI-Powered Project Generation**: LLM generates project structure, skeleton code, and README
- 🔗 **GitHub Integration**: Automatically creates repos, adds collaborators, and sets up webhooks
- 📊 **Commit Tracking**: Monitors all commits and tracks contributor activity
- 📝 **Progress Summaries**: AI analyzes commits and generates actionable progress reports
- 💬 **Teams Notifications**: Sends updates to Microsoft Teams channels

## Tech Stack

- **Backend**: FastAPI + SQLite + SQLAlchemy
- **Frontend**: React + Vite
- **Integrations**: GitHub API, Google Gemini API, Microsoft Teams Webhooks

## Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- GitHub Personal Access Token ([Create one](https://github.com/settings/tokens))
- Google Gemini API Key ([Get one](https://makersuite.google.com/app/apikey))

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
```

5. Edit `.env` with your credentials:
```
GITHUB_TOKEN=ghp_your_token_here
GEMINI_API_KEY=your_gemini_key_here
WEBHOOK_URL=http://your-server.com/api/github-webhook
```

6. Run the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file (optional):
```bash
echo "VITE_API_URL=http://localhost:8000" > .env
```

4. Run development server:
```bash
npm run dev
```

The UI will be available at `http://localhost:3000`

## API Documentation

### Endpoints

#### Create Project
```http
POST /api/projects
Content-Type: application/json

{
  "project_name": "my-project",
  "project_type": "web",
  "assignees": ["user1", "user2"],
  "teams_webhook": "https://outlook.office.com/webhook/..."
}
```

**Response:**
```json
{
  "id": 1,
  "name": "my-project",
  "type": "web",
  "repo_url": "https://github.com/username/my-project",
  "created_at": "2025-11-12T10:30:00"
}
```

#### GitHub Webhook
```http
POST /api/github-webhook
Content-Type: application/json

{
  "repository": {...},
  "commits": [...]
}
```

#### Get Summary
```http
GET /api/projects/{project_id}/summary
```

#### Generate New Summary
```http
POST /api/projects/{project_id}/generate-summary?teams_webhook=https://...
```

#### List Projects
```http
GET /api/projects
```

## Usage

1. Open the frontend at `http://localhost:3000`
2. Fill in the project creation form:
   - **Project Name**: Choose a unique name
   - **Project Type**: Select from dropdown (web, api, mobile, etc.)
   - **Assignees**: Enter GitHub usernames (comma-separated)
   - **Teams Webhook**: Optional Teams webhook URL for notifications
3. Click "Create Project"
4. The system will:
   - Generate project structure using AI
   - Create GitHub repository
   - Add collaborators
   - Push initial files
   - Send Teams notification (if webhook provided)

## Database Schema

### projects
- `id`: Primary key
- `name`: Project name
- `type`: Project type
- `repo_url`: GitHub repository URL
- `created_at`: Creation timestamp

### contributions
- `id`: Primary key
- `project_id`: Foreign key to projects
- `author`: Developer name
- `email`: Developer email
- `commit_count`: Number of commits

### summaries
- `id`: Primary key
- `project_id`: Foreign key to projects
- `summary_text`: AI-generated summary
- `timestamp`: Generation timestamp

## Architecture

```
┌─────────────┐
│   Frontend  │
│   (React)   │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────────────────┐
│      FastAPI Backend            │
│  ┌──────────────────────────┐  │
│  │   API Endpoints          │  │
│  └───────┬──────────────────┘  │
│          │                      │
│  ┌───────▼──────┬───────┬─────┐│
│  │ LLM Service  │GitHub │Teams││
│  │  (OpenAI)    │  API  │ API ││
│  └──────────────┴───────┴─────┘│
│          │                      │
│  ┌───────▼──────────────────┐  │
│  │    SQLite Database       │  │
│  └──────────────────────────┘  │
└─────────────────────────────────┘
```

## Troubleshooting

### GitHub Token Permissions
Ensure your token has these scopes:
- `repo` (full control)
- `admin:repo_hook` (webhook management)

### Gemini API Limits
If you hit rate limits or quota issues, the system provides fallback templates.

### Webhook Setup
For local development, use ngrok to expose your localhost:
```bash
ngrok http 8000
# Use the ngrok URL in .env: WEBHOOK_URL=https://xxx.ngrok.io/api/github-webhook
```

## License

MIT

