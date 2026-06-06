from sklearn.neural_network import MLPClassifier
"""Load persisted EchoEmotion model and run inference."""
import json
import logging
import pickle
from pathlib import Path
from typing import Optional

import numpy as np

from app.ml.feature_extractor import extract_features

logger = logging.getLogger(__name__)


class EmotionPredictor:
    def __init__(self, models_dir: str | Path, n_mfcc: int = 40):
        self.models_dir = Path(models_dir)
        self.n_mfcc = n_mfcc

        self._model = None
        self._scaler = None
        self._label_encoder = None

        self._try_load()

    # ── Paths ──────────────────────────────────────────────────────────────────

    @property
    def model_path(self) -> Path:
        return self.models_dir / "best_model.pkl"

    @property
    def scaler_path(self) -> Path:
        return self.models_dir / "scaler.pkl"

    @property
    def label_encoder_path(self) -> Path:
        return self.models_dir / "label_encoder.pkl"

    @property
    def metrics_path(self) -> Path:
        return self.models_dir / "metrics.json"

    # ── Public API ─────────────────────────────────────────────────────────────

    def is_loaded(self) -> bool:
        return all(x is not None for x in [self._model, self._scaler, self._label_encoder])

    def reload(self) -> None:
        """Force reload from disk (after re-training)."""
        self._model = self._scaler = self._label_encoder = None
        self._try_load()

    def predict(self, file_path: str | Path) -> dict:
        """
        Predict emotion from an audio file.

        Returns
        -------
        dict  Keys: predicted_emotion, confidence, all_probabilities
        """
        if not self.is_loaded():
            raise RuntimeError("Model not loaded. Train first via POST /api/v1/train.")

        features = extract_features(str(file_path), n_mfcc=self.n_mfcc)
        X = self._scaler.transform(features.reshape(1, -1))

        proba = self._model.predict_proba(X)[0]
        classes = self._label_encoder.classes_

        pred_idx = int(np.argmax(proba))
        predicted_emotion = classes[pred_idx]
        confidence = round(float(proba[pred_idx]) * 100, 2)

        all_probs = {
            emotion: round(float(p) * 100, 2)
            for emotion, p in zip(classes, proba)
        }

        return {
            "predicted_emotion": predicted_emotion,
            "confidence": confidence,
            "all_probabilities": all_probs,
        }


    def get_info(self) -> dict:
        """Return metadata about the loaded model artefacts."""
        if not self.is_loaded():
            return {"loaded": False}

        info = {
            "loaded": True,
            "emotions": self._label_encoder.classes_.tolist(),
            "n_features": getattr(self._model, "n_features_in_", "unknown"),
            "algorithm": type(self._model).__name__,
        }

        # Only add MLP-specific information for MLP models
        if isinstance(self._model, MLPClassifier):
            info["n_iter"] = self._model.n_iter_
            info["loss"] = round(self._model.loss_, 6)
            info["hidden_layer_sizes"] = list(self._model.hidden_layer_sizes)

        return info

    def get_metrics(self) -> Optional[dict]:
        """Return cached training metrics (from metrics.json)."""
        if self.metrics_path.exists():
            with open(self.metrics_path) as f:
                return json.load(f)
        return None

    # ── Private ────────────────────────────────────────────────────────────────

    def _try_load(self) -> None:
        paths = [self.model_path, self.scaler_path, self.label_encoder_path]
        if not all(p.exists() for p in paths):
            logger.info("Model artefacts not found — training required.")
            return
        try:
            with open(self.model_path, "rb") as f:
                self._model = pickle.load(f)
            with open(self.scaler_path, "rb") as f:
                self._scaler = pickle.load(f)
            with open(self.label_encoder_path, "rb") as f:
                self._label_encoder = pickle.load(f)
            logger.info("Model loaded: %s", type(self._model).__name__)
        except Exception as exc:
            logger.error("Failed to load model: %s", exc)
            self._model = self._scaler = self._label_encoder = None
