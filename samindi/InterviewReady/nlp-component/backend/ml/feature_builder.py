from .text_features import extract_text_numeric_features
from .audio_features import extract_audio_numeric_features


def build_numeric_features(
    transcript: str,
    audio_path: str,
) -> dict:

    return {
        **extract_text_numeric_features(transcript),
        **extract_audio_numeric_features(
            audio_path,
            transcript,
        ),
    }
