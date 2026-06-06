"""SQLAlchemy ORM models."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, JSON, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    predictions = relationship("Prediction", back_populates="user", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    audio_duration_s = Column(Float, nullable=True)

    predicted_emotion = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    all_probabilities = Column(JSON, nullable=True)
    model_version = Column(String(50), nullable=True, default="v1")

    created_at = Column(DateTime(timezone=True), default=_now)

    user = relationship("User", back_populates="predictions")

    def __repr__(self) -> str:
        return f"<Prediction {self.predicted_emotion} ({self.confidence:.1f}%)>"


class EmotionStat(Base):
    __tablename__ = "emotion_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    emotion = Column(String(50), nullable=False, unique=True, index=True)
    total_count = Column(Integer, default=0)
    avg_confidence = Column(Float, default=0.0)
    last_updated = Column(DateTime(timezone=True), default=_now, onupdate=_now)


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(50), nullable=False, unique=True)
    algorithm = Column(String(100), nullable=False)
    accuracy = Column(Float, nullable=False)
    metrics = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=_now)
    notes = Column(Text, nullable=True)
