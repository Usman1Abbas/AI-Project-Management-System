import os
import google.generativeai as genai
from typing import Dict
import json

# Configure Gemini API key from environment
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_project_structure(project_name: str, project_type: str = "dotnet", requirements: str = None) -> Dict:
    """
    Generate a minimal runnable .NET project scaffold using Gemini API.
    """
    requirements_section = f"\n\n### Custom Requirements:\n{requirements}" if requirements else ""
    
    prompt = f"""You are an expert .NET scaffolder. Create a **minimal runnable .NET project skeleton** named '{project_name}'.

Respond **only** with a valid JSON:
{{
  "directory_structure": ["path/to/file.ext"],
  "files": {{"path/to/file.ext": "file content as string"}}
}}

### Requirements:
- Include folders: Controllers, Models, Services
- Key files: Program.cs, {project_name}.csproj, appsettings.json, README.md
- Sample Controller with one API endpoint (e.g., GET /hello)
- Include .gitignore, Dockerfile, and one test file
- Code must compile in .NET 7
- Use placeholders (// TODO) for future work
- Every path in directory_structure must exist in files

Project: {project_name}{requirements_section}

Output only JSON, no explanations or markdown."""

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(
            prompt,
            generation_config={'temperature': 0.6, 'max_output_tokens': 6000}
        )
        
        text = response.text.strip()
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        text = text[json_start:json_end]

        result = json.loads(text)
        
        print("✅ Successfully generated minimal .NET project structure")
        print(f"Directory count: {len(result.get('directory_structure', []))}")
        print(f"Files count: {len(result.get('files', {}))}")
        print(f"First 5 files: {list(result.get('directory_structure', []))[:5]}")
        
        return result

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print("Raw response snippet:", text[:500])
        raise
    except Exception as e:
        print(f"❌ Error generating .NET project: {e}")
        import traceback
        traceback.print_exc()
        return {
            "directory_structure": ["Program.cs", "README.md", f"{project_name}.csproj"],
            "files": {
                "Program.cs": f"// {project_name} main program\nusing System;\n\nclass Program {{\n    static void Main() {{\n        Console.WriteLine(\"Hello from {project_name}\");\n    }}\n}}\n",
                "README.md": f"# {project_name}\n\nA minimal .NET project.\n\n## Setup\n1. Clone\n2. Restore\n3. Run\n",
                f"{project_name}.csproj": "<Project Sdk=\"Microsoft.NET.Sdk.Web\">\n  <PropertyGroup>\n    <TargetFramework>net7.0</TargetFramework>\n  </PropertyGroup>\n</Project>"
            }
        }


def generate_progress_summary(readme_content: str, commits: list) -> str:
    commit_data = "\n".join([
        f"- {c['author']}: {c['message']} (files: {', '.join(c['files'])})"
        for c in commits[-10:]
    ])
    
    prompt = f"""Summarize this .NET project progress.

README:
{readme_content[:800]}

Recent Commits:
{commit_data}

Output a short report with:
1. 2–3 sentence overall progress summary
2. Key developer contributions (bullet points)
3. 3 suggested next steps

Keep it brief (<200 words)."""

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(
            prompt,
            generation_config={'temperature': 0.5, 'max_output_tokens': 800}
        )
        return response.text.strip()
    except Exception as e:
        return f"Progress Summary:\n\nCommits: {len(commits)} | Contributors: {len(set(c['author'] for c in commits))}\nError generating summary: {str(e)}"
