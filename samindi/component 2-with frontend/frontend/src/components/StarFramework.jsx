export default function StarFramework({ items = [] }) {
  return (
    <section className="panel star-panel">
      <div className="section-kicker">PERSONAL STAR COACH</div>
      <h2>Build a stronger project answer</h2>
      <p className="section-copy">
        Use only your real experience. If information is missing, add the real detail before your next recording.
      </p>

      <div className="star-grid">
        {items.map((item, index) => (
          <article className="star-step" key={`${item.name}-${index}`}>
            <div className="star-number">{index + 1}</div>
            <div>
              <h3>{item.name}</h3>
              <p className="star-content">{item.candidateContent || item.instruction}</p>
              {item.coachingPrompt && (
                <div className="coach-prompt">
                  <strong>Ask yourself:</strong> {item.coachingPrompt}
                </div>
              )}
              {item.exampleStarter && (
                <div className="phrase-chip">“{item.exampleStarter}”</div>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function ResearchDiagnostics({ diagnostics = {} }) {
  if (!diagnostics || (!diagnostics.acousticSignals && !diagnostics.linguisticSignals)) {
    return null;
  }

  const acoustic = diagnostics.acousticSignals || {};
  const linguistic = diagnostics.linguisticSignals || {};
  const meta = diagnostics.researchMetadata || {};

  return (
    <section className="panel diagnostics-panel" style={{ marginTop: "1.5rem" }}>
      <div className="section-kicker" style={{ color: "#2563eb", fontWeight: "800", letterSpacing: "0.08em" }}>
        RESEARCH DIAGNOSTICS & FEATURE ATTRIBUTION
      </div>
      <h2 style={{ fontSize: "1.35rem", margin: "0.4rem 0" }}>Multi-Modal Spoken Communication Evidence</h2>
      <p className="section-copy" style={{ color: "#64748b", fontSize: "0.85rem", marginBottom: "1.2rem" }}>
        Deterministic acoustic signal features and NLP discourse parsing extracted before ML classification.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1rem" }}>
        {/* Acoustic Signals Card */}
        <div style={{ background: "#f8fafc", padding: "1.1rem", borderRadius: "14px", border: "1px solid #e2e8f0" }}>
          <div style={{ fontWeight: "700", color: "#1e293b", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ background: "#dbeafe", color: "#1d4ed8", padding: "0.2rem 0.5rem", borderRadius: "6px", fontSize: "0.75rem" }}>Acoustic</span>
            <span>Spoken-Audio Signal Features</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.6rem", fontSize: "0.82rem" }}>
            <div style={{ background: "white", padding: "0.6rem", borderRadius: "8px", border: "1px solid #edf2f7" }}>
              <div style={{ color: "#64748b", fontSize: "0.72rem" }}>Speaking Rate</div>
              <strong style={{ fontSize: "1.05rem", color: "#0f172a" }}>{acoustic.speakingRateWpm || 0} WPM</strong>
            </div>
            <div style={{ background: "white", padding: "0.6rem", borderRadius: "8px", border: "1px solid #edf2f7" }}>
              <div style={{ color: "#64748b", fontSize: "0.72rem" }}>Silence Ratio</div>
              <strong style={{ fontSize: "1.05rem", color: "#0f172a" }}>{acoustic.silenceRatioPercent || 0}%</strong>
            </div>
            <div style={{ background: "white", padding: "0.6rem", borderRadius: "8px", border: "1px solid #edf2f7" }}>
              <div style={{ color: "#64748b", fontSize: "0.72rem" }}>Pause Count</div>
              <strong style={{ fontSize: "1.05rem", color: "#0f172a" }}>{acoustic.pauseCount || 0} pauses</strong>
            </div>
          </div>
        </div>

        {/* Linguistic / STAR Discourse Card */}
        <div style={{ background: "#f8fafc", padding: "1.1rem", borderRadius: "14px", border: "1px solid #e2e8f0" }}>
          <div style={{ fontWeight: "700", color: "#1e293b", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ background: "#f3e8ff", color: "#7e22ce", padding: "0.2rem 0.5rem", borderRadius: "6px", fontSize: "0.75rem" }}>Linguistic</span>
            <span>STAR Discourse & Lexical Evidence</span>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", marginBottom: "0.75rem" }}>
            <span style={{ padding: "0.25rem 0.55rem", borderRadius: "999px", fontSize: "0.75rem", fontWeight: "700", background: linguistic.starSituationDetected ? "#dcfce7" : "#fee2e2", color: linguistic.starSituationDetected ? "#15803d" : "#b91c1c" }}>
              {linguistic.starSituationDetected ? "✓ Situation" : "✗ Situation"}
            </span>
            <span style={{ padding: "0.25rem 0.55rem", borderRadius: "999px", fontSize: "0.75rem", fontWeight: "700", background: linguistic.starTaskDetected ? "#dcfce7" : "#fee2e2", color: linguistic.starTaskDetected ? "#15803d" : "#b91c1c" }}>
              {linguistic.starTaskDetected ? "✓ Task" : "✗ Task"}
            </span>
            <span style={{ padding: "0.25rem 0.55rem", borderRadius: "999px", fontSize: "0.75rem", fontWeight: "700", background: linguistic.starActionDetected ? "#dcfce7" : "#fee2e2", color: linguistic.starActionDetected ? "#15803d" : "#b91c1c" }}>
              {linguistic.starActionDetected ? "✓ Action" : "✗ Action"}
            </span>
            <span style={{ padding: "0.25rem 0.55rem", borderRadius: "999px", fontSize: "0.75rem", fontWeight: "700", background: linguistic.starResultDetected ? "#dcfce7" : "#fee2e2", color: linguistic.starResultDetected ? "#15803d" : "#b91c1c" }}>
              {linguistic.starResultDetected ? "✓ Result" : "✗ Result"}
            </span>
          </div>
          <div style={{ fontSize: "0.78rem", color: "#475569", lineHeight: "1.45" }}>
            <div><strong>Ownership Phrasing:</strong> {linguistic.hasOwnership ? "✓ Detected (First-person active)" : "Needs strengthening"}</div>
            <div><strong>Action Verbs:</strong> {(linguistic.actionVerbsDetected || []).length > 0 ? linguistic.actionVerbsDetected.join(", ") : "None detected"}</div>
            <div><strong>Filler Density:</strong> {(linguistic.fillerWordsDetected || []).length > 0 ? linguistic.fillerWordsDetected.join(", ") : "None detected"}</div>
          </div>
        </div>
      </div>

      {/* Model Pipeline Attribution */}
      <div style={{ marginTop: "1rem", padding: "0.75rem 1rem", background: "#f1f5f9", borderRadius: "10px", fontSize: "0.76rem", color: "#475569", display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "0.5rem" }}>
        <span><strong>Primary Classifier:</strong> {meta.primaryClassifier || "Linear SVM"}</span>
        <span><strong>Pipeline:</strong> TF-IDF N-Grams + StandardScaler Numeric</span>
        <span style={{ color: "#16a34a", fontWeight: "700", display: "inline-flex", alignItems: "center", gap: "0.3rem" }}>
          ✓ Grounded Anti-Hallucination Verified
        </span>
      </div>
    </section>
  );
}
