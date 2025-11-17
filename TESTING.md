# Testing Guide

## Manual Testing Checklist

### 1. Backend API Tests

#### Test Project Creation
```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "test-automation",
    "project_type": "web",
    "assignees": ["your-github-username"],
    "teams_webhook": null
  }'
```

Expected: 200 OK with project details + GitHub repo created

#### Test List Projects
```bash
curl http://localhost:8000/api/projects
```

Expected: Array of all projects

#### Test Get Summary
```bash
curl http://localhost:8000/api/projects/1/summary
```

Expected: Summary object or "No summary available"

#### Test Generate Summary
```bash
curl -X POST http://localhost:8000/api/projects/1/generate-summary
```

Expected: New AI-generated summary

### 2. GitHub Webhook Test

Simulate a webhook payload:

```bash
curl -X POST http://localhost:8000/api/github-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "repository": {
      "html_url": "https://github.com/user/test-automation"
    },
    "commits": [
      {
        "author": {
          "name": "John Doe",
          "email": "john@example.com"
        },
        "message": "Initial commit",
        "added": ["README.md"],
        "modified": [],
        "removed": []
      }
    ]
  }'
```

Expected: 200 OK, commits tracked in database

### 3. Frontend Tests

#### Test Form Validation
1. Leave project name empty → Should show browser validation
2. Enter invalid GitHub username → Backend should handle gracefully
3. Enter invalid Teams webhook → Should handle gracefully

#### Test Successful Flow
1. Fill all fields correctly
2. Submit form
3. Wait for success message
4. Verify repo link works
5. Check GitHub for new repository

### 4. Integration Tests

#### End-to-End Flow
1. Create project via UI
2. Clone the created repository
3. Make a commit and push
4. Verify webhook received
5. Check database for contribution
6. Generate summary via API
7. Verify summary contains commit data

```bash
# After creating project
git clone <repo_url>
cd <repo_name>
echo "# Test" >> test.txt
git add .
git commit -m "Test webhook"
git push

# Check contributions
curl http://localhost:8000/api/projects/1/summary
```

### 5. Error Handling Tests

#### Invalid GitHub Token
- Set wrong token in .env
- Try creating project
- Expected: 500 error with clear message

#### LLM Timeout/Error
- Use invalid Gemini API key
- Expected: Fallback to template structure

#### Non-existent Project
```bash
curl http://localhost:8000/api/projects/999/summary
```
Expected: 404 "Project not found"

### 6. Database Tests

#### Check Database Contents
```bash
cd backend
sqlite3 project_automation.db

.tables
SELECT * FROM projects;
SELECT * FROM contributions;
SELECT * FROM summaries;
.quit
```

### 7. Performance Tests

#### LLM Response Time
- Should complete within 20 seconds
- Monitor console for timing

#### Concurrent Requests
```bash
# Create 5 projects simultaneously
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/projects \
    -H "Content-Type: application/json" \
    -d "{\"project_name\": \"test-$i\", \"project_type\": \"web\", \"assignees\": []}" &
done
```

## Automated Testing (Future Enhancement)

### Backend Tests (pytest)
```python
# test_api.py
def test_create_project():
    response = client.post("/api/projects", json={
        "project_name": "test",
        "project_type": "web",
        "assignees": []
    })
    assert response.status_code == 200
    assert "repo_url" in response.json()
```

### Frontend Tests (Jest/Vitest)
```javascript
// App.test.jsx
test('renders form', () => {
  render(<App />);
  expect(screen.getByText('Project Name')).toBeInTheDocument();
});
```

## Common Issues

### Issue: GitHub API rate limit
**Solution**: Wait 1 hour or use authenticated requests

### Issue: Webhook not receiving events
**Solution**: 
- Check webhook is registered in GitHub repo settings
- Use ngrok for local development
- Verify WEBHOOK_URL in .env

### Issue: Gemini API timeout/errors
**Solution**: 
- Check internet connection
- Verify API key is valid at https://makersuite.google.com/app/apikey
- System will use fallback templates

### Issue: Database locked
**Solution**: 
- Close all connections
- Delete project_automation.db and restart

