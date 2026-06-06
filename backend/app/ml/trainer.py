"""
Multi-model training pipeline.

Trains and compares:
  - MLPClassifier
  - Random Forest
  - SVM (RBF kernel)
  - XGBoost
  - LightGBM

Automatically selects the best model by weighted F1 score,
then persists it along with the scaler and label encoder.
"""
import glob
import json
import logging
import os
import pickle
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC

from app.ml.feature_extractor import extract_features

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Model catalogue
# ──────────────────────────────────────────────────────────────────────────────

def _build_candidates() -> Dict[str, object]:
    """Return a dict of {name: unfitted_estimator} to compare."""
    candidates: Dict[str, object] = {
        "MLP": MLPClassifier(
            alpha=0.01,
            batch_size=256,
            epsilon=1e-8,
            hidden_layer_sizes=(300, 150),
            learning_rate="adaptive",
            max_iter=500,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1,
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_split=2,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced",
        ),
        "SVM": SVC(
            kernel="rbf",
            C=10,
            gamma="scale",
            probability=True,
            random_state=42,
        ),
    }

    try:
        import xgboost as xgb  # noqa: F401
        candidates["XGBoost"] = xgb.XGBClassifier(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=42,
            n_jobs=-1,
        )
    except ImportError:
        logger.warning("XGBoost not installed – skipping.")

    try:
        import lightgbm as lgb  # noqa: F401
        candidates["LightGBM"] = lgb.LGBMClassifier(
            n_estimators=300,
            learning_rate=0.05,
            num_leaves=63,
            random_state=42,
            n_jobs=-1,
            verbose=-1,
        )
    except ImportError:
        logger.warning("LightGBM not installed – skipping.")

    return candidates


# ──────────────────────────────────────────────────────────────────────────────
# Trainer class
# ──────────────────────────────────────────────────────────────────────────────

class ModelTrainer:
    def __init__(
        self,
        dataset_path: str | Path,
        models_dir: str | Path,
        emotions_map: Dict[str, str],
        n_mfcc: int = 40,
    ):
        self.dataset_path = Path(dataset_path)
        self.models_dir = Path(models_dir)
        self.emotions_map = emotions_map
        self.n_mfcc = n_mfcc

        self.models_dir.mkdir(parents=True, exist_ok=True)

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

    def train(
        self,
        observed_emotions: List[str],
        test_size: float = 0.25,
        cv_folds: int = 5,
        compare_models: bool = True,
    ) -> dict:
        """
        Full training pipeline.

        Returns
        -------
        dict  Comprehensive training report including per-model comparison,
              best model info, evaluation metrics and confusion matrix.
        """
        logger.info("Loading dataset from %s …", self.dataset_path)
        X_raw, y_raw = self._load_data(observed_emotions)

        if len(X_raw) == 0:
            raise ValueError(
                f"No samples for emotions {observed_emotions}. "
                "Check DATASET_PATH and RAVDESS folder structure."
            )

        X = np.array(X_raw, dtype=np.float32)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y_raw, test_size=test_size, random_state=42, stratify=y_raw
        )

        # Fit scaler and label encoder on training set only
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        le = LabelEncoder()
        y_train_enc = le.fit_transform(y_train)
        y_test_enc = le.transform(y_test)

        # ── Model comparison ───────────────────────────────────────────────────
        comparison: Dict[str, dict] = {}
        best_name: str = "MLP"
        best_f1: float = -1.0
        best_model = None

        candidates = _build_candidates() if compare_models else {"MLP": _build_candidates()["MLP"]}

        for name, clf in candidates.items():
            logger.info("Training %s …", name)
            t0 = time.time()
            clf.fit(X_train_s, y_train_enc)
            elapsed = round(time.time() - t0, 2)

            y_pred_enc = clf.predict(X_test_s)
            y_pred = le.inverse_transform(y_pred_enc)
            y_true = le.inverse_transform(y_test_enc)

            acc = accuracy_score(y_true, y_pred)
            f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
            report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)

            # Cross-validation on training set
            cv_scores = cross_val_score(
                clf, X_train_s, y_train_enc,
                cv=StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42),
                scoring="f1_weighted",
                n_jobs=-1,
            )

            comparison[name] = {
                "accuracy": round(acc * 100, 2),
                "f1_weighted": round(f1, 4),
                "cv_f1_mean": round(float(cv_scores.mean()), 4),
                "cv_f1_std": round(float(cv_scores.std()), 4),
                "training_time_s": elapsed,
                "classification_report": report,
            }

            logger.info(
                "%s — acc=%.2f%%  f1=%.4f  cv_f1=%.4f±%.4f  (%.1fs)",
                name, acc * 100, f1, cv_scores.mean(), cv_scores.std(), elapsed,
            )

            if f1 > best_f1:
                best_f1 = f1
                best_name = name
                best_model = clf
                y_best_true, y_best_pred = y_true, y_pred

        # ── Confusion matrix for best model ───────────────────────────────────
        cm = confusion_matrix(y_best_true, y_best_pred, labels=le.classes_).tolist()

        # ── Persist ────────────────────────────────────────────────────────────
        self._save(best_model, scaler, le)

        result = {
            "best_model": best_name,
            "best_f1_weighted": round(best_f1, 4),
            "best_accuracy": comparison[best_name]["accuracy"],
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "observed_emotions": observed_emotions,
            "n_features": X_train.shape[1],
            "model_comparison": comparison,
            "confusion_matrix": {
                "labels": le.classes_.tolist(),
                "matrix": cm,
            },
        }

        # Cache metrics to disk for /metrics endpoint
        with open(self.metrics_path, "w") as f:
            json.dump(result, f, indent=2)

        logger.info("Best model: %s (F1=%.4f)", best_name, best_f1)
        return result

    # ── Private helpers ────────────────────────────────────────────────────────

    def _load_data(self, observed_emotions: List[str]) -> Tuple[List, List]:
        X, y = [], []
        pattern = str(self.dataset_path / "Actor_*" / "*.wav")
        files = glob.glob(pattern)

        if not files:
            raise FileNotFoundError(f"No WAV files at: {pattern}")

        skipped = 0
        for fp in files:
            fname = os.path.basename(fp)
            parts = fname.split("-")
            if len(parts) < 3:
                continue
            emotion = self.emotions_map.get(parts[2])
            if emotion is None or emotion not in observed_emotions:
                continue
            try:
                feats = extract_features(fp, n_mfcc=self.n_mfcc)
                X.append(feats)
                y.append(emotion)
            except Exception as exc:
                logger.warning("Skipping %s: %s", fname, exc)
                skipped += 1

        logger.info("Loaded %d samples (%d skipped)", len(X), skipped)
        return X, y

    def _save(self, model, scaler, le) -> None:
        for obj, path in [
            (model, self.model_path),
            (scaler, self.scaler_path),
            (le, self.label_encoder_path),
        ]:
            with open(path, "wb") as f:
                pickle.dump(obj, f, protocol=5)
        logger.info("Artefacts persisted to %s", self.models_dir)
