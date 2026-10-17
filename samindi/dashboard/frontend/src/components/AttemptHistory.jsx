const HISTORY_KEY = "interviewready-attempt-history-v3";

export function saveAttempt(result) {
  try {
    const existing = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    const entry = {
      id: window.crypto?.randomUUID?.() || String(Date.now()),
      at: new Date().toISOString(),
      level: result.communicationLevel,
      role: result.targetRole || "General interview",
      focus: (result.priorityFocus || []).map((item) => item.title).slice(0, 3),
    };
    const next = [entry, ...existing].slice(0, 12);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
  } catch {
    // History is a convenience feature; analysis must still work if storage is blocked.
  }
}

function readHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
  } catch {
    return [];
  }
}

export default function AttemptHistory({ refreshKey }) {
  const history = readHistory();

  if (!history.length) return null;

  return (
    <section className="panel history-panel" key={refreshKey}>
      <div className="section-kicker">ATTEMPT HISTORY</div>
      <h2>Track categories and focus areas over time</h2>
      <p className="section-copy">
        This timeline records model categories and coaching focus areas. It does not convert them into an artificial improvement percentage.
      </p>
      <div className="history-list">
        {history.slice(0, 6).map((item, index) => (
          <article className="history-item" key={item.id || index}>
            <div className="history-dot" />
            <div className="history-content">
              <div className="history-meta">
                <strong>{item.level}</strong>
                <span>{new Date(item.at).toLocaleString()}</span>
              </div>
              <p>{item.role}</p>
              {!!item.focus?.length && (
                <div className="history-tags">
                  {item.focus.map((focus) => <span key={focus}>{focus}</span>)}
                </div>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
