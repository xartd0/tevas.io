from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ..base import Base  

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    title = Column(String(50), nullable=False)
    created_dt = Column(DateTime(timezone=True), default=datetime.now)
    updated_dt = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

    parent = relationship("Project", remote_side=[id], backref="children")

class TeamProjectLink(Base):
    __tablename__ = "team_project_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    team = relationship("Team", back_populates="project_links")
    project = relationship("Project", back_populates="team_links")
