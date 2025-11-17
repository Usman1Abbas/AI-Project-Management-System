from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from database import get_db, init_db
from models import Project, Contribution, Summary, ProjectCreate, ProjectResponse
from services.llm_service import generate_project_structure, generate_progress_summary
from services.github_service import create_repository, get_repository_readme
from services.teams_service import send_teams_notification, send_summary_notification
from services.progress_routes import router as progress_router

app = FastAPI(title="Project Automation System")

# Include progress analyzer routes
app.include_router(progress_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(project_data: ProjectCreate, db: Session = Depends(get_db)):
    try:
        project_structure = generate_project_structure(
            project_data.project_name,
            project_data.project_type,
            project_data.requirements
        )
        
        github_result = create_repository(
            project_data.project_name,
            project_structure,
            project_data.assignees
        )
        
        db_project = Project(
            name=project_data.project_name,
            type=project_data.project_type,
            repo_url=github_result["repo_url"],
            requirements=project_data.requirements
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        
        if project_data.teams_webhook:
            send_teams_notification(
                project_data.teams_webhook,
                project_data.project_name,
                github_result["repo_url"],
                project_data.assignees
            )
        
        return db_project
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/github-webhook")
async def github_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        
        if "commits" not in payload or "repository" not in payload:
            return {"status": "ignored"}
        
        repo_url = payload["repository"]["html_url"]
        
        project = db.query(Project).filter(Project.repo_url == repo_url).first()
        if not project:
            return {"status": "project not found"}
        
        for commit in payload["commits"]:
            author = commit["author"]["name"]
            email = commit["author"]["email"]
            
            contribution = db.query(Contribution).filter(
                Contribution.project_id == project.id,
                Contribution.email == email
            ).first()
            
            if contribution:
                contribution.commit_count += 1
            else:
                contribution = Contribution(
                    project_id=project.id,
                    author=author,
                    email=email,
                    commit_count=1
                )
                db.add(contribution)
        
        db.commit()
        return {"status": "success", "commits_processed": len(payload["commits"])}
    
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/projects/{project_id}/summary")
async def get_project_summary(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    latest_summary = db.query(Summary).filter(
        Summary.project_id == project_id
    ).order_by(Summary.timestamp.desc()).first()
    
    if latest_summary:
        return {
            "project_name": project.name,
            "summary": latest_summary.summary_text,
            "timestamp": latest_summary.timestamp
        }
    
    return {"project_name": project.name, "summary": "No summary available yet", "timestamp": None}

@app.post("/api/projects/{project_id}/generate-summary")
async def generate_summary(project_id: int, teams_webhook: str = None, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        readme_content = get_repository_readme(project.repo_url)
        
        contributions = db.query(Contribution).filter(
            Contribution.project_id == project_id
        ).all()
        
        commits_data = [
            {
                "author": c.author,
                "message": f"{c.commit_count} commits",
                "files": ["multiple files"]
            }
            for c in contributions
        ]
        
        summary_text = generate_progress_summary(readme_content, commits_data)
        
        db_summary = Summary(
            project_id=project_id,
            summary_text=summary_text
        )
        db.add(db_summary)
        db.commit()
        
        if teams_webhook:
            send_summary_notification(teams_webhook, project.name, summary_text)
        
        return {
            "project_name": project.name,
            "summary": summary_text,
            "timestamp": db_summary.timestamp
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects")
async def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return projects

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

