from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime
from ..base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    login = Column(String(50), unique=True, nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    status_id = Column(Integer, default=0)
    last_login_ip = Column(String(20))
    last_login_dt = Column(DateTime)
    created_dt = Column(DateTime, default=datetime.now)
    updated_dt = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Связь с RefreshToken
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    verification_codes = relationship("UserVerificationCode", back_populates="user", cascade="all, delete-orphan")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    value = Column(String(512), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    ttl_sec = Column(BigInteger, nullable=False)
    created_dt = Column(DateTime, default=datetime.now)
    updated_dt = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="refresh_tokens")


class UserVerificationCode(Base):
    __tablename__ = "user_verification_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email = Column(String(50), nullable=True)
    code = Column(String(6), nullable=False)
    created_dt = Column(DateTime, default=datetime.now)
    updated_dt = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="verification_codes")

