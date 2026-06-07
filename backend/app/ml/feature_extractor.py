"""Audio feature extraction: MFCC + Chroma + Mel-spectrogram."""
import logging
import time
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


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
    Extract a 1-D feature vector from an audio file.

    Feature dimensions (defaults):
      MFCC  : 40   (n_mfcc)
      Chroma: 12
      Mel   : 128
    Total   : 180  ← must match what the model was trained on

    Parameters
    ----------
    file_path   : Path to audio file (WAV / MP3 / OGG / FLAC / M4A).
    use_mfcc    : Include MFCC features.
    use_chroma  : Include Chroma STFT features.
    use_mel     : Include Mel-spectrogram features.
    n_mfcc      : Number of MFCC coefficients (default 40).
    sample_rate : Target sample rate for resampling; None = keep native.

    Returns
    -------
    np.ndarray  1-D float32 feature vector.
    """
    import librosa
    import soundfile as sf

    # ── 1. Load audio ──────────────────────────────────────────────────────────
    logger.info("Opening audio file: %s", file_path)

    try:
        with sf.SoundFile(file_path) as sound_file:
            X = sound_file.read(dtype="float32")
            sr = sound_file.samplerate
            logger.info("Loaded via soundfile. shape=%s sr=%s", X.shape, sr)
    except Exception as e:
        logger.warning("soundfile failed (%s) — falling back to librosa", e)
        X, sr = librosa.load(file_path, sr=sample_rate, mono=True)
        logger.info("Loaded via librosa. shape=%s sr=%s", X.shape, sr)

    # ── 2. Stereo → mono ──────────────────────────────────────────────────────
    if X.ndim > 1:
        X = X.mean(axis=1)
        logger.info("Converted stereo → mono")

    # ── 3. Resample if needed ─────────────────────────────────────────────────
    # IMPORTANT: resample to 22050 Hz so features match training conditions.
    # The model was trained on RAVDESS files natively at 22050 Hz.
    TARGET_SR = 22050
    if sr != TARGET_SR:
        logger.info("Resampling %s Hz → %s Hz", sr, TARGET_SR)
        X = librosa.resample(X, orig_sr=sr, target_sr=TARGET_SR)
        sr = TARGET_SR
        logger.info("Resample complete")

    result = np.array([], dtype=np.float32)

    # ── 4. MFCC ───────────────────────────────────────────────────────────────
    if use_mfcc:
        logger.info("Computing MFCC (n_mfcc=%d)…", n_mfcc)
        t0 = time.time()
        mfcc_raw = librosa.feature.mfcc(y=X, sr=sr, n_mfcc=n_mfcc)
        mfccs = np.mean(mfcc_raw.T, axis=0).astype(np.float32)
        logger.info("MFCC done in %.3fs  shape=%s", time.time() - t0, mfccs.shape)
        result = np.hstack((result, mfccs))

    # ── 5. Chroma ─────────────────────────────────────────────────────────────
    if use_chroma:
        logger.info("Computing Chroma STFT…")
        t0 = time.time()
        stft = np.abs(librosa.stft(X))
        chroma = np.mean(
            librosa.feature.chroma_stft(S=stft, sr=sr).T, axis=0
        ).astype(np.float32)
        logger.info("Chroma done in %.3fs  shape=%s", time.time() - t0, chroma.shape)
        result = np.hstack((result, chroma))

    # ── 6. Mel Spectrogram ────────────────────────────────────────────────────
    if use_mel:
        logger.info("Computing Mel spectrogram…")
        t0 = time.time()
        mel_raw = librosa.feature.melspectrogram(y=X, sr=sr)
        mel = np.mean(mel_raw.T, axis=0).astype(np.float32)
        logger.info("Mel done in %.3fs  shape=%s", time.time() - t0, mel.shape)
        result = np.hstack((result, mel))

    logger.info("Feature extraction complete. vector_size=%d", len(result))
    return result


def feature_dim(
    use_mfcc: bool = True,
    use_chroma: bool = True,
    use_mel: bool = True,
    n_mfcc: int = 40,
) -> int:
    """Return expected feature vector length for the given config."""
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
