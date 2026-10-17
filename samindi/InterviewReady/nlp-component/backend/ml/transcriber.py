from functools import lru_cache

from faster_whisper import WhisperModel

from .config import (
    WHISPER_MODEL,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
)


@lru_cache(maxsize=1)
def get_whisper_model():
    return WhisperModel(
        WHISPER_MODEL,
        device=WHISPER_DEVICE,
        compute_type=WHISPER_COMPUTE_TYPE,
    )


def transcribe_audio(audio_path: str) -> str:
    model = get_whisper_model()

    segments, _ = model.transcribe(
        audio_path,
        language="en",
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
    )

    transcript = " ".join(
        segment.text.strip()
        for segment in segments
        if segment.text and segment.text.strip()
    )

    return " ".join(transcript.split()).strip()
