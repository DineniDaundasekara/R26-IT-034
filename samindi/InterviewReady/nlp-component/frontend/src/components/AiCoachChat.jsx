import { useState } from "react";
import { askCoach } from "../api.js";

const QUICK_PROMPTS = [
  "Give me a stronger opening for this answer.",
  "How can I explain my project more clearly?",
  "Show me how to make my result stronger without inventing facts.",
  "Give me one mock question based on this answer.",
];

export default function AiCoachChat({ result, enabled }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [mode, setMode] = useState("");

  async function submit(value = question) {
    const prompt = String(value || "").trim();
    if (!prompt || loading) return;

    setQuestion(prompt);
    setLoading(true);
    setError("");
    setNotice("");
    setMode("");

    try {
      const response = await askCoach({
        transcript: result.transcript,
        communicationLevel: result.communicationLevel,
        question: prompt,
        targetRole: result.targetRole || "",
      });

      const textAnswer = typeof response === "string" ? response : (response?.answer || "");
      setAnswer(textAnswer);
      setMode(response?.mode || "local-evidence-coach");

      if (response?.fallback) {
        setNotice(
          response?.message ||
            "The built-in evidence-based coach is active. Your guidance is based on your current transcript and detected improvement areas."
        );
      }
    } catch (err) {
      setError(
        "The coaching service is temporarily unavailable. Your main analysis and practice plan are still available."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel ai-chat-panel">
      <div className="section-kicker">FOLLOW-UP COACH</div>
      <h2>Ask about your own answer</h2>
      <p className="section-copy">
        Ask for wording help, a better opening, STAR structure, or a new practice challenge. Guidance stays grounded in your own answer and does not invent candidate facts.
      </p>

      <div className="quick-prompts">
        {QUICK_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            disabled={loading}
            onClick={() => submit(prompt)}
          >
            {prompt}
          </button>
        ))}
      </div>

      <div className="coach-input-row">
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask your communication coach..."
          disabled={loading}
          onKeyDown={(event) => {
            if (event.key === "Enter") submit();
          }}
        />
        <button
          className="primary-button"
          disabled={loading || !question.trim()}
          onClick={() => submit()}
        >
          {loading ? "Preparing guidance..." : "Ask coach"}
        </button>
      </div>

      {notice && (
        <div className="coach-notice" role="status">
          <div className="coach-notice-icon">i</div>
          <div>
            <strong>Evidence-based coaching mode</strong>
            <p>{notice}</p>
          </div>
        </div>
      )}

      {error && <div className="inline-error">{error}</div>}

      {answer && (
        <div className="coach-answer">
          <div className="coach-answer-head">
            <span>{mode === "local-evidence-coach" ? "EVIDENCE-BASED COACH" : "AI COACH"}</span>
            {mode === "local-evidence-coach" && (
              <small>Local fallback · no candidate facts invented</small>
            )}
          </div>
          <p>{answer}</p>
        </div>
      )}
    </section>
  );
}
