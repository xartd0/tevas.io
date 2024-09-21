from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from ..base import Base  


class UserTeamLink(Base):
    __tablename__ = "user_team_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Integer, nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)

    # Связи
    user = relationship("User", back_populates="user_team_links")
    team = relationship("Team", back_populates="user_team_links")

class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(50), nullable=False)
    status_id = Column(Integer, nullable=False, default=1)
    created_dt = Column(DateTime(timezone=True), default=datetime.now)
    updated_dt = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

    # Связи
    user_team_links = relationship("UserTeamLink", back_populates="team", cascade="all, delete-orphan")
    # team_project_links = relationship("TeamProjectLink", back_populates="team", cascade="all, delete-orphan")
