# Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Step 1: Get Your API Keys

1. **GitHub Token**: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: `repo`, `admin:repo_hook`
   - Copy the token

2. **Google Gemini API Key**: https://makersuite.google.com/app/apikey
   - Click "Create API Key"
   - Copy the key

3. **Teams Webhook** (Optional): 
   - In Teams, go to channel → Connectors → Incoming Webhook
   - Copy the webhook URL

### Step 2: Backend Setup

```bash
cd backend

# Windows
start.bat

# Mac/Linux
chmod +x start.sh
./start.sh
```

When prompted, edit `.env` file:
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GEMINI_API_KEY=xxxxxxxxxxxx
WEBHOOK_URL=http://localhost:8000/api/github-webhook
```

Run again:
```bash
# Windows
start.bat

# Mac/Linux
./start.sh
```

Backend will be at: **http://localhost:8000**

### Step 3: Frontend Setup

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend will be at: **http://localhost:3000**

### Step 4: Create Your First Project

1. Open http://localhost:3000
2. Fill in:
   - **Project Name**: `test-project`
   - **Project Type**: Select from dropdown
   - **Assignees**: Your GitHub username
   - **Teams Webhook**: (optional) Paste your Teams webhook
3. Click "Create Project"
4. Watch the magic happen! ✨

### What Happens Next?

- ✅ AI generates project structure
- ✅ GitHub repo created
- ✅ Initial files pushed
- ✅ Collaborators added
- ✅ Webhook configured
- ✅ Teams notification sent

### Test the Webhook

Push a commit to the created repo:
```bash
git clone <repo_url>
cd <repo_name>
echo "test" >> README.md
git add .
git commit -m "Test commit"
git push
```

Check the database for tracked commits!

### Generate Progress Summary

```bash
curl -X POST http://localhost:8000/api/projects/1/generate-summary
```

### Troubleshooting

**Port already in use?**
```bash
# Backend: Edit main.py, change port 8000 to 8001
# Frontend: Edit vite.config.js, change port 3000 to 3001
```

**GitHub API errors?**
- Verify token has correct permissions
- Check token hasn't expired
- Ensure token is in .env file

**Gemini API errors?**
- System will use fallback templates
- Check API key is valid
- Verify you have API access enabled

### Next Steps

- Check out the full [README.md](README.md) for detailed documentation
- Explore API docs at http://localhost:8000/docs
- Customize LLM prompts in `backend/services/llm_service.py`

Happy automating! 🎉

