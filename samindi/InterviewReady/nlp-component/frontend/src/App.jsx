import { useEffect, useMemo, useRef, useState } from "react";
import { analyzeAudio, healthCheck } from "./api.js";
import ResultList from "./components/ResultList.jsx";
import StarFramework, { ResearchDiagnostics } from "./components/StarFramework.jsx";
import PracticePlan from "./components/PracticePlan.jsx";
import AiCoachChat from "./components/AiCoachChat.jsx";
import AttemptHistory, { saveAttempt } from "./components/AttemptHistory.jsx";
import {
  PracticeAnswer,
  PriorityFocus,
  RewriteLab,
  SpeakingPatterns,
} from "./components/ProfessionalCoach.jsx";

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
    navigator.mediaDevices?.getUserMedia;

  async function startRecording() {
    setRecorderError("");
    setRecordingBlob(null);
    chunksRef.current = [];

    if (!supported) {
      setRecorderError("Live recording is not supported in this browser.");
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
    else if (recordingBlob.type.includes("mp4") || recordingBlob.type.includes("m4a")) extension = "m4a";
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
  "Excellent Communication": "Maintain & refine",
};

export default function App() {
  const [backendState, setBackendState] = useState("checking");
  const [aiReady, setAiReady] = useState(false);
  const [aiModel, setAiModel] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [historyRefresh, setHistoryRefresh] = useState(0);
  const [context, setContext] = useState({
    targetRole: "",
    experienceLevel: "Final-year student",
    practiceGoal: "Speak clearly and professionally in interviews",
  });
  const recorder = useAudioRecorder();

  useEffect(() => {
    healthCheck()
      .then((health) => {
        setBackendState(health.modelReady ? "ready" : "needs-model");
        setAiReady(Boolean(health.aiGuidanceReady));
        setAiModel(health.aiGuidanceModel || "");
      })
      .catch(() => setBackendState("offline"));
  }, []);

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
      setError(analysisError?.message || "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  function scrollToInput() {
    document.getElementById("practice-input")?.scrollIntoView({ behavior: "smooth" });
  }

  const audioUrl = useMemo(
    () => recorder.recordingBlob ? URL.createObjectURL(recorder.recordingBlob) : "",
    [recorder.recordingBlob]
  );

  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-wrap">
          <div className="brand-mark">IR</div>
          <div>
            <div className="brand-name">InterviewReady</div>
            <div className="brand-caption">AI Communication Coach</div>
          </div>
        </div>
        <div className="status-wrap">
          <a className="dashboard-back" href="http://127.0.0.1:5180">
            PathReady dashboard
          </a>
          <div className={`backend-status ${backendState}`}>
            <span />
            {backendState === "ready"
              ? "ML ready"
              : backendState === "needs-model"
              ? "Add trained model"
              : backendState === "offline"
              ? "Backend offline"
              : "Checking system"}
          </div>
          <div className={`backend-status ${aiReady ? "ready" : "needs-model"}`}>
            <span />
            {aiReady ? `AI coach · ${aiModel}` : "AI coach fallback"}
          </div>
        </div>
      </header>

      <main className="page">
        <section className="hero">
          <div className="hero-copy">
            <span className="hero-label">FINAL-YEAR RESEARCH · INTERVIEW COMMUNICATION READINESS</span>
            <h1>Know how you sound. Learn what to improve next.</h1>
            <p>
              A saved machine-learning model predicts the overall communication category. An evidence layer explains what is present in the answer, and the AI coach turns that evidence into professional English patterns, a personalised practice answer, mock questions, and a day-by-day improvement journey.
            </p>
            <div className="hero-points">
              <span>Faster-Whisper</span>
              <span>NLP + spoken-audio features</span>
              <span>Saved ML classifier</span>
              <span>Grounded AI guidance</span>
              <span>Practice tracking</span>
            </div>
          </div>
          <div className="hero-note">
            <span>RESEARCH DESIGN</span>
            <p><strong>ML decides the category.</strong> The generative model does not change the prediction.</p>
            <p><strong>AI coaches from evidence.</strong> It is instructed not to invent candidate experience or fake results.</p>
            <p><strong>Progress means practice.</strong> No artificial “communication improvement %” is shown.</p>
          </div>
        </section>

        <section className="panel context-panel" id="practice-input">
          <div className="section-kicker">PERSONALISE THE SESSION</div>
          <h2>Tell the coach what you are preparing for</h2>
          <div className="context-grid">
            <label>
              <span>Target role</span>
              <input
                value={context.targetRole}
                onChange={(event) => setContext({ ...context, targetRole: event.target.value })}
                placeholder="e.g. QA Engineer, Data Analyst"
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

        <section className="input-grid">
          <article className="input-panel">
            <div className="input-icon">↑</div>
            <div className="section-kicker">UPLOAD AUDIO</div>
            <h2>Analyse an existing answer</h2>
            <p>Use WAV, MP3, M4A, OGG, WEBM, FLAC, or AAC.</p>
            <label className="file-picker">
              <input
                type="file"
                accept="audio/*"
                onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
              />
              <span>{selectedFile ? selectedFile.name : "Choose interview audio"}</span>
            </label>
            <button
              className="primary-button wide"
              disabled={!selectedFile || loading || backendState !== "ready"}
              onClick={() => runAnalysis(selectedFile)}
            >
              Analyse uploaded answer
            </button>
          </article>

          <article className="input-panel recording-panel">
            <div className={`input-icon ${recorder.isRecording ? "recording" : ""}`}>●</div>
            <div className="section-kicker">LIVE PRACTICE</div>
            <h2>Record a fresh interview answer</h2>
            <p>Answer naturally. Do not read a prepared script.</p>
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
                  <button className="secondary-button" onClick={recorder.clearRecording}>Record again</button>
                  <button
                    className="primary-button"
                    disabled={loading || backendState !== "ready"}
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
              <strong>Building your communication coaching plan</strong>
              <p>Whisper transcription → ML classification → evidence analysis → personalised guidance</p>
            </div>
          </section>
        )}

        {result && (
          <section id="analysis-result" className="results-shell">
            <section className="assessment-header">
              <div>
                <div className="section-kicker">CURRENT ASSESSMENT</div>
                <h2>{result.communicationLevel}</h2>
                <p>{result.coachSummary}</p>
              </div>
              <div className="assessment-side">
                <span className={`mode-badge ${String(result.guidanceMode || "").startsWith("openai") ? "ai" : "fallback"}`}>
                  {String(result.guidanceMode || "").includes("verified") ? "✦ AI-grounded + verified" : String(result.guidanceMode || "").startsWith("openai") ? "✦ AI-grounded coaching" : "Evidence-based fallback"}
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
                  <h2>What the system heard</h2>
                </div>
                <span className="tiny-note">Used as evidence for coaching</span>
              </div>
              <p className="transcript">{result.transcript}</p>
            </section>

            <ResearchDiagnostics diagnostics={result.diagnostics} />

            <section className="knowledge-grid">
              <ResultList
                title="What you already demonstrate"
                subtitle="Knowledge and communication behaviours already visible in this answer."
                items={result.knowledgeSnapshot?.alreadyDemonstrated || result.strengths}
                variant="strength"
              />
              <ResultList
                title="What to build next"
                subtitle="Priority behaviours that can make the next answer more interview-ready."
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

            <AiCoachChat result={result} enabled={aiReady} />
            <AttemptHistory refreshKey={historyRefresh} />
          </section>
        )}
      </main>
    </div>
  );
}
