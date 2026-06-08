"""
Audio feature extraction — lazy imports for fast startup.

Critical for Render free tier: librosa + numba take 20-40s to JIT-compile
on first import. By importing inside the function (lazy), uvicorn starts
instantly and passes the health check. librosa loads only on the first
actual prediction request.
"""
import gc
import logging
import time
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

MAX_AUDIO_SECONDS = 10   # clip before processing — RAVDESS files are 3-5 s


def extract_features(
    file_path: str,
    *,
    use_mfcc: bool = True,
    use_chroma: bool = True,
    use_mel: bool = True,
    n_mfcc: int = 40,
    sample_rate: Optional[int] = None,
) -> np.ndarray:
    """
    Extract 180-dim float32 feature vector (40 MFCC + 12 Chroma + 128 Mel).

    Imports librosa lazily — inside this function — so the module loads
    at prediction time, not at server startup. This keeps uvicorn startup
    under 5 seconds and prevents health-check timeouts on Render free tier.
    """
    # ── Lazy imports (happen only on first prediction call) ────────────────────
    import librosa          # noqa: PLC0415
    import soundfile as sf  # noqa: PLC0415

    TARGET_SR = 22050  # RAVDESS native rate — must match training

    # ── 1. Load audio ──────────────────────────────────────────────────────────
    logger.info("Opening audio file: %s", file_path)
    try:
        with sf.SoundFile(file_path) as sound_file:
            X = sound_file.read(dtype="float32")
            sr = sound_file.samplerate
            logger.info("Loaded via soundfile. shape=%s sr=%s", X.shape, sr)
    except Exception as e:
        logger.warning("soundfile failed (%s) — falling back to librosa.load", e)
        X, sr = librosa.load(
            file_path, sr=TARGET_SR, mono=True, res_type="kaiser_fast"
        )
        logger.info("Loaded via librosa. shape=%s sr=%s", X.shape, sr)

    # ── 2. Stereo → mono ──────────────────────────────────────────────────────
    if X.ndim > 1:
        X = X.mean(axis=1).astype(np.float32)

    # ── 3. Clip to MAX_AUDIO_SECONDS ──────────────────────────────────────────
    max_samples = int(MAX_AUDIO_SECONDS * sr)
    if len(X) > max_samples:
        logger.info("Clipping audio %d → %d samples", len(X), max_samples)
        X = X[:max_samples]

    # ── 4. Resample to 22050 Hz (kaiser_fast = low RAM) ──────────────────────
    if sr != TARGET_SR:
        logger.info("Resampling %d Hz → %d Hz (kaiser_fast)", sr, TARGET_SR)
        X = librosa.resample(
            X, orig_sr=sr, target_sr=TARGET_SR, res_type="kaiser_fast"
        )
        sr = TARGET_SR
        logger.info("Resample done. shape=%s", X.shape)

    result = np.array([], dtype=np.float32)

    # ── 5. Compute STFT once — shared by MFCC + Chroma ───────────────────────
    stft = None
    if use_mfcc or use_chroma:
        logger.info("Computing STFT…")
        stft = np.abs(librosa.stft(X)).astype(np.float32)

    # ── 6. MFCC ───────────────────────────────────────────────────────────────
    if use_mfcc:
        t0 = time.time()
        mfcc_mat = librosa.feature.mfcc(
            S=librosa.power_to_db(stft ** 2), sr=sr, n_mfcc=n_mfcc
        )
        mfccs = np.mean(mfcc_mat.T, axis=0).astype(np.float32)
        del mfcc_mat
        gc.collect()
        logger.info("MFCC done %.2fs  shape=%s", time.time() - t0, mfccs.shape)
        result = np.hstack((result, mfccs))

    # ── 7. Chroma ─────────────────────────────────────────────────────────────
    if use_chroma:
        t0 = time.time()
        chroma_mat = librosa.feature.chroma_stft(S=stft, sr=sr)
        chroma = np.mean(chroma_mat.T, axis=0).astype(np.float32)
        del chroma_mat
        gc.collect()
        logger.info("Chroma done %.2fs  shape=%s", time.time() - t0, chroma.shape)
        result = np.hstack((result, chroma))

    del stft
    gc.collect()

    # ── 8. Mel Spectrogram ────────────────────────────────────────────────────
    if use_mel:
        t0 = time.time()
        mel_mat = librosa.feature.melspectrogram(y=X, sr=sr)
        mel = np.mean(mel_mat.T, axis=0).astype(np.float32)
        del mel_mat, X
        gc.collect()
        logger.info("Mel done %.2fs  shape=%s", time.time() - t0, mel.shape)
        result = np.hstack((result, mel))

    logger.info("Extraction complete. vector_size=%d", len(result))
    return result


def feature_dim(
    use_mfcc: bool = True,
    use_chroma: bool = True,
    use_mel: bool = True,
    n_mfcc: int = 40,
) -> int:
    return (n_mfcc if use_mfcc else 0) + (12 if use_chroma else 0) + (128 if use_mel else 0)


def feature_names(
    use_mfcc: bool = True,
    use_chroma: bool = True,
    use_mel: bool = True,
    n_mfcc: int = 40,
) -> list:
    names = []
    if use_mfcc:
        names += [f"mfcc_{i}" for i in range(n_mfcc)]
    if use_chroma:
        names += [f"chroma_{i}" for i in range(12)]
    if use_mel:
        names += [f"mel_{i}" for i in range(128)]
    return names
