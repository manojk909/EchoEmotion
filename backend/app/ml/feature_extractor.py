"""Audio feature extraction: MFCC + Chroma + Mel-spectrogram."""
import logging
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
      MFCC:   40  (n_mfcc)
      Chroma: 12
      Mel:   128
    Total:   180

    Parameters
    ----------
    file_path    : Path to WAV/MP3/OGG/FLAC/M4A file.
    use_mfcc     : Include Mel-Frequency Cepstral Coefficients.
    use_chroma   : Include Chroma STFT features.
    use_mel      : Include Mel-spectrogram features.
    n_mfcc       : Number of MFCC coefficients (default 40).
    sample_rate  : Target sample rate; None = keep native rate.

    Returns
    -------
    np.ndarray : 1-D float32 feature vector.
    """
    import soundfile as sf
    import librosa

    try:
        with sf.SoundFile(file_path) as sound_file:
            X = sound_file.read(dtype="float32")
            sr = sound_file.samplerate
    except Exception:
        # Fallback: librosa can handle more formats (mp3, m4a, etc.)
        X, sr = librosa.load(file_path, sr=sample_rate, mono=True)

    # Stereo → mono
    if X.ndim > 1:
        X = X.mean(axis=1)

    # Resample if target sample rate differs
    if sample_rate and sr != sample_rate:
        X = librosa.resample(X, orig_sr=sr, target_sr=sample_rate)
        sr = sample_rate

    result = np.array([], dtype=np.float32)

    if use_chroma or use_mfcc:
        stft = np.abs(librosa.stft(X))

    if use_mfcc:
        mfccs = np.mean(
            librosa.feature.mfcc(y=X, sr=sr, n_mfcc=n_mfcc).T, axis=0
        ).astype(np.float32)
        result = np.hstack((result, mfccs))

    if use_chroma:
        chroma = np.mean(
            librosa.feature.chroma_stft(S=stft, sr=sr).T, axis=0
        ).astype(np.float32)
        result = np.hstack((result, chroma))

    if use_mel:
        mel = np.mean(
            librosa.feature.melspectrogram(y=X, sr=sr).T, axis=0
        ).astype(np.float32)
        result = np.hstack((result, mel))

    logger.debug("Extracted %d features from %s", len(result), file_path)
    return result


def feature_dim(use_mfcc=True, use_chroma=True, use_mel=True, n_mfcc=40) -> int:
    """Return total number of features for the given configuration."""
    return (n_mfcc if use_mfcc else 0) + (12 if use_chroma else 0) + (128 if use_mel else 0)


def feature_names(use_mfcc=True, use_chroma=True, use_mel=True, n_mfcc=40) -> list:
    """Human-readable names matching extraction order."""
    names = []
    if use_mfcc:
        names += [f"mfcc_{i}" for i in range(n_mfcc)]
    if use_chroma:
        names += [f"chroma_{i}" for i in range(12)]
    if use_mel:
        names += [f"mel_{i}" for i in range(128)]
    return names
