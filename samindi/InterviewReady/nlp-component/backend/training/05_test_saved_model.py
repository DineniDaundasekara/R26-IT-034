import json
import sys
from pathlib import Path

# Add backend directory to sys.path automatically
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ml.ai_guidance import generate_ai_guidance
from ml.guidance import build_advanced_fallback, build_guidance
from ml.model_service import predict_communication_level
from ml.transcriber import transcribe_audio


def main():
    if len(sys.argv) < 2:
        # Check for default sample audio in data directory
        default_sample = BACKEND_DIR / "data" / "training_audio" / "1.wav"
        if default_sample.exists():
            print(f"No audio file specified. Using sample: {default_sample}\n")
            audio_path = default_sample
            target_role = "Software Engineer"
        else:
            print(
                'Usage: python 05_test_saved_model.py "C:\\path\\to\\test_audio.wav" [target role]'
            )
            raise SystemExit(1)
    else:
        audio_path = Path(sys.argv[1]).expanduser().resolve()
        target_role = sys.argv[2] if len(sys.argv) >= 3 else "Software Engineer"


    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    transcript = transcribe_audio(str(audio_path))
    if not transcript:
        raise RuntimeError("Whisper did not detect speech.")

    communication_level = predict_communication_level(transcript, str(audio_path))
    baseline = build_guidance(transcript, communication_level)

    guidance_mode = "evidence-fallback"
    try:
        advanced = generate_ai_guidance(
            transcript=transcript,
            communication_level=communication_level,
            evidence=baseline["evidence"],
            deterministic_guidance=baseline,
            target_role=target_role,
        )
        if advanced:
            guidance_mode = "openai-grounded"
        else:
            advanced = build_advanced_fallback(
                transcript=transcript,
                communication_level=communication_level,
                baseline=baseline,
                target_role=target_role,
            )
    except Exception as error:
        print(f"OpenAI guidance unavailable; using evidence fallback: {error}", file=sys.stderr)
        advanced = build_advanced_fallback(
            transcript=transcript,
            communication_level=communication_level,
            baseline=baseline,
            target_role=target_role,
        )

    result = {
        "transcript": transcript,
        "communicationLevel": communication_level,
        "guidanceMode": guidance_mode,
        **advanced,
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
