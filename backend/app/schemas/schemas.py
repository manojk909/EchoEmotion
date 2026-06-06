"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str


class UserOut(BaseModel):
    id: UUID
    email: str
    username: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Prediction ─────────────────────────────────────────────────────────────────

class PredictionOut(BaseModel):
    id: Optional[UUID] = None
    filename: str
    predicted_emotion: str
    confidence: float
    all_probabilities: Dict[str, float]
    audio_duration_s: Optional[float] = None
    model_version: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Model info ────────────────────────────────────────────────────────────────

class ModelInfoOut(BaseModel):
    loaded: bool
    algorithm: Optional[str] = None
    emotions: Optional[List[str]] = None
    n_features: Optional[int] = None
    n_iter: Optional[int] = None
    loss: Optional[float] = None


class TrainRequest(BaseModel):
    observed_emotions: List[str] = ["calm", "happy", "fearful", "disgust"]
    test_size: float = Field(default=0.25, ge=0.05, le=0.5)
    cv_folds: int = Field(default=5, ge=2, le=10)
    compare_models: bool = True

    @field_validator("observed_emotions")
    @classmethod
    def at_least_two(cls, v):
        if len(v) < 2:
            raise ValueError("Need at least 2 emotions.")
        return v


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_predictions: int
    emotion_distribution: Dict[str, int]
    avg_confidence: float
    recent_predictions: List[PredictionOut]
