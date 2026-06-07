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

    import soundfile as sf
    import librosa

    logger.info("Opening audio file: %s", file_path)

    try:
        with sf.SoundFile(file_path) as sound_file:
            X = sound_file.read(dtype="float32")
            sr = sound_file.samplerate
            logger.info(
                "Loaded via soundfile. shape=%s sr=%s",
                X.shape,
                sr,
            )

    except Exception as e:
        logger.error("Soundfile failed: %s", e)
        logger.info("Falling back to librosa")

        X, sr = librosa.load(
            file_path,
            sr=sample_rate,
            mono=True,
        )

        logger.info(
            "Loaded via librosa. shape=%s sr=%s",
            X.shape,
            sr,
        )

    if X.ndim > 1:
        X = X.mean(axis=1)

    if sample_rate and sr != sample_rate:
        logger.info(
            "Resampling audio from %s Hz to %s Hz",
            sr,
            sample_rate,
        )

        X = librosa.resample(
            X,
            orig_sr=sr,
            target_sr=sample_rate,
        )
        sr = sample_rate

    result = np.array([], dtype=np.float32)

    # TEMP DEBUG
    use_chroma = False

    logger.info("Chroma disabled for debugging")

    logger.info("Resampling to 22050 Hz")

    if sr != 22050:
        logger.info("Resampling to 22050 Hz")

        X = librosa.resample(
            X,
            orig_sr=sr,
            target_sr=22050,
        )

        sr = 22050

    if use_mfcc:
        logger.info("Computing MFCC")

        start = time.time()
        try:
            logger.info("START MFCC")

            mfcc_raw = librosa.feature.mfcc(
                y=X,
                sr=sr,
                n_mfcc=n_mfcc,
            )

            logger.info(
                "MFCC generated in %.3f sec. shape=%s dtype=%s",
                time.time() - start,
                mfcc_raw.shape,
                mfcc_raw.dtype,
            )
        except Exception as e:
            logger.exception("MFCC FAILED: %s", e)
            raise

        start = time.time()

        mfccs = np.mean(
            mfcc_raw.T,
            axis=0,
        ).astype(np.float32)

        logger.info(
            "MFCC mean completed in %.3f sec",
            time.time() - start,
        )

        logger.info("END MFCC")

        result = np.hstack((result, mfccs))

    if use_chroma:
        logger.info("Computing Chroma")

        chroma = np.mean(
            librosa.feature.chroma_stft(
                S=stft,
                sr=sr,
            ).T,
            axis=0,
        ).astype(np.float32)

        logger.info(
            "Chroma complete. shape=%s",
            chroma.shape,
        )

        result = np.hstack((result, chroma))

    if use_mel:
        logger.info("Computing Mel")

        mel = np.mean(
            librosa.feature.melspectrogram(
                y=X,
                sr=sr,
            ).T,
            axis=0,
        ).astype(np.float32)

        logger.info(
            "Mel complete. shape=%s",
            mel.shape,
        )

        result = np.hstack((result, mel))

    logger.info("Feature extraction finished")
    logger.info("Feature vector size=%s", len(result))

    return result


def feature_dim(
    use_mfcc=True,
    use_chroma=True,
    use_mel=True,
    n_mfcc=40,
) -> int:
    """Return total number of features for the given configuration."""
    return (
        (n_mfcc if use_mfcc else 0)
        + (12 if use_chroma else 0)
        + (128 if use_mel else 0)
    )


def feature_names(
    use_mfcc=True,
    use_chroma=True,
    use_mel=True,
    n_mfcc=40,
) -> list:
    """Human-readable names matching extraction order."""
    names = []

    if use_mfcc:
        names += [f"mfcc_{i}" for i in range(n_mfcc)]

    if use_chroma:
        names += [f"chroma_{i}" for i in range(12)]

    if use_mel:
        names += [f"mel_{i}" for i in range(128)]

    return names