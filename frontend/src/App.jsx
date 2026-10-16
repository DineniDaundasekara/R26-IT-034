import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import {
  AlertTriangle,
  Award,
  Briefcase,
  CalendarRange,
  CheckCircle2,
  Clock3,
  Download,
  Flag,
  GraduationCap,
  History,
  Info,
  ListChecks,
  Loader2,
  Map,
  RefreshCcw,
  Shield,
  Sparkles,
  Target,
  Trash2,
  TrendingUp,
} from "lucide-react";
import "./App.css";
import { downloadCareerReportPdf } from "./generateReportPdf";

const API_BASE = "http://127.0.0.1:5000";
const API_URL = `${API_BASE}/predict`;
const HISTORY_URL = `${API_BASE}/history`;

const roleOptions = [
  "Cloud & DevOps",
  "Cyber Security",
  "Data Science / AI / ML",
  "Project Management / Business Analysis",
  "Quality Assurance / Testing",
  "Software Development / Engineering",
  "UI/UX & Product Design",
];

const experienceOptions = ["0-2 years", "3-5 years", "6-10 years", "10+ years"];
const learningOptions = ["0 hours", "1-3 hours", "4-7 hours", "8+ hours"];
const strategyOptions = [
  "Deep specialization",
  "Move to management roles",
  "Multi-skill generalization",
  "No clear strategy",
];
const updateFrequencyOptions = [
  "Continuously",
  "Regularly",
  "Occasionally",
  "Rarely",
];

const initialForm = {
  role: roleOptions[0],
  years_experience: experienceOptions[1],
  tech_stack_change: 3,
  weekly_learning_time: learningOptions[1],
  switch_confidence: 3,
  career_strategy: strategyOptions[0],
  skill_update_frequency: updateFrequencyOptions[1],
};

const visibleFields = [
  "role",
  "years_experience",
  "tech_stack_change",
  "weekly_learning_time",
  "switch_confidence",
  "career_strategy",
  "skill_update_frequency",
];

const blankForm = {
  role: "",
  years_experience: "",
  tech_stack_change: "",
  weekly_learning_time: "",
  switch_confidence: "",
  career_strategy: "",
  skill_update_frequency: "",
};

const indicatorMeta = [
  { key: "automationExposure", title: "Automation Exposure", icon: Sparkles },
  { key: "industryDomainStability", title: "Industry / Domain Stability", icon: Shield },
  { key: "jobMarketTrend", title: "Job Market Trend", icon: TrendingUp },
  { key: "learningActivity", title: "Learning Activity", icon: GraduationCap },
  { key: "skillUpdateBehavior", title: "Skill Update Behavior", icon: RefreshCcw },
  { key: "roleSwitchingConfidence", title: "Role-Switching Confidence", icon: Target },
  { key: "careerStrategyStatus", title: "Career Strategy Status", icon: Map },
];

function Badge({ children, tone = "neutral" }) {
  return <span className={`ui-badge tone-${tone}`}>{children}</span>;
}

function SectionCard({ title, icon: Icon, tone = "blue", children, className = "" }) {
  return (
    <section className={`panel-card ${className}`}>
      <div className="panel-card-head">
        {Icon && (
          <span className={`round-icon tone-${tone}`}>
            <Icon size={16} />
          </span>
        )}
        <h3>{title}</h3>
      </div>
      {children}
    </section>
  );
}

function SelectField({ label, name, value, onChange, options, full = false }) {
  return (
    <label className={`field ${full ? "full" : ""}`}>
      <span className="field-label">{label}</span>
      <select name={name} value={value} onChange={onChange} required>
        <option value="">Select...</option>
        {options.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
    </label>
  );
}

function SliderField({ label, name, value, onChange, helper }) {
  const isBlank = value === "" || value === null || value === undefined;
  return (
    <div className={`slider-field ${isBlank ? "is-blank" : ""}`}>
      <div className="slider-top">
        <span className="field-label">{label}</span>
        <span className="slider-bubble">{isBlank ? "—" : value}</span>
      </div>
      <input
        type="range"
        name={name}
        min="1"
        max="5"
        value={isBlank ? 1 : value}
        onChange={onChange}
      />
      {helper && <p className="field-help">{helper}</p>}
      {isBlank && <p className="field-help warn">Move the slider to set a value (1–5).</p>}
    </div>
  );
}

function IndicatorCard({ title, value, icon: Icon }) {
  const tone = indicatorTone(value);
  return (
    <article className={`indicator-card tone-${tone}`}>
      <div className="indicator-top">
        <span className="indicator-dot" />
        {Icon && <Icon size={16} />}
      </div>
      <h4>{title}</h4>
      <p>{value}</p>
    </article>
  );
}

function ReportSection({ tag, title, children, accent = "blue" }) {
  return (
    <section className={`report-section accent-${accent}`}>
      <div className="report-section-head">
        <Badge tone={accent}>{tag}</Badge>
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function indicatorTone(value) {
  const text = String(value || "").toLowerCase();
  if (text.includes("high") || text.includes("increase") || text.includes("continuous")) {
    return "high";
  }
  if (
    text.includes("low") ||
    text.includes("rare") ||
    text.includes("occasional") ||
    text.includes("decrease") ||
    text.includes("no clear")
  ) {
    return "low";
  }
  return "medium";
}

function badgeClassForRisk(level) {
  const text = (level || "").toLowerCase();
  if (text.includes("low")) return "risk-badge risk-low";
  if (text.includes("moderate")) return "risk-badge risk-moderate";
  if (text.includes("high")) return "risk-badge risk-high";
  return "risk-badge";
}

function formatHistoryDate(iso) {
  if (!iso) return "Unknown date";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function priorityTone(level) {
  const text = String(level || "").toLowerCase();
  if (text.includes("high")) return "high";
  if (text.includes("moderate") || text.includes("medium")) return "medium";
  if (text.includes("low")) return "low";
  return "neutral";
}

function ChecklistBlock({ title, items, icon: Icon }) {
  const list = Array.isArray(items) ? items.filter(Boolean) : [];
  return (
    <article className="soft-card checklist-card">
      <div className="soft-card-head">
        {Icon && <Icon size={16} />}
        <h3>{title}</h3>
      </div>
      {list.length ? (
        <ul className="checklist">
          {list.map((item) => (
            <li key={item}>
              <CheckCircle2 size={15} />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted-note">No items available.</p>
      )}
    </article>
  );
}

function TimelinePlanCard({ label, days, items, tone }) {
  const list = Array.isArray(items) ? items.filter(Boolean) : [];
  return (
    <article className={`timeline-plan-card tone-${tone}`}>
      <div className="timeline-plan-head">
        <span className="timeline-day-badge">{days}</span>
        <div>
          <p className="mini-label">{label}</p>
          <h4>{days}-Day Focus</h4>
        </div>
      </div>
      {list.length ? (
        <ol>
          {list.map((item, index) => (
            <li key={`${days}-${index}`}>
              <span>{index + 1}</span>
              <p>{item}</p>
            </li>
          ))}
        </ol>
      ) : (
        <p className="muted-note">No plan items available.</p>
      )}
    </article>
  );
}

function App() {
  const [formData, setFormData] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [historyItems, setHistoryItems] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [activeHistoryId, setActiveHistoryId] = useState(null);
  const resultsRef = useRef(null);

  const prediction = result?.modelPrediction;
  const indicators = result?.systemDerivedIndicators;
  const guidance = result?.aiGeneratedGuidance;
  const actionPlan = guidance?.careerResilienceActionPlan;
  const decisionNote = result?.decisionSupportNote;
  const hasActionPlanContent = Boolean(
    actionPlan &&
      (actionPlan.summary ||
        actionPlan.actionPriorityLevel ||
        (actionPlan.thirtyDayPlan || []).length ||
        (actionPlan.sixtyDayPlan || []).length ||
        (actionPlan.ninetyDayPlan || []).length ||
        (actionPlan.prioritySkillsToImprove || []).length ||
        (actionPlan.suggestedLearningFocus || []).length ||
        (actionPlan.careerStrategyAdjustment || []).length ||
        (actionPlan.riskReductionActions || []).length ||
        (actionPlan.progressTrackingSuggestions || []).length)
  );

  const riskBadgeClass = useMemo(
    () => badgeClassForRisk(prediction?.value),
    [prediction]
  );

  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const response = await axios.get(HISTORY_URL, { timeout: 15000 });
      setHistoryItems(response.data?.items || []);
    } catch {
      // History is optional if backend is down; keep existing list.
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleChange = (event) => {
    const { name, value, type } = event.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "range" ? Number(value) : value,
    }));
  };

  const handleReset = () => {
    setFormData(blankForm);
    setResult(null);
    setError("");
    setActiveHistoryId(null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const missing = visibleFields.filter(
      (key) => formData[key] === "" || formData[key] === null || formData[key] === undefined
    );

    if (missing.length) {
      setError("Please fill all input fields before generating the report.");
      setResult(null);
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    setActiveHistoryId(null);

    try {
      const response = await axios.post(API_URL, formData, {
        headers: { "Content-Type": "application/json" },
        timeout: 90000,
      });
      setResult(response.data);
      if (response.data?.historyId) {
        setActiveHistoryId(response.data.historyId);
      }
      await loadHistory();
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 80);
    } catch (err) {
      const message =
        err.response?.data?.error ||
        err.response?.data?.details ||
        (err.code === "ERR_NETWORK" || err.message?.includes("Network")
          ? "Cannot reach Flask backend at http://127.0.0.1:5000. Start python app.py in the backend folder."
          : "Unable to complete risk estimation. Please check backend and input values.");
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenHistory = async (id) => {
    setLoading(true);
    setError("");
    try {
      const response = await axios.get(`${HISTORY_URL}/${id}`, { timeout: 15000 });
      const item = response.data;
      setFormData({ ...blankForm, ...(item.profile || {}) });
      setResult(item.result || null);
      setActiveHistoryId(item.id);
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 80);
    } catch (err) {
      setError(
        err.response?.data?.error ||
          "Unable to open this saved assessment. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteHistory = async (event, id) => {
    event.stopPropagation();
    try {
      await axios.delete(`${HISTORY_URL}/${id}`, { timeout: 15000 });
      setHistoryItems((prev) => prev.filter((item) => item.id !== id));
      if (activeHistoryId === id) {
        setActiveHistoryId(null);
      }
    } catch (err) {
      setError(err.response?.data?.error || "Unable to delete this assessment.");
    }
  };

  return (
    <div className="app-shell">
      <section className="hero-band">
        <div className="hero">
          <p className="eyebrow">
            Comprehensive Career Development &amp; Recruitment Framework
          </p>
          <h1>Career Safety &amp; Industry Stability Analysis</h1>
          <p className="hero-subtitle">
            Explainable AI-supported career risk estimation for IT professionals
          </p>
          <div className="hero-badges">
            <span className="hero-pill">Decision-support only</span>
            <span className="hero-pill">Risk estimation, not job loss prediction</span>
            <span className="hero-pill">Human-readable guidance</span>
          </div>
          <p className="hero-copy">
            This tool analyzes career-related indicators and provides an overall
            risk level, input-based explanations, and personalized career guidance.
          </p>
        </div>
      </section>

      <main className="page">
        <form className="form-board" onSubmit={handleSubmit}>
          <SectionCard title="A · Career Background" icon={Briefcase} tone="blue">
            <div className="fields-stack">
              <SelectField
                label="Role"
                name="role"
                value={formData.role}
                onChange={handleChange}
                options={roleOptions}
                full
              />
              <div className="fields-row">
                <SelectField
                  label="Years of Experience"
                  name="years_experience"
                  value={formData.years_experience}
                  onChange={handleChange}
                  options={experienceOptions}
                />
                <SelectField
                  label="Career Strategy"
                  name="career_strategy"
                  value={formData.career_strategy}
                  onChange={handleChange}
                  options={strategyOptions}
                />
              </div>
            </div>
          </SectionCard>

          <SectionCard title="B · Learning & Adaptability" icon={GraduationCap} tone="blue">
            <div className="fields-stack">
              <div className="fields-row">
                <SelectField
                  label="Weekly Learning Time"
                  name="weekly_learning_time"
                  value={formData.weekly_learning_time}
                  onChange={handleChange}
                  options={learningOptions}
                />
                <SelectField
                  label="Skill Update Frequency"
                  name="skill_update_frequency"
                  value={formData.skill_update_frequency}
                  onChange={handleChange}
                  options={updateFrequencyOptions}
                />
              </div>
              <SliderField
                label="Tech Stack Change"
                name="tech_stack_change"
                value={formData.tech_stack_change}
                onChange={handleChange}
                helper="1 = No change, 5 = Complete overhaul"
              />
              <SliderField
                label="Switch Confidence"
                name="switch_confidence"
                value={formData.switch_confidence}
                onChange={handleChange}
                helper="1 = Not confident, 5 = Very confident"
              />
            </div>
          </SectionCard>

          <SectionCard
            title="Generate the report"
            icon={Sparkles}
            tone="purple"
            className="generate-card"
          >
            <p className="generate-copy">
              The report contains the model risk estimation, input-based indicators
              and AI-generated guidance.
            </p>
            <button type="submit" className="primary-btn" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="spin" size={18} />
                  Analyzing…
                </>
              ) : (
                <>
                  Generate Career Safety Report
                </>
              )}
            </button>
            <button type="button" className="ghost-btn reset-btn" onClick={handleReset}>
              <RefreshCcw size={14} />
              Reset
            </button>
          </SectionCard>
        </form>

        <SectionCard title="Past Assessments" icon={History} tone="blue" className="history-card">
          <p className="generate-copy">
            Each generated report is saved automatically. Open any entry to reload the
            full prediction, indicators, and guidance.
          </p>

          {historyLoading && historyItems.length === 0 ? (
            <div className="history-empty">
              <Loader2 className="spin" size={18} />
              <span>Loading history…</span>
            </div>
          ) : historyItems.length === 0 ? (
            <div className="history-empty">
              <Clock3 size={18} />
              <span>No saved assessments yet. Generate a report to start history.</span>
            </div>
          ) : (
            <ul className="history-list">
              {historyItems.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    className={`history-item ${activeHistoryId === item.id ? "is-active" : ""}`}
                    onClick={() => handleOpenHistory(item.id)}
                  >
                    <div className="history-item-main">
                      <strong>{item.role}</strong>
                      <span className="history-meta">{formatHistoryDate(item.createdAt)}</span>
                    </div>
                    <span className={badgeClassForRisk(item.riskLevel)}>{item.riskLevel}</span>
                  </button>
                  <button
                    type="button"
                    className="history-delete"
                    aria-label={`Delete assessment ${item.id}`}
                    onClick={(event) => handleDeleteHistory(event, item.id)}
                  >
                    <Trash2 size={14} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        {error && (
          <div className="alert-card">
            <AlertTriangle size={18} />
            <div>
              <strong>Request failed</strong>
              <p>{error}</p>
            </div>
          </div>
        )}

        {loading && (
          <section className="panel-card loading-card">
            <Loader2 className="spin large" size={28} />
            <h3>Analyzing career safety indicators…</h3>
            <p>Generating model prediction and AI-guided recommendations.</p>
          </section>
        )}

        {!loading && !result && (
          <section className="blank-report" aria-label="Blank report state">
            <div className="panel-card empty-hero">
              <div className="empty-icon-wrap">
                <Shield size={26} />
              </div>
              <div>
                <Badge tone="blue">Awaiting analysis</Badge>
                <h3>Career Safety Report is blank</h3>
                <p>
                  Fill the career profile and click Generate Career Safety Report.
                  After Reset, this blank dashboard returns until a new estimation is run.
                </p>
              </div>
            </div>

            <div className="blank-section accent-blue">
              <div className="blank-section-head">
                <Badge tone="blue">Section 1 · Model Prediction</Badge>
                <h4>Overall Career Risk Level</h4>
              </div>
              <div className="blank-skeleton risk-skeleton">
                <span className="blank-pill" />
                <span className="blank-line wide" />
                <span className="blank-line" />
              </div>
            </div>

            <div className="blank-section accent-cyan">
              <div className="blank-section-head">
                <Badge tone="cyan">Section 2 · System-Derived Indicators</Badge>
                <h4>Explanation Indicators</h4>
              </div>
              <div className="blank-indicator-grid">
                {indicatorMeta.map((item) => (
                  <div className="blank-indicator" key={item.key}>
                    <span className="blank-dot" />
                    <span className="blank-line short" />
                    <span className="blank-line" />
                  </div>
                ))}
              </div>
            </div>

            <div className="blank-section accent-purple">
              <div className="blank-section-head">
                <Badge tone="purple">Recommendations of career guidence</Badge>
                <h4>Personalized guidance</h4>
              </div>
              <div className="blank-skeleton">
                <span className="blank-block" />
                <div className="blank-two">
                  <span className="blank-block short" />
                  <span className="blank-block short" />
                </div>
                <span className="blank-line wide" />
                <span className="blank-line" />
              </div>
            </div>
          </section>
        )}

        {result && (
          <div className="results-wrap" ref={resultsRef}>
            <div className="panel-card results-banner">
              <div>
                <Badge tone="purple">Career Safety Report</Badge>
                <h2>Explainable risk estimation dashboard</h2>
                {activeHistoryId && (
                  <p className="history-view-note">
                    Viewing saved assessment #{activeHistoryId}
                  </p>
                )}
              </div>
              <button
                type="button"
                className="download-btn"
                onClick={() =>
                  downloadCareerReportPdf({
                    formData,
                    prediction,
                    indicators,
                    guidance,
                  })
                }
              >
                <Download size={16} />
                Download PDF
              </button>
            </div>

            {prediction && (
              <ReportSection
                tag="Section 1 · Model Prediction"
                title={prediction.predictedOutput}
                accent="blue"
              >
                <div className="prediction-card">
                  <div>
                    <p className="mini-label">Overall Career Risk Level</p>
                    <span className={riskBadgeClass}>{prediction.value}</span>
                  </div>
                </div>
              </ReportSection>
            )}

            {indicators && (
              <ReportSection
                tag="Section 2 · System-Derived Indicators"
                title="Explanation Indicators"
                accent="cyan"
              >
                <div className="indicator-grid">
                  {indicatorMeta.map((item) => (
                    <IndicatorCard
                      key={item.key}
                      title={item.title}
                      value={indicators[item.key]}
                      icon={item.icon}
                    />
                  ))}
                </div>
              </ReportSection>
            )}

            {guidance && (
              <ReportSection
                tag="Recommendations of career guidence"
                title="Recommendations of career guidence"
                accent="purple"
              >
                {guidance.generationStatus === "failed" && (
                  <div className="alert-card compact">
                    <AlertTriangle size={18} />
                    <div>
                      <strong>AI guidance unavailable</strong>
                      <p>{guidance.generationMessage}</p>
                    </div>
                  </div>
                )}

                {guidance.explainableRecommendation && (
                  <article className="highlight-card">
                    <div className="highlight-head">
                      <Sparkles size={18} />
                      <h3>Explainable Recommendation</h3>
                    </div>
                    <p>{guidance.explainableRecommendation}</p>
                  </article>
                )}

                <div className="two-col">
                  <article className="soft-card">
                    <div className="soft-card-head">
                      <AlertTriangle size={16} />
                      <h3>Main Risky Areas</h3>
                    </div>
                    <ul>
                      {(guidance.mainRiskyAreas || []).map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </article>
                  <article className="soft-card">
                    <div className="soft-card-head">
                      <Award size={16} />
                      <h3>Career Strengths</h3>
                    </div>
                    <ul>
                      {(guidance.careerStrengths || []).map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </article>
                </div>

                <div className="insight-grid">
                  <article className="insight-card">
                    <h4>Industry Stability Insight</h4>
                    <p>{guidance.industryStabilityInsight}</p>
                  </article>
                  <article className="insight-card">
                    <h4>Skill Transferability Insight</h4>
                    <p>{guidance.skillTransferabilityInsight}</p>
                  </article>
                  <article className="insight-card">
                    <h4>Adaptability Readiness Insight</h4>
                    <p>{guidance.adaptabilityReadinessInsight}</p>
                  </article>
                </div>

                <article className="soft-card">
                  <div className="soft-card-head">
                    <ListChecks size={16} />
                    <h3>Recommended Next Steps</h3>
                  </div>
                  <div className="action-grid">
                    {(guidance.recommendedNextSteps || []).map((item, index) => (
                      <div className="action-card" key={item}>
                        <span>{index + 1}</span>
                        <p>{item}</p>
                      </div>
                    ))}
                  </div>
                </article>

                <article className="soft-card">
                  <div className="soft-card-head">
                    <Info size={16} />
                    <h3>Why this result?</h3>
                  </div>
                  <ul className="timeline-list">
                    {(guidance.whyThisResult || []).map((item) => (
                      <li key={item}>
                        <CheckCircle2 size={15} />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </article>

                <article className="soft-card">
                  <div className="soft-card-head">
                    <Map size={16} />
                    <h3>Recommendation Mapping</h3>
                  </div>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Risk Factor</th>
                          <th>Condition</th>
                          <th>Lacking Area</th>
                          <th>Recommendation</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(guidance.recommendationMapping || []).map((row) => (
                          <tr key={`${row.riskFactor}-${row.condition}`}>
                            <td>{row.riskFactor}</td>
                            <td>{row.condition}</td>
                            <td>{row.lackingArea}</td>
                            <td>{row.recommendation}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </article>
              </ReportSection>
            )}

            {guidance && (
              <ReportSection
                tag="AI Career Resilience Action Plan"
                title="AI Career Resilience Action Plan"
                accent="teal"
              >
                <p className="section-note">
                  A personalized 30/60/90-day improvement plan generated from the ML
                  prediction, system-derived indicators, and user career profile.
                </p>

                {!hasActionPlanContent ? (
                  <div className="alert-card compact">
                    <AlertTriangle size={18} />
                    <div>
                      <strong>Unavailable</strong>
                      <p>Career resilience action plan is currently unavailable.</p>
                    </div>
                  </div>
                ) : (
                  <>
                    <article className="highlight-card resilience-summary">
                      <div className="highlight-head">
                        <CalendarRange size={18} />
                        <h3>Summary</h3>
                      </div>
                      <p>
                        {actionPlan.summary ||
                          "Career resilience action plan is currently unavailable."}
                      </p>
                      <div className="priority-row">
                        <span className="mini-label">Action Priority Level</span>
                        {actionPlan.actionPriorityLevel ? (
                          <Badge tone={priorityTone(actionPlan.actionPriorityLevel)}>
                            {actionPlan.actionPriorityLevel}
                          </Badge>
                        ) : (
                          <span className="muted-note">Not provided</span>
                        )}
                      </div>
                    </article>

                    <div className="timeline-plan-grid">
                      <TimelinePlanCard
                        label="Near-term"
                        days="30"
                        items={actionPlan.thirtyDayPlan}
                        tone="blue"
                      />
                      <TimelinePlanCard
                        label="Mid-term"
                        days="60"
                        items={actionPlan.sixtyDayPlan}
                        tone="cyan"
                      />
                      <TimelinePlanCard
                        label="Longer-term"
                        days="90"
                        items={actionPlan.ninetyDayPlan}
                        tone="purple"
                      />
                    </div>

                    <div className="checklist-grid">
                      <ChecklistBlock
                        title="Priority Skills to Improve"
                        items={actionPlan.prioritySkillsToImprove}
                        icon={Target}
                      />
                      <ChecklistBlock
                        title="Suggested Learning Focus"
                        items={actionPlan.suggestedLearningFocus}
                        icon={GraduationCap}
                      />
                      <ChecklistBlock
                        title="Career Strategy Adjustment"
                        items={actionPlan.careerStrategyAdjustment}
                        icon={Map}
                      />
                      <ChecklistBlock
                        title="Risk Reduction Actions"
                        items={actionPlan.riskReductionActions}
                        icon={Shield}
                      />
                      <ChecklistBlock
                        title="Progress Tracking Suggestions"
                        items={actionPlan.progressTrackingSuggestions}
                        icon={Flag}
                      />
                    </div>
                  </>
                )}
              </ReportSection>
            )}

            {decisionNote && (
              <section className="panel-card notice-card">
                <Info size={18} />
                <div>
                  <Badge tone="blue">Decision Support Notice</Badge>
                  <p>{decisionNote}</p>
                </div>
              </section>
            )}

          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>R26-IT-034 | Career Safety and Industry Stability Analysis</p>
      </footer>
    </div>
  );
}

export default App;
