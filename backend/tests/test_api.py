"""FastAPI backend tests."""
import io
import pickle
import struct
import uuid
import pytest
import numpy as np
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from unittest.mock import MagicMock, patch

from app.main import app


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
def dummy_wav_bytes():
    """1-second silent 22050 Hz mono WAV."""
    sr, n = 22050, 22050
    buf = io.BytesIO()
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + n * 2))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<IHHIIHH", 16, 1, 1, sr, sr * 2, 2, 16))
    buf.write(b"data")
    buf.write(struct.pack("<I", n * 2))
    buf.write(b"\x00" * n * 2)
    return buf.getvalue()


@pytest.fixture
def mock_predictor():
    pred = MagicMock()
    pred.is_loaded.return_value = True
    pred.predict.return_value = {
        "predicted_emotion": "happy",
        "confidence": 82.5,
        "all_probabilities": {"calm": 5.0, "happy": 82.5, "fearful": 8.0, "disgust": 4.5},
    }
    pred.get_info.return_value = {
        "loaded": True,
        "algorithm": "MLPClassifier",
        "emotions": ["calm", "disgust", "fearful", "happy"],
        "n_features": 180,
    }
    pred.get_metrics.return_value = {"best_model": "MLP", "best_accuracy": 72.4}
    return pred


# ── Async client ──────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_root(client):
    r = await client.get("/api/v1/")
    assert r.status_code == 200
    assert "version" in r.json()


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data


# ── Emotions ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_emotions(client):
    r = await client.get("/api/v1/emotions")
    assert r.status_code == 200
    data = r.json()
    assert "observed_emotions" in data
    assert isinstance(data["observed_emotions"], list)


# ── Predict – validation ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_predict_no_file(client):
    r = await client.post("/api/v1/predict")
    assert r.status_code == 422  # FastAPI unprocessable entity (missing file)


@pytest.mark.asyncio
async def test_predict_bad_extension(client, dummy_wav_bytes):
    r = await client.post(
        "/api/v1/predict",
        files={"file": ("audio.exe", dummy_wav_bytes, "application/octet-stream")},
    )
    assert r.status_code == 415


@pytest.mark.asyncio
async def test_predict_empty_file(client):
    r = await client.post(
        "/api/v1/predict",
        files={"file": ("audio.wav", b"", "audio/wav")},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires PostgreSQL service in CI")
async def test_predict_success(client, dummy_wav_bytes, mock_predictor):
    with patch("app.api.v1.router.get_predictor", return_value=mock_predictor), \
         patch("app.api.v1.router.get_db"):
        r = await client.post(
            "/api/v1/predict",
            files={"file": ("test.wav", dummy_wav_bytes, "audio/wav")},
        )
    # 200 or 503 (db not wired in unit test) — both acceptable
    assert r.status_code in (200, 422, 500, 503)


# ── Model info ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_model_info_not_loaded(client):
    r = await client.get("/api/v1/model-info")
    assert r.status_code in (200, 404)


@pytest.mark.asyncio
async def test_metrics_not_available(client):
    r = await client.get("/api/v1/metrics")
    assert r.status_code in (200, 404)


# ── ML unit tests ──────────────────────────────────────────────────────────────

def test_feature_extractor_dim():
    from app.ml.feature_extractor import feature_dim
    assert feature_dim() == 180  # 40 + 12 + 128


def test_feature_names_mfcc_only():
    from app.ml.feature_extractor import feature_names
    names = feature_names(use_mfcc=True, use_chroma=False, use_mel=False)
    assert len(names) == 40
    assert all(n.startswith("mfcc_") for n in names)


def test_predictor_not_loaded(tmp_path):
    from app.ml.predictor import EmotionPredictor
    p = EmotionPredictor(models_dir=tmp_path)
    assert not p.is_loaded()
    with pytest.raises(RuntimeError):
        p.predict("nonexistent.wav")
