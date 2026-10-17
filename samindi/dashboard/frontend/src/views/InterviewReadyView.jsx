import { useEffect, useMemo, useRef, useState } from "react";
import {
  Mic,
  Upload,
  ArrowLeft,
  Sparkles,
  Volume2,
  CheckCircle2,
  AlertCircle,
  Play,
  Square,
  RotateCcw,
  Loader2,
} from "lucide-react";
import { analyzeAudio } from "../api.js";
import ResultList from "../components/ResultList.jsx";
import StarFramework, { ResearchDiagnostics } from "../components/StarFramework.jsx";
import PracticePlan from "../components/PracticePlan.jsx";
import AiCoachChat from "../components/AiCoachChat.jsx";
import AttemptHistory, { saveAttempt } from "../components/AttemptHistory.jsx";
import {
  PracticeAnswer,
  PriorityFocus,
  RewriteLab,
  SpeakingPatterns,
} from "../components/ProfessionalCoach.jsx";

function useAudioRecorder() {
  const recorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingBlob, setRecordingBlob] = useState(null);
  const [recorderError, setRecorderError] = useState("");

  const supported =
    typeof window !== "undefined" &&
    "MediaRecorder" in window &&
    Boolean(navigator.mediaDevices?.getUserMedia);

  async function startRecording() {
    setRecorderError("");
    setRecordingBlob(null);
    chunksRef.current = [];

    if (!supported) {
      setRecorderError("Live audio recording is not supported in this browser.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const supportedType = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/ogg;codecs=opus",
        "audio/ogg",
      ].find((type) => MediaRecorder.isTypeSupported(type));

      const recorder = new MediaRecorder(
        stream,
        supportedType ? { mimeType: supportedType } : undefined
      );
      recorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data?.size) chunksRef.current.push(event.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });
        setRecordingBlob(blob);
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        setIsRecording(false);
      };

      recorder.start(250);
      setIsRecording(true);
    } catch (error) {
      setRecorderError(error?.message || "Microphone permission was denied.");
    }
  }

  function stopRecording() {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      try {
        if (recorderRef.current.state === "recording") {
          recorderRef.current.requestData();
        }
      } catch {
        // Ignore if requestData not supported in current state
      }
      recorderRef.current.stop();
    }
  }

  function clearRecording() {
    setRecordingBlob(null);
  }

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const recordingFile = useMemo(() => {
    if (!recordingBlob || recordingBlob.size === 0) return null;
    let extension = "webm";
    if (recordingBlob.type.includes("ogg")) extension = "ogg";
    else if (recordingBlob.type.includes("wav")) extension = "wav";
    else if (recordingBlob.type.includes("mp4") || recordingBlob.type.includes("m4a"))
      extension = "m4a";
    return new File([recordingBlob], `live-interview.${extension}`, {
      type: recordingBlob.type || "audio/webm",
    });
  }, [recordingBlob]);

  return {
    supported,
    isRecording,
    recordingBlob,
    recordingFile,
    recorderError,
    startRecording,
    stopRecording,
    clearRecording,
  };
}

const NEXT_LEVEL = {
  "Poor Communication": "Average Communication",
  "Average Communication": "Good Communication",
  "Good Communication": "Excellent Communication",
  "Excellent Communication": "Maintain & refine mastery",
};

export default function InterviewReadyView({ onBackToDashboard, healthData }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [historyRefresh, setHistoryRefresh] = useState(0);
  const [context, setContext] = useState({
    targetRole: "Software Engineer",
    experienceLevel: "Final-year student",
    practiceGoal: "Speak clearly and concisely using STAR structure",
  });
  const recorder = useAudioRecorder();

  async function runAnalysis(file) {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await analyzeAudio(file, context);
      setResult(data);
      saveAttempt(data);
      setHistoryRefresh((value) => value + 1);
      window.setTimeout(() => {
        document.getElementById("analysis-result")?.scrollIntoView({ behavior: "smooth" });
      }, 120);
    } catch (analysisError) {
      setError(analysisError?.message || "Audio analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  function scrollToInput() {
    document.getElementById("practice-input")?.scrollIntoView({ behavior: "smooth" });
  }

  const audioUrl = useMemo(
    () => (recorder.recordingBlob ? URL.createObjectURL(recorder.recordingBlob) : ""),
    [recorder.recordingBlob]
  );

  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  return (
    <div className="module-view-wrapper">
      {/* Top Breadcrumb Nav */}
      <div className="view-subbar">
        <button className="back-dashboard-btn" onClick={onBackToDashboard}>
          <ArrowLeft size={16} /> Back to Home
        </button>
        <span className="view-tag">
          <Mic size={14} /> Communication Skill Guidance (InterviewReady)
        </span>
      </div>

      <main className="page">
        {/* Module Hero */}
        <section className="hero">
          <div className="hero-copy">
            <span className="hero-label">INTERVIEW READINESS · SPOKEN COMMUNICATION</span>
            <h1>Know how you sound. Know exactly what to improve.</h1>
            <p>
              Record or upload a practice answer and get an instant read on how you come across —
              your pace, clarity, and structure — paired with AI coaching that turns your weak spots
              into stronger, more confident answers: a personalised practice script, mock follow-up
              questions, and a 7-day improvement plan.
            </p>
            <div className="hero-points">
              <span>Instant Speech Analysis</span>
              <span>Clarity & Structure Scoring</span>
              <span>AI-Powered Coaching</span>
              <span>Personalised Practice Plan</span>
              <span>Progress Tracking</span>
            </div>
          </div>
          <div className="hero-note">
            <span>WHY YOU CAN TRUST THIS FEEDBACK</span>
            <p><strong>Objective, not opinionated.</strong> Your rating comes from a trained model, not a chatbot's impression.</p>
            <p><strong>Coaching grounded in your words.</strong> Every suggestion is backed by what you actually said.</p>
            <p><strong>Honest progress.</strong> No inflated percentages — just genuine, trackable improvement.</p>
          </div>
        </section>

        {/* Personalization Inputs */}
        <section className="panel context-panel" id="practice-input">
          <div className="section-kicker">PERSONALISE THE SESSION</div>
          <h2>Tell the coach what you are preparing for</h2>
          <div className="context-grid">
            <label>
              <span>Target role</span>
              <input
                value={context.targetRole}
                onChange={(event) => setContext({ ...context, targetRole: event.target.value })}
                placeholder="e.g. Software Engineer, QA Engineer, Data Analyst"
              />
            </label>
            <label>
              <span>Experience level</span>
              <select
                value={context.experienceLevel}
                onChange={(event) => setContext({ ...context, experienceLevel: event.target.value })}
              >
                <option>Final-year student</option>
                <option>Intern</option>
                <option>Recent graduate</option>
                <option>Entry-level professional</option>
              </select>
            </label>
            <label className="goal-field">
              <span>Practice goal</span>
              <input
                value={context.practiceGoal}
                onChange={(event) => setContext({ ...context, practiceGoal: event.target.value })}
                placeholder="What do you want to improve?"
              />
            </label>
          </div>
        </section>

        {/* Audio Inputs */}
        <section className="input-grid">
          {/* Upload Audio */}
          <article className="input-panel">
            <div className="input-icon"><Upload size={22} /></div>
            <div className="section-kicker">UPLOAD AUDIO</div>
            <h2>Analyse an existing answer</h2>
            <p>Supported audio formats: WAV, MP3, M4A, OGG, WEBM, FLAC, AAC.</p>
            <label className="file-picker">
              <input
                type="file"
                accept="audio/*"
                onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
              />
              <span>{selectedFile ? selectedFile.name : "Choose interview audio file"}</span>
            </label>
            <button
              className="primary-button wide"
              disabled={!selectedFile || loading}
              onClick={() => runAnalysis(selectedFile)}
            >
              Analyse uploaded audio answer
            </button>
          </article>

          {/* Live Recording */}
          <article className="input-panel recording-panel">
            <div className={`input-icon ${recorder.isRecording ? "recording" : ""}`}>
              <Mic size={22} />
            </div>
            <div className="section-kicker">LIVE PRACTICE</div>
            <h2>Record a fresh interview answer</h2>
            <p>Speak naturally into your microphone. Answer as you would in a real interview.</p>
            {!recorder.recordingBlob ? (
              <button
                className={recorder.isRecording ? "danger-button wide" : "secondary-button wide"}
                disabled={!recorder.supported || loading}
                onClick={recorder.isRecording ? recorder.stopRecording : recorder.startRecording}
              >
                {recorder.isRecording ? "■ Stop recording" : "● Start recording"}
              </button>
            ) : (
              <>
                <audio className="audio-preview" controls src={audioUrl} />
                <div className="record-actions">
                  <button className="secondary-button" onClick={recorder.clearRecording}>
                    Record again
                  </button>
                  <button
                    className="primary-button"
                    disabled={loading}
                    onClick={() => runAnalysis(recorder.recordingFile)}
                  >
                    Analyse recording
                  </button>
                </div>
              </>
            )}
            {recorder.recorderError && <div className="inline-error">{recorder.recorderError}</div>}
          </article>
        </section>

        {error && <div className="error-banner">{error}</div>}

        {loading && (
          <section className="loading-panel">
            <div className="loader" />
            <div>
              <strong>Building your communication coaching assessment</strong>
              <p>Transcribing your speech, analysing delivery and structure, and preparing personalised coaching...</p>
            </div>
          </section>
        )}

        {/* Results Section */}
        {result && (
          <section id="analysis-result" className="results-shell">
            <section className="assessment-header">
              <div>
                <div className="section-kicker">YOUR COMMUNICATION ASSESSMENT</div>
                <h2>{result.communicationLevel}</h2>
                <p>{result.coachSummary}</p>
              </div>
              <div className="assessment-side">
                <span
                  className={`mode-badge ${
                    String(result.guidanceMode || "").startsWith("openai") ? "ai" : "fallback"
                  }`}
                >
                  {String(result.guidanceMode || "").includes("verified")
                    ? "✦ AI-grounded + verified"
                    : String(result.guidanceMode || "").startsWith("openai")
                    ? "✦ AI-grounded coaching"
                    : "Evidence-based fallback"}
                </span>
                <div className="next-level">
                  <span>Next development target</span>
                  <strong>{NEXT_LEVEL[result.communicationLevel] || "Refine communication"}</strong>
                </div>
              </div>
            </section>

            <section className="panel transcript-panel">
              <div className="panel-heading-row">
                <div>
                  <div className="section-kicker">WHISPER TRANSCRIPT</div>
                  <h2>What the speech recognition heard</h2>
                </div>
                <span className="tiny-note">Used as empirical evidence for coaching</span>
              </div>
              <p className="transcript">{result.transcript}</p>
            </section>

            <ResearchDiagnostics diagnostics={result.diagnostics} />

            <section className="knowledge-grid">
              <ResultList
                title="What you already demonstrate"
                subtitle="Knowledge and communication behaviours clearly visible in this answer."
                items={result.knowledgeSnapshot?.alreadyDemonstrated || result.strengths}
                variant="strength"
              />
              <ResultList
                title="What to build next"
                subtitle="Priority behaviours that will elevate your response to the next level."
                items={result.knowledgeSnapshot?.nextCapabilitiesToBuild || result.weaknesses}
                variant="weakness"
              />
            </section>

            <PriorityFocus items={result.priorityFocus || []} />

            <section className="two-column-results">
              <ResultList
                title="Strengths from this answer"
                items={result.strengths || []}
                variant="strength"
              />
              <ResultList
                title="Areas to improve"
                items={result.weaknesses || []}
                variant="weakness"
              />
            </section>

            <section className="panel guidance-panel">
              <div className="section-kicker">COACHING GUIDANCE</div>
              <h2>What to do differently in your next answer</h2>
              <div className="guidance-grid">
                {(result.guidance || []).map((item, index) => (
                  <div className="guidance-item" key={`${item}-${index}`}>
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <p>{item}</p>
                  </div>
                ))}
              </div>
            </section>

            <RewriteLab items={result.professionalRewrites || []} />
            <SpeakingPatterns items={result.speakingPatterns || []} />
            <PracticeAnswer answer={result.practiceAnswer || ""} />
            <StarFramework items={result.starCoach || result.starPractice || []} />

            {result.nextAttemptChallenge && (
              <section className="panel challenge-panel">
                <div>
                  <div className="section-kicker">NEXT ATTEMPT CHALLENGE</div>
                  <h2>{result.nextAttemptChallenge.question}</h2>
                  <p><strong>Focus:</strong> {result.nextAttemptChallenge.focus}</p>
                </div>
                <div className="challenge-checks">
                  {(result.nextAttemptChallenge.beforeRecording || []).map((item) => (
                    <span key={item}>✓ {item}</span>
                  ))}
                </div>
              </section>
            )}

            <PracticePlan
              activities={result.activities || []}
              sevenDayPlan={result.sevenDayPlan || []}
              motivationText={result.motivation || ""}
              onRecordAgain={scrollToInput}
              attemptKey={result.transcript || ""}
            />

            <section className="panel mock-panel">
              <div className="section-kicker">MOCK INTERVIEW LAB</div>
              <h2>Questions selected for your next practice round</h2>
              <div className="mock-grid">
                {(result.mockInterviewPrompts || []).map((prompt, index) => (
                  <article key={`${prompt}-${index}`}>
                    <span>Q{index + 1}</span>
                    <p>{prompt}</p>
                  </article>
                ))}
              </div>
            </section>

            <AiCoachChat result={result} enabled={healthData?.openaiGuidanceReady} />
            <AttemptHistory refreshKey={historyRefresh} />
          </section>
        )}
      </main>
    </div>
  );
}
