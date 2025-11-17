# Google Gemini Configuration

This project has been configured to use **Google Gemini** instead of OpenAI.

## What Changed

### 1. API Key Setup
You need a **Gemini API Key** instead of OpenAI:
- Get it from: https://makersuite.google.com/app/apikey
- Add to `.env` as: `GEMINI_API_KEY=your_key_here`

### 2. Dependencies
Updated `requirements.txt`:
```
google-generativeai==0.3.2  # Replaces openai
```

### 3. LLM Service
Updated `backend/services/llm_service.py`:
- Uses `google.generativeai` library
- Model: `gemini-pro`
- Handles JSON response parsing (Gemini sometimes wraps in markdown)
- Automatic fallback to templates on errors

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Environment Variables

Your `.env` file should look like:

```env
GITHUB_TOKEN=ghp_your_token_here
GEMINI_API_KEY=your_gemini_key_here
WEBHOOK_URL=http://localhost:8000/api/github-webhook
```

## API Key Setup Steps

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Select a Google Cloud project (or create one)
5. Copy the generated API key
6. Add it to your `.env` file

## Gemini Free Tier

Gemini Pro offers a generous free tier:
- 60 requests per minute
- 1,500 requests per day
- Perfect for this automation system

## Error Handling

The system includes robust error handling:
- **Invalid API Key**: Falls back to template structure
- **Rate Limits**: Returns fallback templates
- **Timeout**: Uses default project structure
- **JSON Parsing**: Strips markdown formatting automatically

## Testing Gemini Integration

Test project generation:
```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "test-gemini",
    "project_type": "web",
    "assignees": []
  }'
```

Test progress summary:
```bash
curl -X POST http://localhost:8000/api/projects/1/generate-summary
```

## Troubleshooting

### "API key not valid"
- Verify key is correctly copied to `.env`
- Check no extra spaces or quotes
- Ensure `.env` is in the `backend/` directory

### "Resource exhausted"
- You've hit rate limits
- Wait a few minutes
- System will use fallback templates

### JSON parsing errors
- Already handled by the code
- Strips markdown code fences automatically
- Falls back to templates if parsing fails

## Switching Back to OpenAI (If Needed)

If you want to use OpenAI instead:

1. Update `requirements.txt`:
```
openai==1.10.0
```

2. Update `llm_service.py` imports:
```python
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")
```

3. Update `.env`:
```
OPENAI_API_KEY=sk-your_key_here
```

## Performance Notes

- **Gemini Pro**: ~3-8 seconds for project generation
- **Gemini Pro**: ~2-5 seconds for progress summaries
- Both well under the 20-second timeout
- Responses are high quality and consistent

## Comparison: Gemini vs OpenAI

| Feature | Gemini Pro | GPT-3.5-turbo |
|---------|-----------|---------------|
| Cost | Free tier available | Paid only |
| Speed | 3-8s | 2-5s |
| Quality | Excellent | Excellent |
| JSON Output | Good (needs cleanup) | Very good |
| Rate Limits | 60/min | Varies by tier |

For this project automation system, **Gemini Pro is an excellent choice** with its free tier and solid performance.


