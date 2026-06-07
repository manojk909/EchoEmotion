"""Audio feature extraction: MFCC + Chroma + Mel-spectrogram.

Memory-optimised for Render free tier (512 MB RAM).
Key changes vs previous version:
  - res_type='kaiser_fast'  → 10x less memory than default 'kaiser_best'
  - Clip audio to 10 s max before feature extraction
  - Explicit del + gc.collect() after heavy intermediate arrays
  - float32 throughout — never upcasts to float64
"""
import gc
import logging
import time
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Render free tier: clip audio to this many seconds before processing.
# RAVDESS files are 3-5 s, so this only affects unusually long uploads.
MAX_AUDIO_SECONDS = 10


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
    Extract a 1-D float32 feature vector (default 180-dim: 40+12+128).

    Memory budget on 512 MB Render free tier
    ─────────────────────────────────────────
    librosa import   ~80 MB
    sklearn model    ~20 MB
    audio array      ~2 MB  (3 s × 22050 Hz × 4 bytes)
    STFT             ~8 MB  (kaiser_fast)
    mel spectrogram  ~4 MB
    ─────────────────────────────────────────
    Total            ~114 MB  ← well within 512 MB
    """
    import librosa
    import soundfile as sf

    TARGET_SR = 22050   # RAVDESS native sample rate — must match training

    # ── 1. Load audio ──────────────────────────────────────────────────────────
    logger.info("Opening audio file: %s", file_path)
    try:
        with sf.SoundFile(file_path) as sound_file:
            X = sound_file.read(dtype="float32")
            sr = sound_file.samplerate
            logger.info("Loaded via soundfile. shape=%s sr=%s", X.shape, sr)
    except Exception as e:
        logger.warning("soundfile failed (%s) — falling back to librosa", e)
        X, sr = librosa.load(
            file_path,
            sr=TARGET_SR,          # load + resample in one step (saves RAM)
            mono=True,
            res_type="kaiser_fast",
        )
        logger.info("Loaded via librosa. shape=%s sr=%s", X.shape, sr)

    # ── 2. Stereo → mono ──────────────────────────────────────────────────────
    if X.ndim > 1:
        X = X.mean(axis=1).astype(np.float32)

    # ── 3. Clip to MAX_AUDIO_SECONDS ──────────────────────────────────────────
    max_samples = MAX_AUDIO_SECONDS * sr
    if len(X) > max_samples:
        logger.info("Clipping audio from %d to %d samples", len(X), max_samples)
        X = X[:max_samples]

    # ── 4. Resample to TARGET_SR ──────────────────────────────────────────────
    # Use kaiser_fast — same quality for speech, ~10x less peak memory than
    # the default kaiser_best.
    if sr != TARGET_SR:
        logger.info("Resampling %s Hz → %s Hz (kaiser_fast)", sr, TARGET_SR)
        X = librosa.resample(
            X, orig_sr=sr, target_sr=TARGET_SR, res_type="kaiser_fast"
        )
        sr = TARGET_SR
        logger.info("Resample complete. new_shape=%s", X.shape)

    # ── 5. Pre-compute STFT once (shared by MFCC and Chroma) ─────────────────
    result = np.array([], dtype=np.float32)
    stft = None

    if use_chroma or use_mfcc:
        logger.info("Computing STFT…")
        stft = np.abs(librosa.stft(X)).astype(np.float32)
        logger.info("STFT shape=%s", stft.shape)

    # ── 6. MFCC ───────────────────────────────────────────────────────────────
    if use_mfcc:
        t0 = time.time()
        logger.info("Computing MFCC (n_mfcc=%d)…", n_mfcc)
        mfcc_raw = librosa.feature.mfcc(
            S=librosa.power_to_db(stft ** 2),  # reuse STFT — avoids recompute
            sr=sr,
            n_mfcc=n_mfcc,
        )
        mfccs = np.mean(mfcc_raw.T, axis=0).astype(np.float32)
        del mfcc_raw
        gc.collect()
        logger.info("MFCC done in %.3fs shape=%s", time.time() - t0, mfccs.shape)
        result = np.hstack((result, mfccs))

    # ── 7. Chroma ─────────────────────────────────────────────────────────────
    if use_chroma:
        t0 = time.time()
        logger.info("Computing Chroma…")
        chroma_raw = librosa.feature.chroma_stft(S=stft, sr=sr)
        chroma = np.mean(chroma_raw.T, axis=0).astype(np.float32)
        del chroma_raw
        gc.collect()
        logger.info("Chroma done in %.3fs shape=%s", time.time() - t0, chroma.shape)
        result = np.hstack((result, chroma))

    # Free STFT — no longer needed
    del stft
    gc.collect()

    # ── 8. Mel Spectrogram ────────────────────────────────────────────────────
    if use_mel:
        t0 = time.time()
        logger.info("Computing Mel spectrogram…")
        mel_raw = librosa.feature.melspectrogram(y=X, sr=sr)
        mel = np.mean(mel_raw.T, axis=0).astype(np.float32)
        del mel_raw, X
        gc.collect()
        logger.info("Mel done in %.3fs shape=%s", time.time() - t0, mel.shape)
        result = np.hstack((result, mel))

    logger.info("Feature extraction complete. vector_size=%d", len(result))
    return result


def feature_dim(
    use_mfcc: bool = True,
    use_chroma: bool = True,
    use_mel: bool = True,
    n_mfcc: int = 40,
) -> int:
    return (
        (n_mfcc if use_mfcc else 0)
        + (12 if use_chroma else 0)
        + (128 if use_mel else 0)
    )


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
