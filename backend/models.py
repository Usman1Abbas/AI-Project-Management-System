from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
from database import Base

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    repo_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    webhook_secret = Column(String, nullable=True)
    requirements = Column(Text, nullable=True)
    
    contributions = relationship("Contribution", back_populates="project")
    summaries = relationship("Summary", back_populates="project")

class Contribution(Base):
    __tablename__ = "contributions"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    author = Column(String, nullable=False)
    email = Column(String, nullable=False)
    commit_count = Column(Integer, default=1)
    
    project = relationship("Project", back_populates="contributions")

class Summary(Base):
    __tablename__ = "summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    summary_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="summaries")

class ProjectCreate(BaseModel):
    project_name: str
    project_type: str
    assignees: List[str]
    teams_webhook: Optional[str] = None
    requirements: Optional[str] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    type: str
    repo_url: str
    created_at: datetime
    requirements: Optional[str] = None
    
    class Config:
        from_attributes = True

