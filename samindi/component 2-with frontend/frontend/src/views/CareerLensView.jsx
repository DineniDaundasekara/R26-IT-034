import { useMemo, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  BadgeCheck,
  BriefcaseBusiness,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  ExternalLink,
  FileCheck2,
  FileText,
  FileUp,
  Github,
  GraduationCap,
  Lightbulb,
  Linkedin,
  Link as LinkIcon,
  LoaderCircle,
  MapPin,
  Search,
  Sparkles,
  Target,
  TrendingUp,
  UserRoundSearch,
  Wrench,
} from "lucide-react";
import { analyzeCv } from "../api.js";

const ROLE_OPTIONS = [
  {
    value: "Software Engineer",
    description: "Develop software applications, data structures and engineering systems",
  },
  {
    value: "Frontend Developer",
    description: "Build interactive user interfaces, web applications and responsive designs",
  },
  {
    value: "Backend Developer",
    description: "Develop REST APIs, databases, microservices and server-side systems",
  },
  {
    value: "Full Stack Developer",
    description: "Work across frontend, backend, databases and full lifecycle development",
  },
  {
    value: "QA Engineer",
    description: "Automated testing, test case authoring and software quality assurance",
  },
  {
    value: "DevOps Engineer",
    description: "CI/CD pipelines, containerization, cloud infrastructure and automation",
  },
  {
    value: "Data Analyst",
    description: "Data analysis, SQL querying, dashboards and business intelligence",
  },
  {
    value: "Business Analyst",
    description: "Requirements gathering, stakeholder communication and process mapping",
  },
  {
    value: "UI/UX Designer",
    description: "User experience research, wireframing, usability testing and UI design",
  },
];

const READINESS_TEXT = {
  Weak: "Your CV needs important additions and structural improvements before it is competitive.",
  Average: "Your CV provides a solid foundation with several priority areas to strengthen.",
  Good: "Your CV presents strong evidence and aligns well with current industry requirements.",
  Excellent: "Your CV is well structured and shows strong evidence alignment with relevant vacancies.",
};

function Chips({ items = [], tone = "default", empty = "No items detected." }) {
  const safe = Array.isArray(items) ? items.filter(Boolean) : [];
  if (!safe.length) return <p className="empty-text">{empty}</p>;

  return (
    <div className="chip-row">
      {safe.map((item, index) => (
        <span className={`chip ${tone}`} key={`${item}-${index}`}>
          {item}
        </span>
      ))}
    </div>
  );
}

function GuidanceList({ title, icon: Icon, items = [] }) {
  const safe = Array.isArray(items) ? items.filter(Boolean) : [];
  return (
    <article className="guidance-card">
      <div className="guidance-heading">
        <span className="guidance-icon"><Icon size={18} /></span>
        <h3>{title}</h3>
      </div>
      {safe.length ? (
        <ul>
          {safe.map((item, index) => <li key={index}>{item}</li>)}
        </ul>
      ) : (
        <p className="empty-text">No guidance available for this section.</p>
      )}
    </article>
  );
}

function ProfessionalLinks({ links = {} }) {
  const github = Array.isArray(links.github) && links.github.length > 0 ? links.github[0] : null;
  const linkedin = Array.isArray(links.linkedin) && links.linkedin.length > 0 ? links.linkedin[0] : null;
  const portfolio = Array.isArray(links.portfolio_or_other) && links.portfolio_or_other.length > 0 ? links.portfolio_or_other[0] : null;

  const items = [
    github && { url: github, label: "GitHub Profile", Icon: Github },
    linkedin && { url: linkedin, label: "LinkedIn Profile", Icon: Linkedin },
    portfolio && { url: portfolio, label: "Portfolio / Website", Icon: LinkIcon },
  ].filter(Boolean);

  if (!items.length) {
    return <p className="empty-text">No professional links detected in CV.</p>;
  }

  return (
    <div className="profile-links">
      {items.map(({ url, label, Icon }, index) => (
        <a href={url} target="_blank" rel="noopener noreferrer" key={index}>
          <Icon size={16} />
          <span>{label}</span>
          <ExternalLink size={13} />
        </a>
      ))}
    </div>
  );
}

function JobCard({ job }) {
  const applyOptions = Array.isArray(job?.apply_options) ? job.apply_options : [];
  const primaryUrl =
    job?.primary_apply_url ||
    job?.share_link ||
    job?.url ||
    job?.link ||
    applyOptions?.[0]?.url ||
    "";
  const isTopJobs = job?.source_type === "topjobs";
  const isLinkedIn = job?.source_type === "linkedin_jobs";

  return (
    <article className="job-card">
      <div className="job-card-top">
        <div>
          <div className="job-source-row">
            <span
              className={`source-badge ${
                isTopJobs ? "topjobs" : isLinkedIn ? "linkedin" : "google"
              }`}
            >
              {job?.source_name || (isTopJobs ? "TopJobs" : isLinkedIn ? "LinkedIn" : "Google Jobs")}
            </span>
            {job?.posted_at && <span className="job-meta-chip">{job.posted_at}</span>}
            {job?.schedule_type && <span className="job-meta-chip">{job.schedule_type}</span>}
          </div>
          <h3>{job?.title || "Job opportunity"}</h3>
          <p className="job-company">
            {[job?.company, job?.location].filter(Boolean).join(" • ") || "Employer details unavailable"}
          </p>
        </div>
        <span className={`fit-badge ${String(job?.fit || "").toLowerCase().replaceAll(" ", "-")}`}>
          {job?.fit || "Evaluated"}
        </span>
      </div>

      <div className="job-skill-grid">
        <div>
          <div className="mini-heading success"><CheckCircle2 size={16} /> Matched skills</div>
          <Chips items={job?.matched_skills || []} tone="success" empty="No matched catalog skills detected." />
        </div>
        <div>
          <div className="mini-heading warning"><CircleAlert size={16} /> Skills to strengthen</div>
          <Chips items={job?.missing_skills || []} tone="warning" empty="No missing catalog skills detected." />
        </div>
      </div>

      {job?.description && (
        <details className="job-details">
          <summary>View vacancy description & requirements</summary>
          <p>{job.description.slice(0, 800)}</p>
        </details>
      )}

      <div className="job-actions">
        {primaryUrl && (
          <a className="job-primary-link" href={primaryUrl} target="_blank" rel="noopener noreferrer">
            {isTopJobs ? "View on TopJobs" : isLinkedIn ? "View on LinkedIn" : "View / Apply"} <ExternalLink size={15} />
          </a>
        )}

        {applyOptions.slice(1, 3).map((option, index) => (
          <a className="job-secondary-link" href={option.url} target="_blank" rel="noreferrer" key={`${option.url}-${index}`}>
            {option.source || "Apply option"} <ChevronRight size={14} />
          </a>
        ))}
      </div>
    </article>
  );
}

function JobRecommendations({ result }) {
  const [tab, setTab] = useState("all");
  const all = Array.isArray(result?.jobs) ? result.jobs : [];
  const google = all.filter((job) => job?.source_type === "google_jobs");
  const topjobs = all.filter((job) => job?.source_type === "topjobs");
  const linkedin = all.filter((job) => job?.source_type === "linkedin_jobs");

  const visible =
    tab === "google"
      ? google
      : tab === "topjobs"
      ? topjobs
      : tab === "linkedin"
      ? linkedin
      : all;

  return (
    <section className="result-section" id="jobs">
      <div className="section-title-row">
        <div>
          <span className="section-kicker">Job opportunities</span>
          <h2>Recommended vacancies</h2>
          <p>Current public vacancies related to your selected role, ranked with explainable skill evidence.</p>
        </div>
        <div className="job-total">
          <BriefcaseBusiness size={19} />
          <strong>{all.length}</strong>
          <span>found</span>
        </div>
      </div>

      <div className="job-tabs">
        <button className={tab === "all" ? "active" : ""} onClick={() => setTab("all")}>
          Recommended All <span>{all.length}</span>
        </button>
        <button className={tab === "google" ? "active" : ""} onClick={() => setTab("google")}>
          Google Jobs <span>{google.length}</span>
        </button>
        <button className={tab === "topjobs" ? "active" : ""} onClick={() => setTab("topjobs")}>
          TopJobs <span>{topjobs.length}</span>
        </button>
        <button className={tab === "linkedin" ? "active" : ""} onClick={() => setTab("linkedin")}>
          LinkedIn Jobs <span>{linkedin.length}</span>
        </button>
      </div>

      {visible.length ? (
        <div className="jobs-list">
          {visible.map((job, index) => (
            <JobCard
              job={job}
              key={job?.job_id || `${job?.title}-${job?.source_type}-${index}`}
            />
          ))}
        </div>
      ) : (
        <div className="job-empty-state">
          <BriefcaseBusiness size={32} />
          <h3>No {tab} vacancies found.</h3>
          <p>Try another role or broader location query.</p>
        </div>
      )}
    </section>
  );
}

function getReadinessClass(level = "") {
  const l = String(level).toLowerCase();
  if (l.includes("transition")) return "level-transition";
  if (l.includes("excellent")) return "level-excellent";
  if (l.includes("good")) return "level-good";
  if (l.includes("weak")) return "level-weak";
  return "level-average";
}

function AnalysisResults({ result }) {
  if (!result) return null;

  const readiness = result?.cv_readiness || {};
  const docQuality = readiness?.document_quality || {};
  const roleAlignment = readiness?.role_alignment || {};
  const evidence = result?.cv_evidence || {};
  const guidance = result?.guidance || {};
  const sections = evidence?.sections || {};
  const sectionItems = Object.entries(sections).map(([name, present]) => ({ name, present }));

  const readinessLevel = readiness?.level || "Average";
  const readinessClass = getReadinessClass(readinessLevel);

  return (
    <div className="results-shell" id="results">
      <section className="overview-card">
        <div className="overview-main">
          <span className="section-kicker">Your Career Analysis</span>
          <h2>{result?.career_path_prediction?.label || "Career path prediction"}</h2>
          <p>Your recommended career direction, based on the real experience and skills in your CV.</p>

          <div className="overview-meta">
            <span><Target size={15} /> Applying for: <strong>{result?.target_role}</strong></span>
            <span><MapPin size={15} /> {result?.location}</span>
          </div>

          {roleAlignment?.is_career_transition && (
            <div className="career-transition-banner">
              <Sparkles size={16} />
              <div>
                <strong>Career Transition Detected</strong>
                <span>
                  Your primary experience aligns with <strong>{roleAlignment?.predicted_domain || result?.career_path_prediction?.label}</strong>, 
                  and you are targeting <strong>{roleAlignment?.target_domain || result?.target_role}</strong>. 
                  Readiness reflects domain transition requirements.
                </span>
              </div>
            </div>
          )}
        </div>

        <div className={`readiness-card ${readinessClass}`}>
          <span>CV readiness</span>
          <strong>{readinessLevel}</strong>
          <p>{readiness?.description || READINESS_TEXT[readinessLevel] || "Qualitative CV readiness assessment."}</p>
        </div>
      </section>

      {/* 2D Decoupled Matrix */}
      <section className="result-section">
        <div className="section-title-row compact">
          <div>
            <span className="section-kicker">Two-Part CV Assessment</span>
            <h2>A Clearer Picture of Your CV</h2>
            <p>We look at how your CV is written and how well it fits your target role separately, so a strong CV is never unfairly penalised just because you're aiming for something new.</p>
          </div>
        </div>

        <div className="decoupled-matrix-grid">
          <div className="matrix-card">
            <div className="matrix-card-header">
              <span className="matrix-icon doc"><FileCheck2 size={20} /></span>
              <div>
                <small>CV Structure</small>
                <h3>Document Structural Quality</h3>
              </div>
              <span className={`matrix-badge ${docQuality?.level === "Complete" ? "badge-success" : docQuality?.level === "Moderate" ? "badge-warning" : "badge-danger"}`}>
                {docQuality?.level || "Complete"}
              </span>
            </div>
            <p className="matrix-desc">
              {docQuality?.description || "Assessment of core CV sections and structural completeness."}
            </p>
            <div className="matrix-stats">
              <span>Core Sections: <strong>{(docQuality?.present_core_sections || []).length}/5</strong></span>
              <span>Links: <strong>{docQuality?.has_professional_links ? "Detected" : "None"}</strong></span>
            </div>
          </div>

          <div className="matrix-card">
            <div className="matrix-card-header">
              <span className="matrix-icon role"><Target size={20} /></span>
              <div>
                <small>Role Fit</small>
                <h3>Target Role Alignment</h3>
              </div>
              <span className={`matrix-badge ${roleAlignment?.status?.includes("High") ? "badge-success" : roleAlignment?.is_career_transition ? "badge-transition" : "badge-warning"}`}>
                {roleAlignment?.status || "Evaluated"}
              </span>
            </div>
            <p className="matrix-desc">
              {roleAlignment?.description || "Evidence alignment with current vacancy market requirements."}
            </p>
            <div className="matrix-stats">
              <span>Target: <strong>{result?.target_role}</strong></span>
              <span>Domain Match: <strong>{roleAlignment?.is_career_transition ? "Cross-Domain" : "Direct Match"}</strong></span>
            </div>
          </div>
        </div>
      </section>

      {/* CV Evidence */}
      <section className="result-section">
        <div className="section-title-row compact">
          <div>
            <span className="section-kicker">CV evidence</span>
            <h2>What your CV currently shows</h2>
          </div>
        </div>

        <div className="evidence-layout">
          <article className="evidence-card wide">
            <h3>Detected technical & soft skills</h3>
            <Chips items={evidence?.skills || []} tone="primary" />
          </article>

          <article className="evidence-card">
            <h3>Professional CV sections</h3>
            <div className="section-checklist">
              {sectionItems.map(({ name, present }) => (
                <div className={present ? "present" : "missing"} key={name}>
                  {present ? <Check size={15} /> : <CircleAlert size={15} />}
                  <span>{name.replaceAll("_", " ")}</span>
                </div>
              ))}
            </div>
          </article>

          <article className="evidence-card">
            <h3>Professional links</h3>
            <ProfessionalLinks links={evidence?.links || {}} />
          </article>
        </div>

        {(readiness?.reasons || []).length > 0 && (
          <div className="why-level">
            <strong>Why this assessment level?</strong>
            <ul>
              {readiness.reasons.map((reason, index) => <li key={index}>{reason}</li>)}
            </ul>
          </div>
        )}
      </section>

      {/* Grounded Guidance */}
      <section className="result-section" id="guidance">
        <div className="section-title-row">
          <div>
            <span className="section-kicker">Career guidance</span>
            <h2>How to strengthen your CV and career direction</h2>
            <p>Practical recommendations based on your CV evidence and current vacancy market demands.</p>
          </div>
        </div>

        <div className="guidance-grid">
          <GuidanceList title="Current strengths" icon={BadgeCheck} items={guidance?.strengths} />
          <GuidanceList title="Priority improvements" icon={Wrench} items={guidance?.priority_improvements} />
          <GuidanceList title="Professional CV maintenance" icon={FileText} items={guidance?.cv_maintenance} />
          <GuidanceList title="Career directions" icon={TrendingUp} items={guidance?.career_paths} />
          <GuidanceList title="Interview preparation" icon={UserRoundSearch} items={guidance?.interview_preparation} />
          <GuidanceList title="Next actions" icon={Lightbulb} items={guidance?.next_actions} />
        </div>
      </section>

      <JobRecommendations result={result} />
    </div>
  );
}

export default function CareerLensView({ onBackToDashboard }) {
  const [file, setFile] = useState(null);
  const [jobRole, setJobRole] = useState("Software Engineer");
  const [location, setLocation] = useState("Sri Lanka");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const fileLabel = useMemo(() => {
    if (!file) return "PDF, DOCX or TXT";
    return `${file.name} • ${(file.size / 1024).toFixed(1)} KB`;
  }, [file]);

  function scrollToAnalyzer() {
    document.getElementById("analyze")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setResult(null);

    if (!file) {
      setError("Please upload your CV first.");
      return;
    }
    if (!jobRole.trim()) {
      setError("Please select the job role you want to apply for.");
      return;
    }

    setLoading(true);
    try {
      const payload = await analyzeCv({
        file,
        jobRole: jobRole.trim(),
        location: location.trim() || "Sri Lanka",
      });
      setResult(payload);
      window.setTimeout(() => {
        document.getElementById("results")?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 100);
    } catch (err) {
      setError(err.message || "CV analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="module-view-wrapper">
      {/* Top Breadcrumb Nav */}
      <div className="view-subbar">
        <button className="back-dashboard-btn" onClick={onBackToDashboard}>
          <ArrowLeft size={16} /> Back to Home
        </button>
        <span className="view-tag">
          <FileText size={14} /> CV Based Career Path Guidance (CareerLens)
        </span>
      </div>

      <div className="site-shell">
        <main id="top">
          <section className="hero-section">
            <div className="hero-copy">
              <span className="hero-eyebrow"><Sparkles size={15} /> Smarter CV & Career Decisions</span>
              <h1>Build a stronger CV.<br />Find roles that fit your evidence.</h1>
              <p className="hero-description">
                Upload your CV and get an instant career-path match, an honest read on your CV's
                structure, real-time openings from Google Jobs, TopJobs & LinkedIn, and a clear list
                of the skills worth building next.
              </p>
              <div className="hero-actions">
                <button className="hero-primary" onClick={scrollToAnalyzer}>
                  Analyze your CV <ArrowRight size={17} />
                </button>
                <a className="hero-secondary" href="#analyze">Explore role matching</a>
              </div>
            </div>

            <div className="hero-visual" aria-label="CareerLens benefits">
              <div className="benefit-card main-benefit">
                <span className="benefit-icon"><Target size={20} /></span>
                <div><small>Career direction</small><strong>Matched to your real experience</strong></div>
              </div>
              <div className="benefit-grid">
                <div className="benefit-card"><FileCheck2 size={19} /><strong>CV quality</strong><span>Clear, structured feedback</span></div>
                <div className="benefit-card"><TrendingUp size={19} /><strong>Skill gaps</strong><span>See exactly what's missing</span></div>
                <div className="benefit-card"><BriefcaseBusiness size={19} /><strong>Live vacancies</strong><span>Google Jobs, TopJobs, LinkedIn</span></div>
                <div className="benefit-card"><Lightbulb size={19} /><strong>Actionable guidance</strong><span>Targeted upskilling recommendations</span></div>
              </div>
            </div>
          </section>

          <section className="analyzer-section" id="analyze">
            <div className="analyzer-heading">
              <span className="section-kicker">CV analysis</span>
              <h2>Upload your CV and select your target role</h2>
              <p>We will extract your CV evidence, predict career direction, assess structural readiness, and match current live vacancies.</p>
            </div>

            <form className="analyzer-card" onSubmit={handleSubmit}>
              <label className={`upload-box ${file ? "has-file" : ""}`}>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={(event) => setFile(event.target.files?.[0] || null)}
                />
                <span className="upload-icon">
                  {file ? <FileCheck2 size={28} /> : <FileUp size={28} />}
                </span>
                <strong>{file ? "CV file selected" : "Upload your CV"}</strong>
                <span>{fileLabel}</span>
              </label>

              <div className="form-fields">
                <label>
                  <span><Target size={16} /> Job role you want to apply for</span>
                  <select value={jobRole} onChange={(event) => setJobRole(event.target.value)}>
                    {ROLE_OPTIONS.map((role) => (
                      <option value={role.value} key={role.value}>
                        {role.value}
                      </option>
                    ))}
                  </select>
                  <small className="role-description">
                    {ROLE_OPTIONS.find((role) => role.value === jobRole)?.description}
                  </small>
                </label>

                <label>
                  <span><MapPin size={16} /> Location</span>
                  <input
                    value={location}
                    onChange={(event) => setLocation(event.target.value)}
                    placeholder="Sri Lanka"
                  />
                </label>
              </div>

              {error && <div className="form-error"><CircleAlert size={17} /> {error}</div>}

              <button className="analyze-button" type="submit" disabled={loading}>
                {loading ? (
                  <><LoaderCircle className="spin" size={18} /> Analyzing your CV & Matching Jobs...</>
                ) : (
                  <><Search size={18} /> Analyze CV & Find Jobs</>
                )}
              </button>
            </form>
          </section>

          <section className="what-you-get">
            <div>
              <span><Target size={20} /></span>
              <h3>Career Direction</h3>
              <p>An AI-matched career path based on your real experience.</p>
            </div>
            <div>
              <span><FileText size={20} /></span>
              <h3>Two-Part CV Quality</h3>
              <p>How well your CV is written, and how well it fits your target role.</p>
            </div>
            <div>
              <span><BriefcaseBusiness size={20} /></span>
              <h3>Real-Time Opportunities</h3>
              <p>Direct vacancy links from Google Jobs, TopJobs, and LinkedIn.</p>
            </div>
          </section>

          <AnalysisResults result={result} />
        </main>
      </div>
    </div>
  );
}
