import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  analyzeAudio,
  analyzeText,
  getHistory,
  getTrainingSummary,
  healthCheck
} from "./api.js";

function classNames(...xs) {
  return xs.filter(Boolean).join(" ");
}

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function Badge({ tone = "neutral", children }) {
  return (
    <span className={classNames("badge", `badge-${tone}`)}>{children}</span>
  );
}

function ScoreBadge({ levelText }) {
  const t = String(levelText || "").toLowerCase();
  if (t.includes("excellent")) return <Badge tone="good">Excellent</Badge>;
  if (t.includes("good")) return <Badge tone="good">Good</Badge>;
  if (t.includes("average")) return <Badge tone="warn">Average</Badge>;
  if (t.includes("poor")) return <Badge tone="bad">Poor</Badge>;
  return <Badge tone="neutral">Unknown</Badge>;
}

function normalizeLevel({ levelText, predictedLevel }) {
  const t = String(levelText || "").toLowerCase();
  if (t.includes("excellent")) return 4;
  if (t.includes("good")) return 3;
  if (t.includes("average")) return 2;
  if (t.includes("poor")) return 1;
  const n = Number(predictedLevel || 0);
  if ([1, 2, 3, 4].includes(n)) return n;
  return 0;
}

function levelLabel(n, levelText) {
  if (levelText) return levelText;
  if (n === 4) return "Excellent Communication";
  if (n === 3) return "Good Communication";
  if (n === 2) return "Average Communication";
  if (n === 1) return "Poor Communication";
  return "Communication Level";
}

function levelMeaning(n) {
  if (n === 4) return "Clear, structured, professional. Ready for interviews.";
  if (n === 3) return "Good clarity and flow. Improve impact with stronger examples.";
  if (n === 2) return "Understandable, but needs better structure and professional wording.";
  if (n === 1) return "Needs improvement: clarity, confidence, and structure are weak.";
  return "Run an analysis to see your level.";
}

function levelTone(n) {
  if (n === 4 || n === 3) return "good";
  if (n === 2) return "warn";
  if (n === 1) return "bad";
  return "neutral";
}

function LevelMeter({ levelText, predictedLevel }) {
  const n = normalizeLevel({ levelText, predictedLevel });
  const pct = n ? Math.round((n / 4) * 100) : 0;
  const tone = levelTone(n);

  return (
    <div className={classNames("level-card", `level-${tone}`)}>
      <div className="level-head">
        <div>
          <div className="level-title">{levelLabel(n, levelText)}</div>
          <div className="level-meaning">{levelMeaning(n)}</div>
        </div>
        <div className="level-score">
          <div className="level-score-big">{n ? `${n}/4` : "—"}</div>
          <div className="level-score-sub">{pct ? `${pct}%` : ""}</div>
        </div>
      </div>
      <div className="meter">
        <div className="meter-track">
          <div className="meter-fill" style={{ width: `${pct}%` }} />
        </div>
        <div className="meter-labels">
          <span>Poor</span>
          <span>Average</span>
          <span>Good</span>
          <span>Excellent</span>
        </div>
      </div>
    </div>
  );
}

function guidanceForLevel(n) {
  if (n === 4) {
    return {
      headline: "You’re interview-ready. Focus on polish + impact.",
      priorities: [
        "Add measurable results (numbers, impact, outcome) in every answer.",
        "Keep answers concise (60–90 seconds) with a strong closing line.",
        "Practice role-specific stories (STAR method) for 5–7 common questions."
      ],
      english: [
        "Maintain a steady pace and avoid long sentences.",
        "Use stronger action verbs: implemented, optimized, automated, delivered."
      ],
      professional: [
        "Mirror the job description keywords naturally (tools, responsibilities).",
        "Prepare 2–3 questions to ask the interviewer about the team/project."
      ]
    };
  }

  if (n === 3) {
    return {
      headline: "Good communication. Upgrade structure and confidence for top results.",
      priorities: [
        "Use a fixed structure: Intro → Skills → Project → Your role → Result → Why this role.",
        "Give 1 concrete example (tool/feature) instead of general statements.",
        "End with a confident close: ‘I’m excited to contribute to…’"
      ],
      english: [
        "Reduce filler words (like/umm/actually). Pause instead.",
        "Speak in short sentences and use connectors: first, then, because, result."
      ],
      professional: [
        "Explain ownership clearly: ‘I designed…’, ‘I integrated…’, ‘I tested…’.",
        "Quantify where possible: performance, time saved, users, accuracy."
      ]
    };
  }

  if (n === 2) {
    return {
      headline: "Average level. Biggest gap is structure + professional wording.",
      priorities: [
        "Use STAR method for every project answer (Situation, Task, Action, Result).",
        "Add missing details: tech stack, what you built, your exact responsibility.",
        "Practice 10 minutes daily speaking from bullet points (not memorized)."
      ],
      english: [
        "Practice pronunciation + clarity: read 1 paragraph aloud daily.",
        "Replace weak words: ‘maybe’ → ‘I believe’; ‘things’ → ‘features’; ‘some’ → specific."
      ],
      professional: [
        "Learn 15 job-role keywords and use 5 of them in your answer naturally.",
        "Prepare a 45–60 second ‘Tell me about yourself’ script and repeat until fluent."
      ]
    };
  }

  if (n === 1) {
    return {
      headline: "Poor level. Focus on basics: clarity, confidence, and sentence flow.",
      priorities: [
        "Speak slower. Use simple sentences. One idea per sentence.",
        "Prepare a short introduction: name → role goal → 3 skills → 1 project → result.",
        "Practice with recordings: listen, note mistakes, repeat improved version."
      ],
      english: [
        "Daily routine (15 min): 5 min reading aloud + 5 min shadowing + 5 min speaking.",
        "Use basic grammar patterns: ‘I have…’, ‘I worked on…’, ‘I improved…’"
      ],
      professional: [
        "Avoid ‘I don’t know’—say: ‘I’m learning this, and my plan is…’.",
        "Write a small role-aligned project summary and reuse it in interviews."
      ]
    };
  }

  return {
    headline: "Run an analysis to get personalized guidance.",
    priorities: [],
    english: [],
    professional: []
  };
}

function extractSkillGaps({ weaknesses, suggestions }) {
  const text = [...(weaknesses || []), ...(suggestions || [])].join(" ").toLowerCase();
  const gaps = [];

  const add = (key, label) => {
    if (!gaps.find((g) => g.key === key)) gaps.push({ key, label });
  };

  if (/(structure|star|flow|organized|organised)/.test(text)) add("structure", "Answer structure (STAR / clear flow)");
  if (/(clarity|clear|too short|detail|more detail)/.test(text)) add("clarity", "Clarity and completeness");
  if (/(filler|um|uh|like|pause)/.test(text)) add("fluency", "Fluency (reduce filler, steady pace)");
  if (/(professional|keyword|wording|terminology)/.test(text)) add("professional", "Professional wording / role keywords");
  if (/(confidence|confident|nervous)/.test(text)) add("confidence", "Confidence and delivery");
  if (/(grammar|sentence|pronunciation)/.test(text)) add("english", "English basics (grammar/pronunciation)");
  if (/(result|impact|measure|metric|number)/.test(text)) add("impact", "Impact (results, metrics, outcomes)");

  if (!gaps.length) {
    add("structure", "Answer structure (STAR / clear flow)");
    add("professional", "Professional wording / role keywords");
    add("impact", "Impact (results, metrics, outcomes)");
  }

  return gaps;
}

function buildGapChart({ weaknesses, suggestions, n }) {
  const text = [...(weaknesses || []), ...(suggestions || [])].join(" ").toLowerCase();
  const base = n === 4 ? 78 : n === 3 ? 62 : n === 2 ? 42 : n === 1 ? 28 : 40;

  const bump = (re, v) => (re.test(text) ? v : 0);
  const clamp = (x) => Math.max(10, Math.min(95, x));

  // Heuristic “scores” for visualization only (no model scores shown)
  const structure = clamp(base - bump(/(structure|star|flow|organized|organised)/, 18));
  const clarity = clamp(base - bump(/(clarity|clear|too short|detail|more detail)/, 18));
  const fluency = clamp(base - bump(/(filler|um|uh|like|pause)/, 14));
  const professional = clamp(base - bump(/(professional|keyword|wording|terminology)/, 18));
  const confidence = clamp(base - bump(/(confidence|confident|nervous)/, 14));
  const impact = clamp(base - bump(/(result|impact|measure|metric|number)/, 16));

  return [
    { key: "structure", label: "Structure", value: structure },
    { key: "clarity", label: "Clarity", value: clarity },
    { key: "fluency", label: "Fluency", value: fluency },
    { key: "professional", label: "Professional", value: professional },
    { key: "confidence", label: "Confidence", value: confidence },
    { key: "impact", label: "Impact", value: impact }
  ];
}

function FrameworkPanel({ jobRole }) {
  return (
    <div className="guidance-box">
      <div className="guidance-title">Framework to follow (use this in every answer)</div>
      <ol className="steps">
        <li>
          <b>Hook (1 line)</b>: “I’m a {jobRole || "candidate"} skilled in X and Y.”
        </li>
        <li>
          <b>Skills</b>: 2–3 job keywords (tools + strengths).
        </li>
        <li>
          <b>Project (STAR)</b>: Situation → Task → Action → Result.
        </li>
        <li>
          <b>Role ownership</b>: clearly say what <b>you</b> did.
        </li>
        <li>
          <b>Impact</b>: include numbers or outcomes (time, quality, users, accuracy).
        </li>
        <li>
          <b>Close (1 line)</b>: why you fit this role + confidence.
        </li>
      </ol>
      <div className="muted" style={{ marginTop: 8 }}>
        Target length: <b>60–90 seconds</b>. Prefer short sentences and clear pauses.
      </div>
    </div>
  );
}

function WeeklyPlanPanel({ n }) {
  const plan =
    n === 4
      ? [
          "Day 1: Refine your 60–90 sec self-introduction with metrics.",
          "Day 2: Practice 3 STAR stories (project, teamwork, problem).",
          "Day 3: Mock interview (record → review → improve).",
          "Day 4: Add role keywords + stronger verbs.",
          "Day 5: Practice HR questions + confident closing.",
          "Day 6: Technical explanation practice (simple + clear).",
          "Day 7: Full mock interview + final polish."
        ]
      : n === 3
        ? [
            "Day 1: Create a structured self-introduction template.",
            "Day 2: Write 2 STAR stories and speak them without reading.",
            "Day 3: Record 2 answers; remove filler words.",
            "Day 4: Add professional keywords from the job description.",
            "Day 5: Improve closing lines + confidence delivery.",
            "Day 6: Practice pronunciation (read aloud + shadowing).",
            "Day 7: Full mock interview + compare improvement."
          ]
        : n === 2
          ? [
              "Day 1: Learn STAR method; write 2 short STAR answers.",
              "Day 2: Practice 10 minutes speaking from bullet points.",
              "Day 3: Record + fix clarity (add details: stack, role, result).",
              "Day 4: Replace weak words with specific professional words.",
              "Day 5: Practice pronunciation + slower speaking pace.",
              "Day 6: Repeat the same answer until fluent (3 times).",
              "Day 7: Mock interview (record) + re-check level."
            ]
          : [
              "Day 1: Build a simple intro (name, role goal, 3 skills, 1 project).",
              "Day 2: Speak slowly with short sentences (one idea per sentence).",
              "Day 3: Read aloud 5 minutes + shadow 5 minutes + speak 5 minutes.",
              "Day 4: Practice 1 STAR story (very simple).",
              "Day 5: Record + remove filler words; pause instead.",
              "Day 6: Repeat the same answer until clear (3 times).",
              "Day 7: Try again and compare the new level."
            ];

  return (
    <div className="guidance-box">
      <div className="guidance-title">7‑Day preparation plan (do this before interview)</div>
      <ul className="list">
        {plan.map((x, idx) => (
          <li key={idx}>{x}</li>
        ))}
      </ul>
    </div>
  );
}

function GapChart({ items }) {
  return (
    <div className="guidance-box">
      <div className="guidance-title">Skill chart (visual idea of gaps)</div>
      <div className="chart">
        {items.map((it) => (
          <div className="bar-row" key={it.key}>
            <div className="bar-label">{it.label}</div>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${it.value}%` }} />
            </div>
            <div className="bar-val">{it.value}%</div>
          </div>
        ))}
      </div>
      <div className="muted" style={{ marginTop: 8 }}>
        Use the chart to decide what to practice first (lowest bars = biggest gap).
      </div>
    </div>
  );
}

function GuidancePanel({ jobRole, jobDescription, levelText, predictedLevel, weaknesses, suggestions }) {
  const n = normalizeLevel({ levelText, predictedLevel });
  const g = guidanceForLevel(n);
  const gaps = extractSkillGaps({ weaknesses, suggestions });
  const chart = buildGapChart({ weaknesses, suggestions, n });

  return (
    <div className="panel">
      <div className="section-title">Career Guidance + Skill Gap (Action Plan)</div>
      <div className="muted">
        Target role: <b>{jobRole || "—"}</b>
      </div>
      {jobDescription ? (
        <div className="muted" style={{ marginTop: 6 }}>
          Job focus: {jobDescription.length > 180 ? `${jobDescription.slice(0, 180)}…` : jobDescription}
        </div>
      ) : null}

      <div className="guidance-headline">{g.headline}</div>

      <div className="guidance-grid">
        <FrameworkPanel jobRole={jobRole} />
        <GapChart items={chart} />
        <div className="guidance-box">
          <div className="guidance-title">Top priorities (next 7 days)</div>
          <ul className="list">
            {g.priorities.map((x, idx) => (
              <li key={idx}>{x}</li>
            ))}
          </ul>
        </div>
        <div className="guidance-box">
          <div className="guidance-title">English speaking improvement</div>
          <ul className="list">
            {g.english.map((x, idx) => (
              <li key={idx}>{x}</li>
            ))}
          </ul>
        </div>
        <div className="guidance-box">
          <div className="guidance-title">Professional interview skills</div>
          <ul className="list">
            {g.professional.map((x, idx) => (
              <li key={idx}>{x}</li>
            ))}
          </ul>
        </div>
        <WeeklyPlanPanel n={n} />
        <div className="guidance-box">
          <div className="guidance-title">Your skill gaps (based on this answer)</div>
          <ul className="list">
            {gaps.map((x) => (
              <li key={x.key}>{x.label}</li>
            ))}
          </ul>
          <div className="muted" style={{ marginTop: 8 }}>
            Tip: Re-record the same answer after improvements and compare the level.
          </div>
        </div>
      </div>
    </div>
  );
}

function Card({ title, right, children }) {
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">{title}</div>
        <div className="card-right">{right}</div>
      </div>
      <div className="card-body">{children}</div>
    </div>
  );
}

function useSpeechRecognition() {
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  const available = !!SpeechRecognition;
  const recognitionRef = useRef(null);

  const [listening, setListening] = useState(false);
  const [finalText, setFinalText] = useState("");
  const [interimText, setInterimText] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!available) return;
    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = "en-US";

    rec.onresult = (event) => {
      let interim = "";
      let finalChunk = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const res = event.results[i];
        const txt = res[0]?.transcript || "";
        if (res.isFinal) finalChunk += txt;
        else interim += txt;
      }
      if (finalChunk) setFinalText((prev) => `${prev}${prev ? " " : ""}${finalChunk}`.trim());
      setInterimText(interim.trim());
    };

    rec.onerror = (e) => {
      setError(e?.error || "Speech recognition error");
      setListening(false);
    };

    rec.onend = () => {
      setListening(false);
      setInterimText("");
    };

    recognitionRef.current = rec;
    return () => {
      try {
        rec.stop();
      } catch {
        // ignore
      }
    };
  }, [available]);

  const start = () => {
    setError("");
    if (!available || !recognitionRef.current) return;
    try {
      recognitionRef.current.start();
      setListening(true);
    } catch (e) {
      setError(e?.message || "Unable to start recognition");
      setListening(false);
    }
  };

  const stop = () => {
    if (!recognitionRef.current) return;
    try {
      recognitionRef.current.stop();
    } catch {
      // ignore
    }
  };

  const reset = () => {
    setFinalText("");
    setInterimText("");
    setError("");
  };

  const transcript = useMemo(() => {
    const joined = [finalText, interimText].filter(Boolean).join(" ").trim();
    return joined;
  }, [finalText, interimText]);

  return {
    available,
    listening,
    transcript,
    error,
    start,
    stop,
    reset,
    finalText,
    interimText
  };
}

function useAudioRecorder() {
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);

  const [recording, setRecording] = useState(false);
  const [error, setError] = useState("");
  const [recordedBlob, setRecordedBlob] = useState(null);

  const isSupported =
    typeof navigator !== "undefined" &&
    !!navigator.mediaDevices?.getUserMedia &&
    typeof window !== "undefined" &&
    typeof window.MediaRecorder !== "undefined";

  const start = async () => {
    setError("");
    setRecordedBlob(null);
    chunksRef.current = [];

    if (!isSupported) {
      setError("Audio recording is not supported in this browser.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      let mimeType = "";
      const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/ogg"];
      mimeType = candidates.find((t) => window.MediaRecorder.isTypeSupported?.(t)) || "";

      const mr = new window.MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = mr;

      mr.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };

      mr.onerror = () => {
        setError("Recording failed. Please try again.");
        setRecording(false);
      };

      mr.onstop = () => {
        setRecording(false);
        try {
          const blob = new Blob(chunksRef.current, { type: mr.mimeType || "audio/webm" });
          setRecordedBlob(blob);
        } catch {
          setError("Failed to build recorded audio.");
        }
      };

      mr.start();
      setRecording(true);
    } catch (e) {
      setError(e?.message || "Microphone permission denied.");
    }
  };

  const stop = () => {
    setError("");
    const mr = mediaRecorderRef.current;
    if (!mr) return;
    try {
      if (mr.state !== "inactive") mr.stop();
    } catch {
      // ignore
    }
    const stream = streamRef.current;
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
  };

  const reset = () => {
    setError("");
    setRecordedBlob(null);
    chunksRef.current = [];
  };

  const recordedFile = useMemo(() => {
    if (!recordedBlob) return null;
    const ext = recordedBlob.type.includes("ogg") ? "ogg" : "webm";
    return new File([recordedBlob], `live_recording.${ext}`, { type: recordedBlob.type || "audio/webm" });
  }, [recordedBlob]);

  return { isSupported, recording, error, recordedBlob, recordedFile, start, stop, reset };
}

function ResultView({ result }) {
  if (!result) return null;
  const r = result?.data || result;

  return (
    <div className="result">
      <LevelMeter
        levelText={r.communicationSkillLevel}
        predictedLevel={r.predictedLevel}
      />

      <div className="result-grid">
        <div className="result-col">
          <div className="section-title">Transcript</div>
          <div className="panel">
            <div className="pre">{r.transcript}</div>
          </div>
        </div>
        <div className="result-col">
          <div className="section-title">Feedback</div>
          <div className="panel">
            <div className="pre">{r.feedback}</div>
          </div>
        </div>
      </div>

      <div className="result-grid">
        <div className="panel">
          <div className="section-title">Strengths</div>
          {Array.isArray(r.strengths) && r.strengths.length ? (
            <ul className="list">
              {r.strengths.map((s, idx) => (
                <li key={idx}>{s}</li>
              ))}
            </ul>
          ) : (
            <div className="muted">No strengths returned.</div>
          )}
        </div>
        <div className="panel">
          <div className="section-title">Weaknesses</div>
          {Array.isArray(r.weaknesses) && r.weaknesses.length ? (
            <ul className="list">
              {r.weaknesses.map((s, idx) => (
                <li key={idx}>{s}</li>
              ))}
            </ul>
          ) : (
            <div className="muted">No weaknesses returned.</div>
          )}
        </div>
      </div>

      <div className="panel">
        <div className="section-title">Suggestions</div>
        {Array.isArray(r.suggestions) && r.suggestions.length ? (
          <ul className="list">
            {r.suggestions.map((s, idx) => (
              <li key={idx}>{s}</li>
            ))}
          </ul>
        ) : (
          <div className="muted">No suggestions returned.</div>
        )}
      </div>

      <div className="panel">
        <div className="section-title">Better Answer Example</div>
        <div className="pre">{r.betterAnswerExample}</div>
      </div>
    </div>
  );
}

function TrainingSummaryCard({ summary }) {
  const data = summary?.data?.data;
  if (!data) return null;

  const best = data.bestModel;
  const results = data.modelResults?.models || [];

  return (
    <Card
      title="Model Training Summary"
      right={<Badge tone="neutral">From backend/models JSON</Badge>}
    >
      <div className="grid2">
        <div className="panel">
          <div className="section-title">Best Model</div>
          <div className="kv">
            <div className="kv-row">
              <div className="kv-k">Model</div>
              <div className="kv-v">{best?.best_model}</div>
            </div>
            <div className="kv-row">
              <div className="kv-k">Accuracy</div>
              <div className="kv-v">{best?.accuracy}</div>
            </div>
            <div className="kv-row">
              <div className="kv-k">F1</div>
              <div className="kv-v">{best?.f1_score}</div>
            </div>
            <div className="kv-row">
              <div className="kv-k">Saved</div>
              <div className="kv-v">{best?.saved_model_path}</div>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="section-title">Compared Models</div>
          <div className="table">
            <div className="tr th">
              <div>Model</div>
              <div>Accuracy</div>
              <div>F1</div>
            </div>
            {results.map((m, idx) => (
              <div className="tr" key={idx}>
                <div>{m.model_name}</div>
                <div>{m.accuracy}</div>
                <div>{m.f1_score ?? m.f1}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState("analyze");
  const [apiStatus, setApiStatus] = useState({ ok: false, message: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [training, setTraining] = useState(null);

  const [jobRole, setJobRole] = useState("Software Engineer (MERN Stack)");
  const [jobDescription, setJobDescription] = useState(
    "Looking for a MERN Stack developer with React, Node.js, Express, and MongoDB experience. Strong communication, teamwork, and problem solving."
  );
  const [question, setQuestion] = useState(
    "Tell me about yourself and explain your skills, experience, and career goals."
  );
  const [jobDetailsSubmitted, setJobDetailsSubmitted] = useState(false);
  const analyzerRef = useRef(null);

  const [audioFile, setAudioFile] = useState(null);
  const speech = useSpeechRecognition();
  const recorder = useAudioRecorder();

  const refreshHistory = async () => {
    const h = await getHistory();
    setHistory(h?.data || []);
  };

  useEffect(() => {
    (async () => {
      try {
        const h = await healthCheck();
        setApiStatus({ ok: true, message: h?.message || "Backend OK" });
      } catch (e) {
        setApiStatus({ ok: false, message: e?.message || "Backend not reachable" });
      }

      try {
        const t = await getTrainingSummary();
        setTraining(t);
      } catch {
        // training summary depends on backend; ignore for now
      }
    })();
  }, []);

  const runTextAnalysis = async () => {
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const payload = {
        transcript: speech.transcript,
        jobRole,
        jobDescription,
        question
      };
      const r = await analyzeText(payload);
      setResult(r);
      await refreshHistory();
    } catch (e) {
      setError(e?.message || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const runAudioAnalysis = async () => {
    setError("");
    setResult(null);
    setLoading(true);
    try {
      if (!audioFile) throw new Error("Please choose an audio file first.");
      const r = await analyzeAudio({ file: audioFile, jobRole, jobDescription, question });
      setResult(r);
      await refreshHistory();
    } catch (e) {
      setError(e?.message || "Audio analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const runRecordedAudioAnalysis = async () => {
    setError("");
    setResult(null);
    setLoading(true);
    try {
      if (!recorder.recordedFile) throw new Error("Please record your voice first.");
      const r = await analyzeAudio({ file: recorder.recordedFile, jobRole, jobDescription, question });
      setResult(r);
      await refreshHistory();
    } catch (e) {
      setError(e?.message || "Recorded audio analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const submitJobDetails = () => {
    setError("");
    const role = String(jobRole || "").trim();
    const desc = String(jobDescription || "").trim();
    if (!role) {
      setError("Please enter the job role.");
      return;
    }
    if (!desc) {
      setError("Please enter the job description.");
      return;
    }
    setJobDetailsSubmitted(true);
    setTimeout(() => {
      analyzerRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark" />
          <div className="brand-text">
            <div className="brand-title">AI Interview</div>
            <div className="brand-subtitle">Communication Analyzer</div>
          </div>
        </div>

        <div className="nav">
          <button
            className={classNames("nav-item", activeTab === "analyze" && "active")}
            onClick={() => setActiveTab("analyze")}
          >
            MOC Sessions
          </button>
          <button
            className={classNames("nav-item", activeTab === "training" && "active")}
            onClick={() => setActiveTab("training")}
          >
            Training Summary
          </button>
          <button
            className={classNames("nav-item", activeTab === "history" && "active")}
            onClick={() => setActiveTab("history")}
          >
            History
          </button>
        </div>

        <div className="sidebar-footer">
          <div className="status">
            <div className="status-dot" data-ok={apiStatus.ok ? "1" : "0"} />
            <div className="status-text">
              <div className="status-title">Backend</div>
              <div className="status-sub">{apiStatus.message}</div>
            </div>
          </div>
        </div>
      </aside>

      <main className="main">
        <div className="topbar">
          <div className="topbar-title">Mock Interview Communication Analyzer</div>
          <div className="topbar-right" />
        </div>

        <div className="content">
          {activeTab === "analyze" && (
            <>
              <Card title="Job Details">
                <div className="form">
                  <div className="field">
                    <label>Target Job Role</label>
                    <input
                      value={jobRole}
                      onChange={(e) => setJobRole(e.target.value)}
                      placeholder="e.g., DevOps Engineer"
                    />
                  </div>
                  <div className="field">
                    <label>Job Description</label>
                    <textarea
                      value={jobDescription}
                      onChange={(e) => setJobDescription(e.target.value)}
                      rows={4}
                      placeholder="Paste the job description here (skills, responsibilities, requirements)."
                    />
                  </div>
                  <div className="row">
                    <button
                      className="btn btn-primary"
                      onClick={submitJobDetails}
                      disabled={loading}
                      type="button"
                    >
                      Test Communication Skill
                    </button>
                    {jobDetailsSubmitted ? (
                      <div className="muted">Job details saved. You can start analysis below.</div>
                    ) : (
                      <div className="muted">Fill job role + description, then click submit.</div>
                    )}
                  </div>
                </div>
              </Card>

              {jobDetailsSubmitted ? (
                <>
                  <div ref={analyzerRef} />
                  <Card
                    title="Interview Communication Skill Analyzer"
                    right={
                      <div className="toggle">
                        <button
                          className={classNames("toggle-btn", !audioFile && "active")}
                          onClick={() => setAudioFile(null)}
                          disabled={loading}
                          type="button"
                        >
                          Live Voice
                        </button>
                        <button
                          className={classNames("toggle-btn", !!audioFile && "active")}
                          onClick={() => {}}
                          disabled={loading}
                          type="button"
                        >
                          Audio File
                        </button>
                      </div>
                    }
                  >
                    <div className="form">
                      <div className="field">
                        <label>Interview Question</label>
                        <textarea
                          value={question}
                          onChange={(e) => setQuestion(e.target.value)}
                          rows={2}
                        />
                      </div>
                    </div>

                    <div className="grid2">
                      <div className="panel dashed">
                        <div className="section-title">Live Voice (Speech-to-Text)</div>
                        {!speech.available ? (
                          <div className="muted">
                            Speech recognition is not available (or blocked). Use the recorder below to capture your voice and analyze it.
                          </div>
                        ) : (
                          <>
                            <div className="row">
                              <button
                                className="btn"
                                onClick={speech.listening ? speech.stop : speech.start}
                                disabled={loading}
                                type="button"
                              >
                                {speech.listening ? "Stop" : "Start"} Mic
                              </button>
                              <button
                                className="btn btn-ghost"
                                onClick={speech.reset}
                                disabled={loading}
                                type="button"
                              >
                                Reset
                              </button>
                            </div>
                            {speech.error ? <div className="error">{speech.error}</div> : null}
                            <div className="preview">
                              <div className="muted">
                                Speak now. Your words will appear here.
                              </div>
                              <div className="pre">{speech.transcript || "—"}</div>
                            </div>
                            <div className="row">
                              <button
                                className="btn btn-primary"
                                onClick={runTextAnalysis}
                                disabled={loading || !speech.transcript}
                                type="button"
                              >
                                {loading ? "Analyzing..." : "Analyze Transcript"}
                              </button>
                            </div>
                          </>
                        )}

                        <div className="divider" />
                        <div className="section-title">Live Voice (Record → Transcribe)</div>
                        {!recorder.isSupported ? (
                          <div className="muted">
                            Audio recording is not supported in this browser. Use Chrome/Edge.
                          </div>
                        ) : (
                          <>
                            <div className="row">
                              <button
                                className={classNames("btn", recorder.recording && "btn-primary")}
                                onClick={recorder.recording ? recorder.stop : recorder.start}
                                disabled={loading}
                                type="button"
                              >
                                {recorder.recording ? "Stop Recording" : "Start Recording"}
                              </button>
                              <button
                                className="btn btn-ghost"
                                onClick={recorder.reset}
                                disabled={loading || recorder.recording}
                                type="button"
                              >
                                Reset
                              </button>
                            </div>
                            {recorder.error ? <div className="error">{recorder.error}</div> : null}
                            {recorder.recordedBlob ? (
                              <>
                                <audio controls className="audio">
                                  <source src={URL.createObjectURL(recorder.recordedBlob)} />
                                </audio>
                                <div className="row">
                                  <button
                                    className="btn btn-primary"
                                    onClick={runRecordedAudioAnalysis}
                                    disabled={loading || !recorder.recordedFile}
                                    type="button"
                                  >
                                    {loading ? "Analyzing..." : "Analyze Recorded Audio"}
                                  </button>
                                </div>
                              </>
                            ) : (
                              <div className="muted">Record 15–45 seconds for best results.</div>
                            )}
                          </>
                        )}
                      </div>

                      <div className="panel dashed">
                        <div className="section-title">Upload Interview Audio</div>
                        <div className="muted">Supported: WAV, MP3, M4A, OGG, WEBM (≤ 25MB)</div>
                        <div className="row">
                          <input
                            type="file"
                            accept="audio/*"
                            onChange={(e) => setAudioFile(e.target.files?.[0] || null)}
                            disabled={loading}
                          />
                        </div>
                        {audioFile ? (
                          <div className="muted">
                            Selected: <b>{audioFile.name}</b>
                          </div>
                        ) : (
                          <div className="muted">No file selected.</div>
                        )}
                        <div className="row">
                          <button
                            className="btn btn-primary"
                            onClick={runAudioAnalysis}
                            disabled={loading || !audioFile}
                            type="button"
                          >
                            {loading ? "Analyzing..." : "Transcribe + Analyze Audio"}
                          </button>
                        </div>
                      </div>
                    </div>

                    {error ? <div className="error">{error}</div> : null}
                  </Card>

                  <ResultView result={result?.data ? result.data : result} />
                  {result ? (
                    <GuidancePanel
                      jobRole={jobRole}
                      jobDescription={jobDescription}
                      levelText={(result?.data ? result.data : result)?.communicationSkillLevel}
                      predictedLevel={(result?.data ? result.data : result)?.predictedLevel}
                      weaknesses={(result?.data ? result.data : result)?.weaknesses}
                      suggestions={(result?.data ? result.data : result)?.suggestions}
                    />
                  ) : null}
                </>
              ) : null}
            </>
          )}

          {activeTab === "training" && (
            <>
              {training ? (
                <TrainingSummaryCard summary={training} />
              ) : (
                <Card title="Model Training Summary">
                  <div className="muted">
                    Training summary will load after backend is running.
                  </div>
                </Card>
              )}
            </>
          )}

          {activeTab === "history" && (
            <Card title="Recent Analyses" right={<button className="btn btn-ghost" onClick={refreshHistory} type="button">Refresh</button>}>
              {history.length ? (
                <div className="table">
                  <div className="tr th">
                    <div>When</div>
                    <div>Type</div>
                    <div>Level</div>
                    <div>Role</div>
                  </div>
                  {history.map((h) => (
                    <button
                      key={h._id}
                      className="tr tr-btn"
                      onClick={() => setResult(h)}
                      type="button"
                    >
                      <div>{formatDate(h.createdAt)}</div>
                      <div>{h.inputType}</div>
                      <div>{h.communicationSkillLevel || "—"}</div>
                      <div className="truncate">{h.jobRole || "—"}</div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="muted">No history yet. Run an analysis first.</div>
              )}
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}

