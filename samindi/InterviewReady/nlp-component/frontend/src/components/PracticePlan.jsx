import { useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "interviewready-practice-progress-v4";

function todayKey() {
  return new Date().toISOString().slice(0, 10);
}

function shiftDate(dateKey, amount) {
  const date = new Date(`${dateKey}T12:00:00`);
  date.setDate(date.getDate() + amount);
  return date.toISOString().slice(0, 10);
}

function getAttemptHash(key = "") {
  let hash = 0;
  const str = String(key || "default");
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return `attempt_${Math.abs(hash)}`;
}

function readProgress(attemptKey) {
  const hashKey = getAttemptHash(attemptKey);
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    const attempts = parsed.attempts || {};
    return {
      completed: attempts[hashKey] || {},
      practiceDates: parsed.practiceDates || {},
      completedDays: parsed.completedDays || {},
    };
  } catch {
    return { completed: {}, practiceDates: {}, completedDays: {} };
  }
}

function calculateStreak(practiceDates) {
  const active = new Set(
    Object.entries(practiceDates)
      .filter(([, ids]) => Array.isArray(ids) && ids.length)
      .map(([date]) => date)
  );
  if (!active.size) return 0;

  const today = todayKey();
  let cursor = active.has(today) ? today : shiftDate(today, -1);
  let streak = 0;
  while (active.has(cursor)) {
    streak += 1;
    cursor = shiftDate(cursor, -1);
  }
  return streak;
}

function motivation({ completed, total, streak, fallback }) {
  if (total > 0 && completed === total) {
    return "Practice cycle completed. Make a fresh recording and use the new feedback to decide the next practice cycle.";
  }
  if (streak >= 5) {
    return "Your practice routine is consistent. Keep sessions focused and use a fresh answer to test whether the same focus areas appear again.";
  }
  if (streak >= 2) {
    return "You are building consistency. Repeat one difficult answer before adding another question.";
  }
  return fallback || "Complete one focused task today, then record a short answer using the pattern you practised.";
}

export default function PracticePlan({
  activities = [],
  sevenDayPlan = [],
  motivationText = "",
  onRecordAgain,
  attemptKey = "",
}) {
  const [progress, setProgress] = useState(() => readProgress(attemptKey));

  useEffect(() => {
    setProgress(readProgress(attemptKey));
  }, [attemptKey]);

  useEffect(() => {
    const hashKey = getAttemptHash(attemptKey);
    try {
      const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
      parsed.attempts = parsed.attempts || {};
      parsed.attempts[hashKey] = progress.completed;
      parsed.practiceDates = progress.practiceDates;
      parsed.completedDays = progress.completedDays;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(parsed));
    } catch {}
  }, [progress, attemptKey]);

  const completedCount = activities.filter((item) => progress.completed[item.id]).length;
  const total = activities.length;
  const completionPercent = total ? Math.round((completedCount / total) * 100) : 0;
  const practiceDays = Object.values(progress.practiceDates).filter(
    (ids) => Array.isArray(ids) && ids.length
  ).length;
  const streak = useMemo(
    () => calculateStreak(progress.practiceDates),
    [progress.practiceDates]
  );
  const todayCompleted = progress.practiceDates[todayKey()]?.length || 0;
  const nextActivity = activities.find((item) => !progress.completed[item.id]);
  const note = motivation({
    completed: completedCount,
    total,
    streak,
    fallback: motivationText,
  });

  function toggleActivity(id) {
    const date = todayKey();
    setProgress((current) => {
      const completed = { ...current.completed };
      const practiceDates = { ...current.practiceDates };
      const todayIds = new Set(practiceDates[date] || []);

      if (completed[id]) {
        delete completed[id];
        todayIds.delete(id);
      } else {
        completed[id] = date;
        todayIds.add(id);
      }

      practiceDates[date] = Array.from(todayIds);
      return { ...current, completed, practiceDates };
    });
  }

  function toggleDay(day) {
    setProgress((current) => ({
      ...current,
      completedDays: {
        ...current.completedDays,
        [day]: !current.completedDays[day],
      },
    }));
  }

  function resetProgress() {
    if (!window.confirm("Reset practice completion on this browser?")) return;
    setProgress({ completed: {}, practiceDates: {}, completedDays: {} });
  }

  const milestone =
    completedCount >= 8 ? "Practice Finisher" :
    streak >= 5 ? "Consistency Builder" :
    completedCount >= 3 ? "Focused Practitioner" :
    "Practice Starter";

  return (
    <section className="growth-section">
      <div className="journey-hero panel">
        <div className="journey-copy">
          <div className="section-kicker">PERSONAL IMPROVEMENT JOURNEY</div>
          <h2>Turn feedback into a repeatable practice routine</h2>
          <p className="section-copy">
            The bar below measures completed practice tasks only. It is not a communication score.
          </p>
        </div>
        <div className="milestone-badge">✦ {milestone}</div>

        <div className="journey-stats">
          <div><strong>{completedCount}/{total || 0}</strong><span>Tasks completed</span></div>
          <div><strong>{practiceDays}</strong><span>Practice days</span></div>
          <div><strong>{streak}</strong><span>Day streak</span></div>
          <div><strong>{todayCompleted}</strong><span>Done today</span></div>
        </div>

        <div className="progress-heading">
          <span>Practice completion</span>
          <strong>{completionPercent}%</strong>
        </div>
        <div className="progress-track" aria-label="Practice completion">
          <div className="progress-fill" style={{ width: `${completionPercent}%` }} />
        </div>
        <div className="motivation-card">{note}</div>
      </div>

      {nextActivity && (
        <div className="next-task panel">
          <div>
            <div className="section-kicker">NEXT BEST TASK</div>
            <h3>{nextActivity.title}</h3>
            <p>{nextActivity.description}</p>
          </div>
          <div className="next-task-meta">
            <span>{nextActivity.category}</span>
            <strong>{nextActivity.durationMinutes || 8} min</strong>
          </div>
        </div>
      )}

      <div className="practice-layout">
        <section className="panel">
          <div className="section-kicker">PERSONAL TASKS</div>
          <h2>Complete, rehearse, repeat</h2>
          <div className="activity-list">
            {activities.map((activity) => {
              const done = Boolean(progress.completed[activity.id]);
              return (
                <button
                  type="button"
                  className={`activity-card ${done ? "done" : ""}`}
                  key={activity.id}
                  onClick={() => toggleActivity(activity.id)}
                >
                  <span className="activity-check">{done ? "✓" : ""}</span>
                  <span className="activity-body">
                    <span className="activity-meta">
                      {activity.category} · {activity.durationMinutes || 8} min
                    </span>
                    <strong>{activity.title}</strong>
                    <span>{activity.description}</span>
                    {activity.successCheck && (
                      <em>Self-check: {activity.successCheck}</em>
                    )}
                  </span>
                </button>
              );
            })}
          </div>
        </section>

        <section className="panel">
          <div className="section-kicker">7-DAY SPRINT</div>
          <h2>One small focus each day</h2>
          <div className="week-list">
            {sevenDayPlan.map((day) => {
              const done = Boolean(progress.completedDays[day.day]);
              return (
                <article className={`day-card ${done ? "done" : ""}`} key={day.day}>
                  <button className="day-check" onClick={() => toggleDay(day.day)}>
                    {done ? "✓" : day.day}
                  </button>
                  <div>
                    <span>DAY {day.day}</span>
                    <h3>{day.title}</h3>
                    <p>{day.focus}</p>
                    {!!day.tasks?.length && (
                      <ul>{day.tasks.map((task) => <li key={task}>{task}</li>)}</ul>
                    )}
                    {day.reflection && <small>Reflect: {day.reflection}</small>}
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      </div>

      <div className="practice-footer panel">
        <div>
          <div className="section-kicker">NEW ATTEMPT</div>
          <h2>Practise, then generate fresh evidence</h2>
          <p>
            Record a new answer after practice. The system will run Whisper, the saved ML model, and the coaching layer again on the new response.
          </p>
        </div>
        <div className="practice-footer-actions">
          <button className="secondary-button" onClick={resetProgress}>Reset checklist</button>
          <button className="primary-button" onClick={onRecordAgain}>Record another answer</button>
        </div>
      </div>
    </section>
  );
}
