import React, { useMemo, useState } from "react";
import axios from "axios";
import "./Prediction.css";

const SCALE_OPTIONS = [1, 2, 3, 4, 5];
const NAV_ITEMS = ["Dashboard", "Prediction", "Results & History", "Model Information", "About"];

const QUESTION_BANK = {
  sie: {
    title: "Internship Experience (SIE1-SIE14)",
    groups: [
      {
        title: "Clear Internship Objectives",
        items: [
          { code: "SIE1", text: "I gained practical skills during my internship." },
          { code: "SIE2", text: "I was given meaningful tasks to perform." },
          { code: "SIE3", text: "I received helpful feedback from my supervisor." },
          { code: "SIE4", text: "I have a clear idea of what work to do during my internship." },
        ],
      },
      {
        title: "School Support",
        items: [
          { code: "SIE5", text: "The school helped me in preparing to find an internship." },
          { code: "SIE6", text: "School supervisors supported my internship assignments and projects." },
          { code: "SIE7", text: "School supervisors helped identify and understand internship problems." },
        ],
      },
      {
        title: "Comfortable Environment",
        items: [
          { code: "SIE8", text: "I was treated with respect and professionalism at my internship site." },
          { code: "SIE9", text: "My internship supervisor was available to answer questions and guide me." },
          { code: "SIE10", text: "My supervisor shared valuable experiences relevant to my work issues." },
          { code: "SIE11", text: "My supervisor gave clear and detailed performance feedback." },
        ],
      },
      {
        title: "Job Prospects",
        items: [
          { code: "SIE12", text: "My internship work outcomes support career opportunities and benefits." },
          { code: "SIE13", text: "I had opportunities to join challenging and valuable projects." },
          { code: "SIE14", text: "This internship let me observe and learn best practices from experts." },
        ],
      },
    ],
  },
  comp: {
    title: "Competence (C1-C10)",
    groups: [
      {
        title: "Life and Career Competencies",
        items: [
          { code: "C1", text: "I can adapt quickly to changing situations in learning or group activities." },
          { code: "C2", text: "I can interact clearly and effectively with people from different backgrounds." },
          { code: "C3", text: "I can organize and execute projects efficiently and effectively." },
          { code: "C4", text: "I can lead and inspire group members with a clear vision and values." },
        ],
      },
      {
        title: "Learning and Innovation Competencies",
        items: [
          { code: "C5", text: "I can identify and resolve problems in varied situations." },
          { code: "C6", text: "I communicate clearly and collaborate well with other group members." },
          { code: "C7", text: "I can think creatively and create new innovations." },
        ],
      },
      {
        title: "Information Technology and Media Competencies",
        items: [
          { code: "C8", text: "I can access information effectively and evaluate its quality for decisions." },
          { code: "C9", text: "I can select and develop media to support communication." },
          { code: "C10", text: "I can analyze information media and create suitable communication media." },
        ],
      },
    ],
  },
  psy: {
    title: "Psychological Capital (PsyCap1-PsyCap14)",
    groups: [
      {
        title: "Hope",
        items: [
          { code: "PsyCap1", text: "I can find various ways to overcome obstacles in my studies." },
          { code: "PsyCap2", text: "I can use realistic and effective approaches to solve faced problems." },
          { code: "PsyCap3", text: "I stay committed to doing my best and working hard toward my goals." },
          { code: "PsyCap4", text: "I can make plans and pathways to reach my target outcomes." },
        ],
      },
      {
        title: "Optimism",
        items: [
          { code: "PsyCap5", text: "I feel optimistic that my investment of time and effort yields results." },
          { code: "PsyCap6", text: "I tend to see positive lessons from every learning experience." },
          { code: "PsyCap7", text: "I can recover from difficulties and continue pursuing my goals." },
        ],
      },
      {
        title: "Resilience",
        items: [
          { code: "PsyCap8", text: "I can identify and analyze causes of setbacks in learning." },
          { code: "PsyCap9", text: "I try to find solutions when I receive low grades." },
          { code: "PsyCap10", text: "I understand that everyone has ups and downs on the way to success." },
          { code: "PsyCap11", text: "I have strong intrinsic motivation to keep improving myself." },
        ],
      },
      {
        title: "Self-Efficacy",
        items: [
          { code: "PsyCap12", text: "I believe that I can complete difficult tasks successfully." },
          { code: "PsyCap13", text: "I have enough self-confidence to ask for help when needed." },
          { code: "PsyCap14", text: "I feel confident I can make meaningful contributions with my abilities." },
        ],
      },
    ],
  },
};

const sections = Object.entries(QUESTION_BANK).map(([key, value]) => ({
  key,
  title: value.title,
  items: value.groups.flatMap((group) => group.items),
  groups: value.groups,
}));

const getLevelClass = (level) => {
  const normalized = (level || "").toLowerCase();
  if (normalized === "high") return "level-high";
  if (normalized === "medium") return "level-medium";
  return "level-low";
};

const getDimensionStrength = (avg) => {
  if (avg >= 4.2) return "Strong";
  if (avg >= 3.3) return "Good";
  return "Developing";
};

const Prediction = () => {
  const [sieValues, setSieValues] = useState(Array(sections.find((section) => section.key === "sie").items.length).fill(4));
  const [compValues, setCompValues] = useState(Array(sections.find((section) => section.key === "comp").items.length).fill(4));
  const [psyValues, setPsyValues] = useState(Array(sections.find((section) => section.key === "psy").items.length).fill(4));
  const [openSection, setOpenSection] = useState("sie");
  const [showAll, setShowAll] = useState({ sie: false, comp: false, psy: false });

  const [score, setScore] = useState(null);
  const [level, setLevel] = useState("");
  const [loading, setLoading] = useState(false);

  const average = (arr) => {
    const nums = arr.map(Number);
    return nums.reduce((acc, item) => acc + item, 0) / nums.length;
  };

  const SIE_avg = useMemo(() => average(sieValues), [sieValues]);
  const Comp_avg = useMemo(() => average(compValues), [compValues]);
  const PsyCap_avg = useMemo(() => average(psyValues), [psyValues]);
  const qualityLabel = score === null ? "--" : (Number(score) >= 4 ? "High" : Number(score) >= 3 ? "Medium" : "Low");

  const handleChange = (type, index, value) => {
    const parsed = Number(value);

    if (type === "sie") {
      const updated = [...sieValues];
      updated[index] = parsed;
      setSieValues(updated);
    } else if (type === "comp") {
      const updated = [...compValues];
      updated[index] = parsed;
      setCompValues(updated);
    } else if (type === "psy") {
      const updated = [...psyValues];
      updated[index] = parsed;
      setPsyValues(updated);
    }
  };

  const getValuesByType = (type) => {
    if (type === "sie") return sieValues;
    if (type === "comp") return compValues;
    return psyValues;
  };

  const handlePredict = async () => {
    try {
      setLoading(true);

      const response = await axios.post("http://localhost:5000/api/predict", {
        SIE_avg,
        PsyCap_avg,
        Comp_avg,
      });

      const predictedScore = response?.data?.score ?? response?.data?.predicted_score ?? null;
      const predictedLevel = response?.data?.level ?? response?.data?.predicted_level ?? "";

      setScore(predictedScore);
      setLevel(predictedLevel);
    } catch (error) {
      console.error(error);
      alert("Prediction failed. Check backend and ML API.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSieValues(Array(sections.find((section) => section.key === "sie").items.length).fill(4));
    setCompValues(Array(sections.find((section) => section.key === "comp").items.length).fill(4));
    setPsyValues(Array(sections.find((section) => section.key === "psy").items.length).fill(4));
    setScore(null);
    setLevel("");
  };

  return (
    <div className="prediction-dashboard">
      <aside className="prediction-sidebar">
        <div className="brand-wrap">
          <div className="brand-icon">EP</div>
          <div>
            <h2>Employability Prediction System</h2>
          </div>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item}
              type="button"
              className={`nav-item ${item === "Prediction" ? "active" : ""}`}
            >
              {item}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer-card">
          <p className="sidebar-footer-title">Admin User</p>
          <p className="sidebar-footer-sub">admin@eps.edu</p>
        </div>
      </aside>

      <main className="prediction-main">
        <header className="page-header">
          <h1>Employability Prediction System</h1>
          <p>Predict and assess employability based on key factors</p>
        </header>

        <section className="top-stats">
          <article className="stat-card highlight">
            <p>Latest Prediction</p>
            <h3>{score !== null ? Number(score).toFixed(2) : "--"}</h3>
            <span>{qualityLabel}</span>
          </article>
          <article className="stat-card">
            <p>Internship Average</p>
            <h3>{SIE_avg.toFixed(2)}</h3>
            <span>{getDimensionStrength(SIE_avg)}</span>
          </article>
          <article className="stat-card">
            <p>Competence Average</p>
            <h3>{Comp_avg.toFixed(2)}</h3>
            <span>{getDimensionStrength(Comp_avg)}</span>
          </article>
          <article className="stat-card">
            <p>PsyCap Average</p>
            <h3>{PsyCap_avg.toFixed(2)}</h3>
            <span>{getDimensionStrength(PsyCap_avg)}</span>
          </article>
        </section>

        <div className="prediction-layout">
          <section className="input-panel">
            <div className="panel-head">
              <h3>Input Factors</h3>
              <div className="scale-help">
                <span>1 = Strongly Disagree</span>
                <span>5 = Strongly Agree</span>
              </div>
            </div>

            {sections.map((section) => (
              <SectionCard
                key={section.key}
                section={section}
                values={getValuesByType(section.key)}
                isOpen={openSection === section.key}
                onToggle={() => setOpenSection(openSection === section.key ? "" : section.key)}
                onChange={handleChange}
                showAll={showAll[section.key]}
                onToggleShowAll={() =>
                  setShowAll((prev) => ({
                    ...prev,
                    [section.key]: !prev[section.key],
                  }))
                }
              />
            ))}

            <div className="form-actions">
              <button type="button" className="predict-btn secondary" onClick={handleReset} disabled={loading}>
                Reset
              </button>
              <button type="button" className="predict-btn" onClick={handlePredict} disabled={loading}>
                {loading ? "Predicting..." : "Predict Employability"}
              </button>
            </div>
          </section>

          <aside className="result-card">
            <h3>Prediction Result</h3>
            <p className="result-label">Predicted Employability Score</p>

            <p className="score-value">{score !== null ? Number(score).toFixed(2) : "--"}</p>

            <div className="level-wrap">
              <span className={`level-badge ${getLevelClass(level)}`}>
                {level || "No Prediction"}
              </span>
            </div>

            <div className="summary-box">
              <h4>Dimension Summary</h4>
              <div className="summary-row">
                <span>Internship Experience</span>
                <strong>{getDimensionStrength(SIE_avg)}</strong>
              </div>
              <div className="summary-row">
                <span>Competence</span>
                <strong>{getDimensionStrength(Comp_avg)}</strong>
              </div>
              <div className="summary-row">
                <span>Psychological Capital</span>
                <strong>{getDimensionStrength(PsyCap_avg)}</strong>
              </div>
            </div>

            <div className="result-note">
              This prediction is based on your selected responses and is intended for guidance.
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
};

const SectionCard = ({ section, values, isOpen, onToggle, onChange, showAll, onToggleShowAll }) => {
  const visibleCount = section.key === "comp" ? 3 : 4;
  let cursor = 0;

  return (
    <div className="section-card">
      <button type="button" className="section-title-btn" onClick={onToggle}>
        <span>{section.title}</span>
        <span className="section-metric">Avg: {(values.reduce((acc, item) => acc + item, 0) / values.length).toFixed(2)}</span>
        <span className={`chevron ${isOpen ? "open" : ""}`}>⌄</span>
      </button>

      {isOpen && (
        <div className="section-content">
          {section.groups.map((group) => {
            const itemOffset = cursor;
            cursor += group.items.length;
            const displayedItems = showAll ? group.items : group.items.slice(0, visibleCount);

            return (
              <div className="question-group" key={`${section.key}-${group.title}`}>
                <h4>{group.title}</h4>
                {displayedItems.map((item, index) => {
                  const itemIndex = itemOffset + index;

                  return (
                    <div className="question-row" key={item.code}>
                      <div className="question-text-wrap">
                        <label htmlFor={`${section.key}-${itemIndex}`}>{item.code}</label>
                        <p>{item.text}</p>
                      </div>
                      <select
                        id={`${section.key}-${itemIndex}`}
                        value={values[itemIndex]}
                        onChange={(event) => onChange(section.key, itemIndex, event.target.value)}
                      >
                        {SCALE_OPTIONS.map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                    </div>
                  );
                })}
              </div>
            );
          })}

          <button type="button" className="show-toggle-btn" onClick={onToggleShowAll}>
            {showAll ? "Show less items" : `Show all ${section.items.length} items`}
          </button>
        </div>
      )}
    </div>
  );
};

export default Prediction;