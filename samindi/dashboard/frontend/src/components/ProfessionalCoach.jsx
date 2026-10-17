import { useState } from "react";

function copyText(value, setCopied) {
  navigator.clipboard?.writeText(value).then(() => {
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1200);
  });
}

export function PriorityFocus({ items = [] }) {
  return (
    <section className="panel">
      <div className="section-kicker">TOP PRIORITIES</div>
      <h2>Your next communication upgrades</h2>
      <div className="focus-grid">
        {items.map((item, index) => (
          <article className="focus-card" key={`${item.title}-${index}`}>
            <div className="focus-index">0{index + 1}</div>
            <h3>{item.title}</h3>
            <p>{item.why}</p>
            <div className="focus-target">
              <span>Target behaviour</span>
              <strong>{item.targetBehavior}</strong>
            </div>
            <div className="quick-win">{item.quickWin}</div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function RewriteLab({ items = [] }) {
  return (
    <section className="panel">
      <div className="section-kicker">PROFESSIONAL ENGLISH LAB</div>
      <h2>Say the same idea more professionally</h2>
      <p className="section-copy">
        These examples improve structure and wording without adding experience you did not mention.
      </p>
      <div className="rewrite-stack">
        {items.map((item, index) => (
          <article className="rewrite-card" key={`rewrite-${index}`}>
            <div className="rewrite-column muted-block">
              <span className="mini-label">YOUR IDEA</span>
              <p>{item.originalIdea}</p>
            </div>
            <div className="rewrite-arrow">→</div>
            <div className="rewrite-column upgraded-block">
              <span className="mini-label">INTERVIEW-READY VERSION</span>
              <p>{item.improvedVersion}</p>
              <small>{item.whyItIsBetter}</small>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function SpeakingPatterns({ items = [] }) {
  return (
    <section className="panel">
      <div className="section-kicker">SPEAKING PATTERN LIBRARY</div>
      <h2>Reusable professional sentence patterns</h2>
      <p className="section-copy">
        Learn the pattern, not a memorized script. Replace the example with your own real experience.
      </p>
      <div className="pattern-grid">
        {items.map((item, index) => (
          <article className="pattern-card" key={`${item.purpose}-${index}`}>
            <span>{item.purpose}</span>
            <h3>{item.pattern}</h3>
            <p>{item.candidateExample}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export function PracticeAnswer({ answer = "" }) {
  const [copied, setCopied] = useState(false);
  const [speaking, setSpeaking] = useState(false);

  function speak() {
    if (!("speechSynthesis" in window) || !answer) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(answer);
    utterance.rate = 0.92;
    utterance.onend = () => setSpeaking(false);
    setSpeaking(true);
    window.speechSynthesis.speak(utterance);
  }

  function stop() {
    window.speechSynthesis?.cancel();
    setSpeaking(false);
  }

  return (
    <section className="panel practice-answer-panel">
      <div className="practice-answer-head">
        <div>
          <div className="section-kicker">PRACTICE ANSWER</div>
          <h2>Hear and rehearse an improved version</h2>
        </div>
        <div className="answer-actions">
          <button className="secondary-button small" onClick={() => copyText(answer, setCopied)}>
            {copied ? "Copied" : "Copy"}
          </button>
          {!speaking ? (
            <button className="primary-button small" onClick={speak}>▶ Listen</button>
          ) : (
            <button className="primary-button small" onClick={stop}>■ Stop</button>
          )}
        </div>
      </div>
      <p className="practice-answer">{answer}</p>
      <div className="fact-guard">
        Use this as a speaking model. Keep only details that are true for your own experience.
      </div>
    </section>
  );
}
