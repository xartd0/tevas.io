from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, UUID, Boolean, BigInteger
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

    def __repr__(self):
        return f"<UserTeamLink(id={self.id}, user_id={self.user_id}, role={self.role}, team_id={self.team_id})>"

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

    def __repr__(self):
        return f"<Team(id={self.id}, title={self.title}, status_id={self.status_id})>"


class Invitation(Base):
    __tablename__ = 'invitations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), nullable=False)
    role_id = Column(Integer, nullable=False)
    inviting_user_id = Column(UUID(as_uuid=True), nullable=False)
    is_active = Column(Boolean, default=True)
    users_accepted = Column(Integer, default=0)
    ttl_sec = Column(BigInteger, nullable=False)
    created_dt = Column(DateTime(timezone=True), default=datetime.now)

    def __repr__(self):
        return f"<Invitation(id={self.id}, team_id={self.team_id}, role_id={self.role_id}, " \
               f"inviting_user_id={self.inviting_user_id}, is_active={self.is_active})>"
