"""FastAPI v1 router — all endpoints."""
import logging
import os
import uuid
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import EMOTIONS_MAP, get_settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.models.models import EmotionStat, Prediction, User
from app.db.session import get_db
from app.ml.predictor import EmotionPredictor
from app.ml.trainer import ModelTrainer
from app.schemas.schemas import (
    DashboardStats,
    ModelInfoOut,
    PredictionOut,
    TokenResponse,
    TrainRequest,
    UserOut,
    UserRegister,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# ── Singleton predictor (loaded once at startup) ───────────────────────────────
_predictor: Optional[EmotionPredictor] = None


def get_predictor() -> EmotionPredictor:
    global _predictor
    if _predictor is None:
        _predictor = EmotionPredictor(settings.models_dir, n_mfcc=settings.N_MFCC)
    return _predictor


# ── Optional auth dependency ───────────────────────────────────────────────────

async def get_current_user_optional(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None
    from app.core.security import decode_token
    email = decode_token(token)
    if not email:
        return None
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await get_current_user_optional(token, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/", tags=["Health"])
async def root():
    return {"message": "EchoEmotion API", "version": settings.APP_VERSION, "docs": "/docs"}


@router.get("/health", tags=["Health"])
async def health_check():
    pred = get_predictor()
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "model_loaded": pred.is_loaded(),
    }


# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/auth/register", response_model=UserOut, tags=["Auth"])
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    exists = await db.execute(select(User).where(User.email == payload.email))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered.")
    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.flush()
    return user


@router.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token, user_id=str(user.id), username=user.username)


@router.get("/auth/me", response_model=UserOut, tags=["Auth"])
async def me(current_user: User = Depends(get_current_user)):
    return current_user


# ══════════════════════════════════════════════════════════════════════════════
# EMOTIONS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/emotions", tags=["Emotions"])
async def list_emotions():
    return {
        "all_emotions": list(EMOTIONS_MAP.values()),
        "observed_emotions": settings.OBSERVED_EMOTIONS,
        "emoji_map": {
            "calm": "😌", "happy": "😄", "fearful": "😨",
            "disgust": "🤢", "angry": "😠", "sad": "😢",
            "neutral": "😐", "surprised": "😲",
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# PREDICTION
# ══════════════════════════════════════════════════════════════════════════════

ALLOWED_EXTENSIONS = set(settings.ALLOWED_AUDIO_EXTENSIONS)
MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@router.post("/predict", response_model=PredictionOut, tags=["Prediction"])
async def predict(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    # ── Extension check ────────────────────────────────────────────────────────
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '.{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    # ── Size check ─────────────────────────────────────────────────────────────
    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit.")
    if len(contents) == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    # ── Save temp file ─────────────────────────────────────────────────────────
    tmp_name = f"{uuid.uuid4().hex}_{file.filename}"
    tmp_path = settings.upload_folder / tmp_name
    try:
        tmp_path.write_bytes(contents)

        # Audio integrity check
        try:
            import soundfile as sf
            info = sf.info(str(tmp_path))
            duration = info.duration
            if duration < 0.1:
                raise HTTPException(status_code=422, detail="Audio is too short (< 0.1 s).")
            if duration > 120:
                raise HTTPException(status_code=422, detail="Audio exceeds 120 s limit.")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Cannot read audio: {exc}")

        # ── Run prediction ─────────────────────────────────────────────────────
        predictor = get_predictor()
        if not predictor.is_loaded():
            raise HTTPException(status_code=503, detail="Model not trained yet. POST /api/v1/train first.")

        result = predictor.predict(tmp_path)

        # ── Persist to DB ──────────────────────────────────────────────────────
        row = Prediction(
            user_id=current_user.id if current_user else None,
            filename=file.filename or "unknown",
            file_size_bytes=len(contents),
            audio_duration_s=round(duration, 2),
            predicted_emotion=result["predicted_emotion"],
            confidence=result["confidence"],
            all_probabilities=result["all_probabilities"],
        )
        db.add(row)

        # Update aggregated emotion stats
        stat_res = await db.execute(
            select(EmotionStat).where(EmotionStat.emotion == result["predicted_emotion"])
        )
        stat = stat_res.scalar_one_or_none()
        if stat is None:
            stat = EmotionStat(emotion=result["predicted_emotion"], total_count=1, avg_confidence=result["confidence"])
            db.add(stat)
        else:
            new_avg = (stat.avg_confidence * stat.total_count + result["confidence"]) / (stat.total_count + 1)
            stat.total_count += 1
            stat.avg_confidence = round(new_avg, 2)

        await db.flush()

        return PredictionOut(
            id=row.id,
            filename=row.filename,
            predicted_emotion=result["predicted_emotion"],
            confidence=result["confidence"],
            all_probabilities=result["all_probabilities"],
            audio_duration_s=round(duration, 2),
            created_at=row.created_at,
        )

    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# MODEL INFO & METRICS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/model-info", response_model=ModelInfoOut, tags=["Model"])
async def model_info():
    info = get_predictor().get_info()
    if not info.get("loaded"):
        raise HTTPException(status_code=404, detail="No trained model found.")
    return ModelInfoOut(**info)


@router.get("/metrics", tags=["Model"])
async def get_metrics():
    metrics = get_predictor().get_metrics()
    if metrics is None:
        raise HTTPException(status_code=404, detail="No metrics available — train the model first.")
    return metrics


# ══════════════════════════════════════════════════════════════════════════════
# TRAINING
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/train", tags=["Training"])
async def train_model(payload: TrainRequest):
    dataset_path = settings.DATASET_PATH
    if not dataset_path.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"Dataset directory '{dataset_path}' not found. "
                   "Download RAVDESS and place Actor_* folders there.",
        )
    wav_files = list(dataset_path.glob("Actor_*/*.wav"))
    if not wav_files:
        raise HTTPException(status_code=404, detail="No WAV files found in dataset directory.")

    trainer = ModelTrainer(
        dataset_path=dataset_path,
        models_dir=settings.models_dir,
        emotions_map=EMOTIONS_MAP,
        n_mfcc=settings.N_MFCC,
    )
    result = trainer.train(
        observed_emotions=payload.observed_emotions,
        test_size=payload.test_size,
        cv_folds=payload.cv_folds,
        compare_models=payload.compare_models,
    )

    # Reload predictor with new model
    get_predictor().reload()
    return result


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/dashboard", tags=["Dashboard"])
async def dashboard(db: AsyncSession = Depends(get_db)):
    total_res = await db.execute(select(func.count()).select_from(Prediction))
    total = total_res.scalar() or 0

    dist_res = await db.execute(
        select(Prediction.predicted_emotion, func.count().label("cnt"))
        .group_by(Prediction.predicted_emotion)
    )
    distribution = {row.predicted_emotion: row.cnt for row in dist_res}

    avg_res = await db.execute(select(func.avg(Prediction.confidence)))
    avg_conf = round(float(avg_res.scalar() or 0), 2)

    recent_res = await db.execute(
        select(Prediction).order_by(Prediction.created_at.desc()).limit(10)
    )
    recent = [
        PredictionOut(
            id=r.id,
            filename=r.filename,
            predicted_emotion=r.predicted_emotion,
            confidence=r.confidence,
            all_probabilities=r.all_probabilities or {},
            audio_duration_s=r.audio_duration_s,
            created_at=r.created_at,
        )
        for r in recent_res.scalars()
    ]

    return DashboardStats(
        total_predictions=total,
        emotion_distribution=distribution,
        avg_confidence=avg_conf,
        recent_predictions=recent,
    )
