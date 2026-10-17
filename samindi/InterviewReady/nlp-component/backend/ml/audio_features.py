from pathlib import Path

import av
import numpy as np


TARGET_SAMPLE_RATE = 16000


def decode_audio_mono(audio_path: str | Path) -> np.ndarray:
    container = av.open(str(audio_path))

    if not container.streams.audio:
        container.close()
        raise ValueError("The file does not contain an audio stream.")

    stream = container.streams.audio[0]

    resampler = av.audio.resampler.AudioResampler(
        format="fltp",
        layout="mono",
        rate=TARGET_SAMPLE_RATE,
    )

    chunks = []

    for frame in container.decode(stream):
        frames = resampler.resample(frame)

        if frames is None:
            continue

        if not isinstance(frames, list):
            frames = [frames]

        for resampled_frame in frames:
            array = resampled_frame.to_ndarray()

            if array.ndim > 1:
                array = array.reshape(-1)

            chunks.append(
                array.astype(np.float32, copy=False)
            )

    flushed = resampler.resample(None)

    if flushed:
        if not isinstance(flushed, list):
            flushed = [flushed]

        for resampled_frame in flushed:
            array = resampled_frame.to_ndarray()

            if array.ndim > 1:
                array = array.reshape(-1)

            chunks.append(
                array.astype(np.float32, copy=False)
            )

    container.close()

    if not chunks:
        return np.array([], dtype=np.float32)

    return np.concatenate(chunks)


def extract_audio_numeric_features(
    audio_path: str | Path,
    transcript: str,
) -> dict:

    signal = decode_audio_mono(audio_path)

    if signal.size == 0:
        return {
            "audio_duration_seconds": 0.0,
            "speech_duration_seconds": 0.0,
            "silence_ratio": 1.0,
            "pause_count": 0.0,
            "average_pause_duration": 0.0,
            "speaking_rate_wpm": 0.0,
            "energy_dynamic_range_db": 0.0,
        }

    duration = signal.size / TARGET_SAMPLE_RATE

    frame_length = int(0.030 * TARGET_SAMPLE_RATE)
    hop_length = int(0.010 * TARGET_SAMPLE_RATE)

    if signal.size < frame_length:
        padded = np.pad(
            signal,
            (0, frame_length - signal.size)
        )
        frames = padded.reshape(1, -1)
    else:
        frame_count = 1 + (
            signal.size - frame_length
        ) // hop_length

        frames = np.stack([
            signal[
                i * hop_length:
                i * hop_length + frame_length
            ]
            for i in range(frame_count)
        ])

    rms = np.sqrt(
        np.mean(
            np.square(frames),
            axis=1
        ) + 1e-12
    )

    positive_rms = rms[rms > 1e-7]

    if positive_rms.size:
        threshold = max(
            float(np.percentile(positive_rms, 25)) * 1.5,
            1e-4,
        )
        p95 = float(np.percentile(positive_rms, 95))
        p05 = float(np.percentile(positive_rms, 5))
        energy_dynamic_range = float(20 * np.log10((p95 / (p05 + 1e-9)) + 1e-9))
    else:
        threshold = 1e-4
        energy_dynamic_range = 0.0

    speech_mask = rms > threshold
    silence_mask = ~speech_mask

    frame_step_seconds = hop_length / TARGET_SAMPLE_RATE

    speech_duration = float(
        speech_mask.sum() * frame_step_seconds
    )

    silence_duration = max(
        float(duration - speech_duration),
        0.0
    )

    silence_ratio = (
        silence_duration / duration
        if duration > 0
        else 1.0
    )

    pause_lengths = []
    current = 0

    for is_silent in silence_mask:
        if is_silent:
            current += 1
        else:
            if current:
                seconds = current * frame_step_seconds

                if seconds >= 0.45:
                    pause_lengths.append(seconds)

                current = 0

    if current:
        seconds = current * frame_step_seconds

        if seconds >= 0.45:
            pause_lengths.append(seconds)

    pause_count = len(pause_lengths)

    average_pause_duration = (
        float(np.mean(pause_lengths))
        if pause_lengths
        else 0.0
    )

    word_count = len(
        str(transcript or "").split()
    )

    speaking_minutes = speech_duration / 60.0

    speaking_rate_wpm = (
        float(word_count / speaking_minutes)
        if speaking_minutes > 0.01
        else 0.0
    )

    return {
        "audio_duration_seconds": float(duration),
        "speech_duration_seconds": float(speech_duration),
        "silence_ratio": float(silence_ratio),
        "pause_count": float(pause_count),
        "average_pause_duration": float(average_pause_duration),
        "speaking_rate_wpm": float(speaking_rate_wpm),
        "energy_dynamic_range_db": round(float(energy_dynamic_range), 1),
    }
