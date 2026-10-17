from pathlib import Path
import shutil
import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ml.ai_guidance import generate_ai_guidance, generate_follow_up
from ml.config import (
    AUDIO_EXTENSIONS,
    MODEL_FILE,
    OPENAI_API_KEY,
    OPENAI_GUIDANCE_ENABLED,
    OPENAI_GUIDANCE_MODEL,
    OPENAI_GUIDANCE_VERIFY,
    OPENAI_VERIFIER_MODEL,
    TEMP_DIR,
)
from ml.guidance import build_advanced_fallback, build_follow_up_fallback, build_guidance
from ml.model_service import predict_communication_level
from ml.transcriber import transcribe_audio


app = FastAPI(
    title="InterviewReady AI Communication Coach API",
    version="2.0.0",
    description=(
        "Faster-Whisper transcription, NLP + spoken-audio communication classification, "
        "evidence extraction, and grounded OpenAI interview coaching."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "success": True,
        "message": "InterviewReady AI Communication Coach API is running.",
    }


@app.get("/health")
def health():
    return {
        "success": True,
        "modelReady": MODEL_FILE.exists(),
        "aiGuidanceReady": bool(
            OPENAI_GUIDANCE_ENABLED and OPENAI_API_KEY
        ),
        "aiGuidanceModel": (
            OPENAI_GUIDANCE_MODEL
            if OPENAI_GUIDANCE_ENABLED and OPENAI_API_KEY
            else None
        ),
        "aiGuidanceVerification": bool(
            OPENAI_GUIDANCE_ENABLED and OPENAI_API_KEY and OPENAI_GUIDANCE_VERIFY
        ),
        "aiVerifierModel": (
            OPENAI_VERIFIER_MODEL
            if OPENAI_GUIDANCE_ENABLED and OPENAI_API_KEY and OPENAI_GUIDANCE_VERIFY
            else None
        ),
    }


class CoachFollowUpRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=12000)
    communicationLevel: str = Field(min_length=1, max_length=80)
    question: str = Field(min_length=1, max_length=1000)
    targetRole: str = Field(default="", max_length=120)


@app.post("/api/coach/follow-up")
def coach_follow_up(payload: CoachFollowUpRequest):
    fallback_answer = build_follow_up_fallback(
        transcript=payload.transcript,
        communication_level=payload.communicationLevel,
        question=payload.question,
        target_role=payload.targetRole,
    )

    # The follow-up coach remains useful even when OpenAI is not configured.
    if not (OPENAI_GUIDANCE_ENABLED and OPENAI_API_KEY):
        return {
            "success": True,
            "fallback": True,
            "mode": "local-evidence-coach",
            "message": (
                "Using the built-in evidence-based coach because generative AI "
                "is not currently available."
            ),
            "answer": fallback_answer,
        }

    try:
        answer = generate_follow_up(
            transcript=payload.transcript,
            communication_level=payload.communicationLevel,
            question=payload.question,
            target_role=payload.targetRole,
        )
        if not answer:
            raise RuntimeError("No coach response was generated.")

        return {
            "success": True,
            "fallback": False,
            "mode": "openai-grounded",
            "message": "",
            "answer": answer,
        }

    except Exception as error:
        # Never expose raw provider errors, API keys, quota details, or stack traces
        # to a candidate. The server can log the short error for development.
        print(f"AI coach provider unavailable; using local fallback: {type(error).__name__}")

        return {
            "success": True,
            "fallback": True,
            "mode": "local-evidence-coach",
            "message": (
                "AI Coach is temporarily using the built-in evidence-based mode. "
                "Your communication analysis and personalised practice guidance "
                "are still available."
            ),
            "answer": fallback_answer,
        }


@app.post("/api/analyze/audio")
async def analyze_audio(
    audio: UploadFile = File(...),
    target_role: str = Form(default=""),
    experience_level: str = Form(default=""),
    practice_goal: str = Form(default=""),
):
    original_name = audio.filename or "recording.webm"
    suffix = Path(original_name).suffix.lower()

    if suffix not in AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported audio format. Use WAV, MP3, M4A, OGG, WEBM, FLAC, or AAC."
            ),
        )

    temp_path = TEMP_DIR / f"{uuid.uuid4().hex}{suffix}"

    try:
        with temp_path.open("wb") as output:
            shutil.copyfileobj(audio.file, output)

        if temp_path.stat().st_size == 0:
            raise HTTPException(
                status_code=400,
                detail="The uploaded audio file is empty.",
            )

        transcript = transcribe_audio(str(temp_path))

        if not transcript:
            raise HTTPException(
                status_code=422,
                detail="Whisper could not detect usable speech in this recording.",
            )

        communication_level = predict_communication_level(
            transcript,
            str(temp_path),
        )

        baseline = build_guidance(
            transcript,
            communication_level,
            audio_path=str(temp_path),
        )

        guidance_mode = "evidence-fallback"
        ai_error = None
        advanced = None

        try:
            advanced = generate_ai_guidance(
                transcript=transcript,
                communication_level=communication_level,
                evidence=baseline["evidence"],
                deterministic_guidance=baseline,
                target_role=target_role.strip(),
                experience_level=experience_level.strip(),
                practice_goal=practice_goal.strip(),
            )
            if advanced:
                guidance_mode = (
                    "openai-grounded-verified"
                    if OPENAI_GUIDANCE_VERIFY
                    else "openai-grounded"
                )
        except Exception as error:
            ai_error = str(error)

        if advanced is None:
            advanced = build_advanced_fallback(
                transcript=transcript,
                communication_level=communication_level,
                baseline=baseline,
                target_role=target_role.strip(),
            )

        return {
            "success": True,
            "data": {
                "transcript": transcript,
                "communicationLevel": communication_level,
                "guidanceMode": guidance_mode,
                "targetRole": target_role.strip(),
                "experienceLevel": experience_level.strip(),
                "diagnostics": baseline.get("diagnostics", {}),
                "audioEvidence": baseline.get("audioEvidence", {}),
                **advanced,
            },
            "meta": {
                "modelPredictionSource": "saved-ml-pipeline",
                "guidanceSource": guidance_mode,
                "aiFallbackUsed": bool(ai_error),
            },
        }

    except HTTPException:
        raise
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Audio analysis failed: " + str(error),
        ) from error
    finally:
        try:
            await audio.close()
        except Exception:
            pass

        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
