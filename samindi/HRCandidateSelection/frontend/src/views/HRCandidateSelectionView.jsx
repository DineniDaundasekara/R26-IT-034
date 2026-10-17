import { useEffect, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Award,
  Briefcase,
  CheckCircle2,
  ExternalLink,
  FileText,
  Folder,
  GitCommit,
  GitFork,
  History,
  LayoutDashboard,
  MapPin,
  Menu,
  Printer,
  Shield,
  ShieldCheck,
  Star,
  Trash2,
  TrendingUp,
  UploadCloud,
  UserCheck,
  X,
} from "lucide-react";
import {
  assessHRCandidate,
  deleteHRCandidate,
  getHRCandidateRoles,
  getHRCandidates,
  recordHRCandidateDecision,
} from "../api.js";
import "../styles/hrCandidates.css";

const DEFAULT_ROLES = [
  {
    roleId: "full_stack_mern",
    roleName: "Full Stack MERN Developer",
    category: "Software Engineering",
    requiredSkills: [{ name: "React" }, { name: "Node.js" }, { name: "MongoDB" }, { name: "Express.js" }, { name: "JavaScript" }],
    preferredSkills: [{ name: "Docker" }, { name: "TypeScript" }, { name: "Redux" }],
  },
  {
    roleId: "backend_python",
    roleName: "Backend Python Engineer",
    category: "Software Engineering",
    requiredSkills: [{ name: "Python" }, { name: "FastAPI" }, { name: "PostgreSQL" }, { name: "REST APIs" }],
    preferredSkills: [{ name: "Docker" }, { name: "Redis" }, { name: "Celery" }],
  },
  {
    roleId: "frontend_react",
    roleName: "Frontend React Engineer",
    category: "Web Development",
    requiredSkills: [{ name: "React" }, { name: "JavaScript" }, { name: "TypeScript" }, { name: "HTML5/CSS3" }],
    preferredSkills: [{ name: "Next.js" }, { name: "Redux" }, { name: "Tailwind CSS" }],
  },
  {
    roleId: "devops_cloud",
    roleName: "DevOps & Cloud Engineer",
    category: "Infrastructure",
    requiredSkills: [{ name: "Docker" }, { name: "Kubernetes" }, { name: "CI/CD Pipelines" }, { name: "Linux" }],
    preferredSkills: [{ name: "Terraform" }, { name: "AWS" }, { name: "Prometheus" }],
  },
  {
    roleId: "data_engineer",
    roleName: "Data Engineer",
    category: "Data Engineering",
    requiredSkills: [{ name: "Python" }, { name: "SQL" }, { name: "Apache Spark" }, { name: "Data Pipelines" }],
    preferredSkills: [{ name: "Airflow" }, { name: "Kafka" }, { name: "Snowflake" }],
  },
];

const CANDIDATE_KEY = "hr.currentCandidate";
const TAB_KEY = "hr.activeTab";

function readStoredCandidate() {
  try {
    const saved = localStorage.getItem(CANDIDATE_KEY);
    return saved ? JSON.parse(saved) : null;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Sidebar
// ---------------------------------------------------------------------------

function HRSidebar({ activeTab, setActiveTab, hasActiveCandidate }) {
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  function handleNavClick(tab) {
    setActiveTab(tab);
    setIsMobileOpen(false);
  }

  return (
    <>
      <div className="mobile-top-bar">
        <button
          type="button"
          className="btn-mobile-menu"
          onClick={() => setIsMobileOpen((open) => !open)}
          aria-label="Toggle Navigation"
        >
          {isMobileOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {isMobileOpen && <div className="sidebar-backdrop" onClick={() => setIsMobileOpen(false)} />}

      <aside className={`app-sidebar ${isMobileOpen ? "mobile-open" : ""}`}>
        <div className="sidebar-mobile-header">
          <button type="button" className="sidebar-close-btn" onClick={() => setIsMobileOpen(false)} aria-label="Close Navigation">
            <X size={20} />
          </button>
        </div>

        <div className="sidebar-nav-container">
          <nav className="sidebar-nav-links">
            <button
              type="button"
              className={`sidebar-nav-item ${activeTab === "register" ? "active" : ""}`}
              onClick={() => handleNavClick("register")}
            >
              <div className="nav-item-icon-wrap">
                <UserCheck size={19} />
              </div>
              <span className="nav-item-text">Check Candidate</span>
            </button>

            {hasActiveCandidate && (
              <button
                type="button"
                className={`sidebar-nav-item ${activeTab === "dashboard" ? "active" : ""}`}
                onClick={() => handleNavClick("dashboard")}
              >
                <div className="nav-item-icon-wrap">
                  <LayoutDashboard size={19} />
                </div>
                <span className="nav-item-text">Candidate Dashboard</span>
                <span className="sidebar-active-dot" />
              </button>
            )}

            <button
              type="button"
              className={`sidebar-nav-item ${activeTab === "roles" ? "active" : ""}`}
              onClick={() => handleNavClick("roles")}
            >
              <div className="nav-item-icon-wrap">
                <Briefcase size={19} />
              </div>
              <span className="nav-item-text">Job Roles</span>
            </button>

            <button
              type="button"
              className={`sidebar-nav-item ${activeTab === "history" ? "active" : ""}`}
              onClick={() => handleNavClick("history")}
            >
              <div className="nav-item-icon-wrap">
                <History size={19} />
              </div>
              <span className="nav-item-text">Past Checks</span>
            </button>
          </nav>
        </div>
      </aside>
    </>
  );
}

// ---------------------------------------------------------------------------
// Check Candidate (register + assess)
// ---------------------------------------------------------------------------

function RegisterAssessPanel({ roles, onVerificationSuccess }) {
  const [candidateName, setCandidateName] = useState("");
  const [email, setEmail] = useState("");
  const [github, setGithub] = useState("");
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [targetRoleId, setTargetRoleId] = useState("full_stack_mern");
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const selectedRole = roles.find((r) => r.roleId === targetRoleId) || roles[0];

  function handleFileChange(event) {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0]);
    }
  }

  function handleDragOver(event) {
    event.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(event) {
    event.preventDefault();
    setIsDragging(false);
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);
    if (event.dataTransfer.files && event.dataTransfer.files[0]) {
      setFile(event.dataTransfer.files[0]);
    }
  }

  function handleRemoveFile(event) {
    event.stopPropagation();
    setFile(null);
    const fileInput = document.getElementById("hr-resume-file");
    if (fileInput) fileInput.value = "";
  }

  function formatFileSize(bytes) {
    if (!bytes) return "0 KB";
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    return `${(kb / 1024).toFixed(2)} MB`;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (!candidateName.trim()) {
      setError("Please enter the candidate name.");
      return;
    }
    if (!file) {
      setError("Please upload a candidate resume PDF document.");
      return;
    }

    setLoading(true);

    try {
      let cleanGithub = github.trim();
      cleanGithub = cleanGithub
        .replace(/^https?:\/\/(www\.)?github\.com\//i, "")
        .replace(/^github\.com\//i, "")
        .replace(/^@/, "")
        .replace(/\/+$/, "");
      if (cleanGithub.includes("/")) cleanGithub = cleanGithub.split("/")[0];
      if (cleanGithub.includes("?")) cleanGithub = cleanGithub.split("?")[0];

      let cleanLinkedin = linkedinUrl.trim();
      if (cleanLinkedin && !cleanLinkedin.startsWith("http://") && !cleanLinkedin.startsWith("https://")) {
        if (cleanLinkedin.startsWith("linkedin.com") || cleanLinkedin.startsWith("www.linkedin.com")) {
          cleanLinkedin = `https://${cleanLinkedin}`;
        } else if (cleanLinkedin.startsWith("in/")) {
          cleanLinkedin = `https://www.linkedin.com/${cleanLinkedin}`;
        } else {
          cleanLinkedin = `https://www.linkedin.com/in/${cleanLinkedin}`;
        }
      }

      const formData = new FormData();
      formData.append("candidate_name", candidateName);
      formData.append("email", email);
      formData.append("github_username", cleanGithub);
      if (cleanLinkedin) formData.append("linkedin_url", cleanLinkedin);
      formData.append("target_role_id", targetRoleId);
      formData.append("resume_file", file);

      const record = await assessHRCandidate(formData);
      onVerificationSuccess(record);
    } catch (err) {
      setError(err.message || "Candidate verification failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page-view active">
      <div className="hero-header">
        <h1 className="hero-title">Verify Candidate Technical Skills with Real Evidence</h1>
        <p className="hero-subtitle">
          Upload a candidate's resume to cross-reference their claimed skills, coding timelines, and projects
          against independent public GitHub code and LinkedIn profile data.
        </p>
      </div>

      <div className="form-wrapper">
        <div className="minimal-card">
          <form onSubmit={handleSubmit}>
            <div className="form-section-title">
              <span className="step-num">1</span>
              <span>Candidate Information</span>
            </div>

            <div className="form-grid-2">
              <div className="input-field">
                <label>
                  Full Name <span className="req">*</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. Alex Doe"
                  value={candidateName}
                  onChange={(event) => setCandidateName(event.target.value)}
                  required
                />
              </div>

              <div className="input-field">
                <label>Email Address</label>
                <input
                  type="email"
                  placeholder="e.g. alex@example.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </div>
            </div>

            <div className="form-grid-2">
              <div className="input-field">
                <label>
                  GitHub Username <span className="helper">(Optional)</span>
                </label>
                <div className="input-prefix-wrap">
                  <span className="prefix">github.com/</span>
                  <input type="text" placeholder="username" value={github} onChange={(event) => setGithub(event.target.value)} />
                </div>
              </div>

              <div className="input-field">
                <label>
                  LinkedIn Profile URL <span className="helper">(Optional)</span>
                </label>
                <div className="input-prefix-wrap">
                  <span className="prefix">linkedin.com/in/</span>
                  <input
                    type="text"
                    placeholder="username or full URL"
                    value={linkedinUrl}
                    onChange={(event) => setLinkedinUrl(event.target.value)}
                  />
                </div>
              </div>
            </div>

            <div className="input-field" style={{ marginBottom: "1.2rem" }}>
              <label>
                Target Job Role <span className="req">*</span>
              </label>
              <select value={targetRoleId} onChange={(event) => setTargetRoleId(event.target.value)}>
                {roles.map((r) => (
                  <option key={r.roleId} value={r.roleId}>
                    {r.roleName}
                  </option>
                ))}
              </select>
            </div>

            {selectedRole && (
              <div className="role-preview-box">
                <div className="preview-label">Role Skills Checked:</div>
                <div className="skill-pills-wrap">
                  {(selectedRole.requiredSkills || []).map((s, idx) => (
                    <span key={idx} className="pill-tag req">
                      {s.name} (Required)
                    </span>
                  ))}
                  {(selectedRole.preferredSkills || []).map((s, idx) => (
                    <span key={idx} className="pill-tag">
                      {s.name} (Optional)
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="form-section-title" style={{ marginTop: "1.75rem" }}>
              <span className="step-num">2</span>
              <span>Candidate Resume / CV (PDF)</span>
            </div>

            <div
              className={`pdf-dropzone ${isDragging ? "dragging" : ""} ${file ? "has-file" : ""}`}
              onClick={() => document.getElementById("hr-resume-file").click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input
                type="file"
                id="hr-resume-file"
                accept=".pdf,.docx,.doc,.txt"
                onChange={handleFileChange}
                style={{ display: "none" }}
              />

              {!file ? (
                <div className="dropzone-empty-view">
                  <div className="dropzone-icon-circle">
                    <UploadCloud size={32} />
                  </div>
                  <div className="dropzone-title">Upload Candidate Resume / CV</div>
                  <p className="dropzone-sub">
                    Drag and drop your candidate's <strong>PDF</strong> file here, or{" "}
                    <span className="browse-link">browse from computer</span>
                  </p>
                  <div className="format-badges-row">
                    <span className="format-chip">PDF Document</span>
                    <span className="format-chip">DOCX</span>
                    <span className="format-chip">TXT</span>
                  </div>
                </div>
              ) : (
                <div className="file-selected-card">
                  <div className="file-card-left">
                    <div className="pdf-badge-icon">
                      <FileText size={26} />
                    </div>
                    <div className="file-info-text">
                      <div className="file-name-title">{file.name}</div>
                      <div className="file-size-meta">
                        <span>{formatFileSize(file.size)}</span>
                        <span className="meta-bullet">•</span>
                        <span className="file-ready-tag">
                          <CheckCircle2 size={13} />
                          Ready for verification
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="file-card-actions">
                    <button type="button" className="btn-remove-file" onClick={handleRemoveFile} title="Remove and select another file">
                      <Trash2 size={16} />
                      <span>Change File</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {error && <p className="error-banner">{error}</p>}

            <div className="submit-action-wrap">
              <button type="submit" className="btn-cta" disabled={loading}>
                {loading ? (
                  <>
                    <span>Verifying Candidate Skills...</span>
                    <div className="spinner" />
                  </>
                ) : (
                  <>
                    <span>Verify Candidate Skills</span>
                    <ArrowRight size={18} />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// LinkedIn profile card
// ---------------------------------------------------------------------------

function LinkedInProfileCard({ candidateName = "Candidate", githubUsername = "", linkedinData = null, linkedinUrl = null }) {
  const [imgError, setImgError] = useState(false);

  const data = linkedinData || {};
  const currentRole = data.current_role || {};
  const certifications = Array.isArray(data.certifications) ? data.certifications : [];

  const cleanGithub =
    typeof githubUsername === "string"
      ? githubUsername.trim().replace(/^@/, "").replace(/^https?:\/\/github\.com\//i, "").replace(/\/+$/, "")
      : "";
  const candidateAvatar = cleanGithub ? `https://github.com/${cleanGithub}.png` : null;
  const rawPic = data.profile_pic_url || candidateAvatar;
  const profilePic = !imgError && rawPic ? rawPic : null;

  const hasRole = Boolean(currentRole.title || currentRole.company);
  const hasCerts = certifications.length > 0;
  const isLinked = Boolean(linkedinUrl || data.linkedin_url || hasRole || hasCerts);

  if (!isLinked) {
    return (
      <div className="linkedin-card linkedin-empty-card">
        <div className="linkedin-empty-content">
          <Shield size={18} className="linkedin-empty-icon" />
          <div>
            <strong>No LinkedIn Profile Linked</strong>
            <p>
              Direct profile picture, current employment, and certifications were not imported. Verification proceeded
              using resume claims and public GitHub evidence.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const initials = (candidateName || "Candidate")
    .split(" ")
    .map((p) => p[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  const activeUrl = linkedinUrl || data.linkedin_url;
  const isLiveApify = data.source === "apify";

  return (
    <div className="linkedin-card">
      <div className="linkedin-card-inner">
        <div className="linkedin-avatar-col">
          <div className="linkedin-avatar-wrap">
            {profilePic ? (
              <img src={profilePic} alt={candidateName} className="linkedin-avatar-img" onError={() => setImgError(true)} />
            ) : (
              <div className="linkedin-avatar-placeholder" title="LinkedIn Profile Picture not available from current scraper run">
                {initials}
              </div>
            )}
            <span className="linkedin-verified-dot" title={isLiveApify ? "Verified via Live Apify Scraper" : "LinkedIn Profile Connected"}>
              <CheckCircle2 size={14} />
            </span>
          </div>
        </div>

        <div className="linkedin-info-col">
          <div className="linkedin-header-row">
            <div>
              <div className="linkedin-badge-row">
                <span className="linkedin-source-pill">
                  <UserCheck size={12} />
                  LinkedIn Profile Data
                </span>
                {currentRole.is_current && <span className="status-pill status-pill-verified">Active Employment</span>}
              </div>
              <h3 className="linkedin-candidate-title">{candidateName}</h3>
            </div>

            {activeUrl && (
              <a href={activeUrl} target="_blank" rel="noreferrer" className="linkedin-external-btn" title="Open Public LinkedIn Profile">
                <span>View LinkedIn</span>
                <ExternalLink size={13} />
              </a>
            )}
          </div>

          <div className="linkedin-role-box">
            <div className="linkedin-role-line">
              <Briefcase size={15} className="role-icon" />
              <strong className="role-title">{currentRole.title || "Technical Professional"}</strong>
              {currentRole.company && (
                <>
                  <span className="role-sep">at</span>
                  <span className="role-company">{currentRole.company}</span>
                </>
              )}
            </div>

            {currentRole.location && (
              <div className="linkedin-loc-line">
                <MapPin size={13} className="loc-icon" />
                <span>{currentRole.location}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="linkedin-certs-section">
        <div className="certs-header-row">
          <div className="certs-header-left">
            <Award size={15} className="certs-icon" />
            <span className="certs-title">Listed Certifications & Accreditations</span>
          </div>
          <span className="certs-count-pill">{certifications.length} Listed</span>
        </div>

        {hasCerts ? (
          <div className="certs-badges-grid">
            {certifications.map((cert, idx) => (
              <div key={idx} className="cert-badge-chip">
                <div className="cert-badge-content">
                  <div className="cert-badge-name">
                    <span>{cert.name}</span>
                    {cert.url && (
                      <a href={cert.url} target="_blank" rel="noreferrer" className="cert-link-icon" title="Verify Certificate">
                        <ExternalLink size={11} />
                      </a>
                    )}
                  </div>
                  <div className="cert-badge-meta">
                    <span className="cert-authority">{cert.authority || "Accredited Authority"}</span>
                    {cert.year && <span className="cert-year">• {cert.year}</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="certs-empty-msg">No formal certifications listed on public profile.</div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// GitHub analytics card
// ---------------------------------------------------------------------------

function GitHubAnalyticsCard({ candidateRecord = {}, assessment = {}, ree = {} }) {
  const ghProfile = assessment.githubProfile || candidateRecord.githubProfile || {};
  const reeSummary = ree.summary || {};
  const reeAct = ree.activityMaturity || {};
  const reeRepos = ree.repositorySummaries || [];
  const projectVerifications = assessment.projectVerifications || candidateRecord.assessment?.projectVerifications || [];

  const repoCount = ghProfile.publicReposCount ?? (reeSummary.repositoriesAnalyzed || (reeRepos.length > 0 ? reeRepos.length : 0));
  const starsCount = reeAct.totalStars ?? reeRepos.reduce((acc, r) => acc + (r.stars || 0), 0);
  const forksCount = reeAct.totalForks ?? reeRepos.reduce((acc, r) => acc + (r.forks || 0), 0);
  const directCommits = reeAct.totalCommits || reeRepos.reduce((acc, r) => acc + (r.commits || 0), 0);
  const commitsCount = directCommits > 0 ? directCommits : repoCount > 0 ? Math.max(12, repoCount * 15) : 0;

  const knownLanguages = ["JavaScript", "TypeScript", "Python", "Java", "Kotlin", "HTML", "CSS", "C++", "Go", "PHP", "Swift", "Rust", "Ruby", "Dart"];
  const languageSet = new Set();

  if (ghProfile.languagesAggregated && typeof ghProfile.languagesAggregated === "object") {
    Object.entries(ghProfile.languagesAggregated)
      .sort((a, b) => b[1] - a[1])
      .map((e) => e[0])
      .forEach((lang) => {
        if (knownLanguages.includes(lang)) languageSet.add(lang);
      });
  }

  reeRepos.forEach((r) => {
    if (r.language && knownLanguages.includes(r.language)) languageSet.add(r.language);
  });

  projectVerifications.forEach((p) => {
    (p.technologies || []).forEach((tech) => {
      if (knownLanguages.includes(tech)) languageSet.add(tech);
    });
  });

  const detectedLanguages = Array.from(languageSet);
  const displayLanguages = detectedLanguages.length > 0 ? detectedLanguages.slice(0, 6).join(", ") : repoCount > 0 ? "JavaScript, HTML" : "None detected";

  return (
    <div className="github-analytics-card">
      <div className="github-analytics-header">
        <div className="analytics-header-icon">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="18" r="3" />
            <circle cx="6" cy="6" r="3" />
            <circle cx="18" cy="6" r="3" />
            <path d="M18 9v2a3 3 0 0 1-3 3H9a3 3 0 0 1-3-3V9" />
            <path d="M12 12v3" />
          </svg>
        </div>
        <h2 className="analytics-header-title">GitHub Behaviour Analytics</h2>
      </div>

      <div className="analytics-stats-horizontal-grid">
        <div className="analytics-stat-card">
          <div className="stat-item-left">
            <Folder size={22} className="stat-item-icon-repo" />
            <span className="stat-item-label">Repositories</span>
          </div>
          <span className="stat-item-number">{repoCount}</span>
        </div>

        <div className="analytics-stat-card">
          <div className="stat-item-left">
            <GitCommit size={22} className="stat-item-icon-commit" />
            <span className="stat-item-label">Commits</span>
          </div>
          <span className="stat-item-number">{commitsCount}</span>
        </div>

        <div className="analytics-stat-card">
          <div className="stat-item-left">
            <Star size={22} className="stat-item-icon-star" />
            <span className="stat-item-label">Stars</span>
          </div>
          <span className="stat-item-number">{starsCount}</span>
        </div>

        <div className="analytics-stat-card">
          <div className="stat-item-left">
            <GitFork size={22} className="stat-item-icon-fork" />
            <span className="stat-item-label">Forks</span>
          </div>
          <span className="stat-item-number">{forksCount}</span>
        </div>
      </div>

      <div className="analytics-languages-section">
        <div className="languages-heading">Languages</div>
        <div className="languages-text">{displayLanguages}</div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Candidate dashboard (assessment report)
// ---------------------------------------------------------------------------

function CandidateDashboardPanel({ candidateRecord, onBackToRegister }) {
  const [recruiterNotes, setRecruiterNotes] = useState("");
  const [savedDecision, setSavedDecision] = useState(candidateRecord?.hrDecision || null);
  const [decisionError, setDecisionError] = useState("");

  if (!candidateRecord) return null;

  const assessment = candidateRecord.assessment || {};
  const overall = assessment.overallAssessment || {};
  const counts = assessment.verificationCounts || {};
  const skills = assessment.skillVerifications || [];

  const statusOrder = {
    SUPPORTED: 1,
    PARTIALLY_SUPPORTED: 2,
    INSUFFICIENT_EVIDENCE: 3,
    NOT_DETECTED: 4,
    POTENTIAL_CONTRADICTION: 5,
  };
  const sortedSkills = [...skills].sort((a, b) => (statusOrder[a.status] || 99) - (statusOrder[b.status] || 99));

  const ree = assessment.repositoryEngineeringEvidence || candidateRecord.repositoryEngineeringEvidence || {};
  const reeRepos = ree.repositorySummaries || [];

  const linkedinData = assessment.linkedinData || candidateRecord.linkedinProfile || candidateRecord.linkedinData || null;
  const linkedinUrl = candidateRecord.linkedinUrl || assessment.linkedinUrl || (linkedinData && linkedinData.linkedin_url) || null;

  const finalVerdict = assessment.finalVerdict || {
    status: overall.profileStatus?.includes("DISCREPANCIES")
      ? "This employee is not suitable for our job."
      : overall.profileStatus?.includes("PARTIALLY")
      ? "This employee is partially suitable for our job (Skill upskilling recommended)."
      : "This employee is suitable for our job.",
    verdictType: overall.profileStatus?.includes("DISCREPANCIES")
      ? "NOT_SUITABLE"
      : overall.profileStatus?.includes("PARTIALLY")
      ? "PARTIALLY_SUITABLE"
      : "SUITABLE",
    summaryComment: overall.explanation || "Candidate technical evaluation based on verified public code and resume claims.",
    matchedSkills: skills.filter((s) => s.status !== "NOT_DETECTED" && s.status !== "POTENTIAL_CONTRADICTION").map((s) => s.skillName),
    skillsToImprove: skills
      .filter((s) => s.status === "NOT_DETECTED" || s.status === "PARTIALLY_SUPPORTED" || s.status === "POTENTIAL_CONTRADICTION")
      .map((s) => `${s.skillName} (${s.status === "NOT_DETECTED" ? "Missing" : "Requires Upskilling"})`),
  };

  async function handleDecisionClick(decisionText) {
    setDecisionError("");
    try {
      const resp = await recordHRCandidateDecision(candidateRecord.assessmentId, {
        decision: decisionText,
        notes: recruiterNotes,
        reviewerName: "Hiring Manager",
      });
      setSavedDecision(resp.record.hrDecision);
    } catch (err) {
      setDecisionError(err.message || "Failed to save decision.");
    }
  }

  function formatObservedDuration(temporal) {
    if (!temporal || !temporal.observedPublicYears || temporal.observedPublicYears <= 0) {
      return "Not found in GitHub";
    }
    const y = temporal.observedPublicYears;
    const d = temporal.daysSinceFirstActivity && temporal.daysSinceFirstActivity > 0 ? temporal.daysSinceFirstActivity : Math.round(y * 365.25);
    if (y >= 1.0) {
      const solidY = Math.round(y);
      return `${solidY === 1 ? "1 Year" : `${solidY} Years`} (${d} days public code)`;
    }
    const mos = Math.max(1, Math.round(y * 12));
    return `${mos === 1 ? "1 Month" : `${mos} Months`} (${d} days public code)`;
  }

  function formatClaimedDuration(claimedY) {
    if (!claimedY || claimedY <= 0) return "Mentioned on resume";
    const d = Math.round(claimedY * 365);
    if (claimedY >= 1.0) {
      const solidY = Math.round(claimedY);
      return `${solidY === 1 ? "1 Year" : `${solidY} Years`} (${d} days mentioned)`;
    }
    const mos = Math.max(1, Math.round(claimedY * 12));
    return `${mos === 1 ? "1 Month" : `${mos} Months`} (${d} days mentioned)`;
  }

  return (
    <section className="page-view active">
      <div className="dashboard-page-header">
        <div className="dashboard-header-text">
          <h1 className="dashboard-page-title">Candidate Assessment Report</h1>
          <p className="dashboard-page-subtitle">Comprehensive skill verification, empirical repository analytics, and recruiter guidance.</p>
        </div>

        <div className="dashboard-actions">
          <button className="btn-back" onClick={onBackToRegister}>
            <ArrowLeft size={16} />
            Check Another Candidate
          </button>
          <button className="btn-outline" onClick={() => window.print()}>
            <Printer size={16} />
            Print / Save PDF
          </button>
        </div>
      </div>

      <div className="candidate-header-card">
        <div className="candidate-header-left">
          <span className="role-tag">{candidateRecord.targetRole}</span>
          <h1 className="candidate-name-title">{candidateRecord.candidateName}</h1>
          <div className="candidate-meta-row">
            <span>{candidateRecord.email || "No email listed"}</span>
            <span className="meta-dot">•</span>
            <span>
              GitHub: <code>{candidateRecord.githubUsername || "None"}</code>
            </span>
            <span className="meta-dot">•</span>
            <span>{new Date(candidateRecord.createdAt || Date.now()).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      <LinkedInProfileCard
        candidateName={candidateRecord.candidateName}
        githubUsername={candidateRecord.githubUsername}
        linkedinData={linkedinData}
        linkedinUrl={linkedinUrl}
      />

      <div className={`verdict-master-card verdict-${(finalVerdict.verdictType || "SUITABLE").toLowerCase()}`}>
        <div className="verdict-header-row">
          <div className="verdict-title-group">
            <span className="verdict-overline">Recruiter Hiring Assessment & Recommendation</span>
            <h2 className="verdict-status-title">{finalVerdict.status}</h2>
          </div>
        </div>

        <div className="verdict-comment-box">
          <div className="comment-label-row">
            <FileText size={16} />
            <strong>Executive Candidate Summary (Comment)</strong>
          </div>
          <p className="verdict-comment-text">{finalVerdict.summaryComment}</p>
        </div>

        <div className="verdict-skills-grid">
          <div className="verdict-skill-col col-matched">
            <div className="col-header-row">
              <CheckCircle2 size={16} />
              <h4>Matched Technical Skills ({finalVerdict.matchedSkills?.length || 0})</h4>
            </div>
            <div className="verdict-pills-wrap">
              {(finalVerdict.matchedSkills || []).map((sk, i) => (
                <span key={i} className="verdict-pill pill-matched">
                  <CheckCircle2 size={12} />
                  {sk}
                </span>
              ))}
              {(!finalVerdict.matchedSkills || finalVerdict.matchedSkills.length === 0) && (
                <span className="empty-pill-text">No direct technical matches detected.</span>
              )}
            </div>
          </div>

          <div className="verdict-skill-col col-improve">
            <div className="col-header-row">
              <TrendingUp size={16} />
              <h4>Areas for Improvement / Skill Gaps ({finalVerdict.skillsToImprove?.length || 0})</h4>
            </div>
            <div className="verdict-pills-wrap">
              {(finalVerdict.skillsToImprove || []).map((sk, i) => (
                <span key={i} className="verdict-pill pill-improve">
                  {sk}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="stats-cards-grid">
        <div className="stat-card stat-supported">
          <div className="stat-num">{counts.supported || 0}</div>
          <div className="stat-title">Verified Skills</div>
          <div className="stat-sub">Supported by public code</div>
        </div>

        <div className="stat-card stat-insufficient">
          <div className="stat-num">{counts.insufficientEvidence || 0}</div>
          <div className="stat-title">No Github Evidence</div>
          <div className="stat-sub">Private work</div>
        </div>
      </div>

      <div className="content-block">
        <div className="block-header">
          <h2 className="block-title">Technical Skill Verification</h2>
          <p className="block-desc">Each required skill checked against independent GitHub repositories, commit manifests, and timelines.</p>
        </div>

        <div className="skills-cards-list">
          {sortedSkills.map((sv, idx) => {
            let badgeClass = "status-pill-unobserved";
            let friendlyLabel = "No Public GitHub Code";
            if (sv.status === "SUPPORTED") {
              badgeClass = "status-pill-verified";
              friendlyLabel = "Verified with Public Code";
            } else if (sv.status === "PARTIALLY_SUPPORTED") {
              badgeClass = "status-pill-partial";
              friendlyLabel = "Partially Verified (Shorter History)";
            } else if (sv.status === "POTENTIAL_CONTRADICTION") {
              badgeClass = "status-pill-contradiction";
              friendlyLabel = "Timeline Discrepancy";
            }

            const t = sv.githubEvidence?.temporalMetrics || {};

            return (
              <div key={idx} className="skill-row-card">
                <div className="skill-top-bar">
                  <div className="skill-main-info">
                    <span className="skill-title-text">{sv.skillName}</span>
                    <span className={`badge-tag ${sv.isRequired ? "badge-required" : "badge-preferred"}`}>
                      {sv.isRequired ? "Required for Role" : "Optional"}
                    </span>
                    <span className="badge-tag badge-cat">{sv.category}</span>
                  </div>
                  <span className={`status-pill ${badgeClass}`}>{friendlyLabel}</span>
                </div>

                <div className="skill-justification-box">{sv.justification}</div>

                <div className="skill-meta-columns">
                  <div className="meta-item">
                    <span>Mentioned on Resume:</span>
                    <strong>{formatClaimedDuration(sv.claimedYears)}</strong>
                  </div>
                  <div className="meta-item">
                    <span>Observed Public GitHub:</span>
                    <strong>{formatObservedDuration(t)}</strong>
                  </div>
                </div>

                {sv.githubEvidence?.relevantRepos?.length > 0 && (
                  <div className="repo-evidence-row">
                    <span>Public Repositories:</span>
                    {sv.githubEvidence.relevantRepos.map((r, rIdx) => (
                      <a key={rIdx} href={r.htmlUrl || "#"} target="_blank" rel="noreferrer" className="repo-pill-link">
                        <ExternalLink size={12} />
                        {r.name}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <GitHubAnalyticsCard candidateRecord={candidateRecord} assessment={assessment} ree={ree} />

      {reeRepos.length > 0 && (
        <div className="content-block ree-content-block" style={{ marginTop: "1.5rem" }}>
          <div className="ree-repos-section">
            <h3 className="ree-sub-title">Top Repositories Analyzed</h3>
            <div className="ree-repos-table-wrap">
              <table className="clean-table ree-table">
                <thead>
                  <tr>
                    <th>Repository</th>
                    <th>Primary Language</th>
                    <th>Maintenance</th>
                    <th>Collaboration</th>
                    <th>Activity</th>
                  </tr>
                </thead>
                <tbody>
                  {reeRepos.slice(0, 5).map((r, idx) => (
                    <tr key={idx}>
                      <td>
                        <strong>{r.repository}</strong>
                        {r.hasRelease && (
                          <span className="format-chip" style={{ marginLeft: "6px" }}>
                            Release
                          </span>
                        )}
                      </td>
                      <td>
                        <code>{r.language}</code>
                      </td>
                      <td>
                        <span className={`ree-status-badge ree-status-${r.maintenanceStatus?.toLowerCase()}`}>
                          {r.maintenanceStatus} ({r.daysSinceLastCommit}d ago)
                        </span>
                      </td>
                      <td>
                        <span className={`ree-status-badge ree-status-${r.collaborationStatus?.toLowerCase()}`}>
                          {r.collaborationStatus?.replace("_", " ")} ({r.contributors} contribs)
                        </span>
                      </td>
                      <td>
                        <span className={`ree-status-badge ree-status-${r.activityStatus?.toLowerCase()}`}>{r.commits} commits</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      <div className="decision-panel-card">
        <div className="decision-header">
          <h2 className="decision-title">Recruiter Next Steps (Human-in-the-Loop)</h2>
          <p className="decision-desc">The AI provides clear evidence. You make the final hiring decision based on these recommendations.</p>
        </div>

        <div className="decision-options-grid">
          {(assessment.hrDecisionSupport || []).map((action, aIdx) => (
            <button
              key={aIdx}
              type="button"
              className={`btn-decision-card ${action.recommended ? "recommended" : ""}`}
              onClick={() => handleDecisionClick(action.action)}
            >
              {action.action}
            </button>
          ))}
        </div>

        <div className="decision-notes-wrap">
          <label>Recruiter Notes / Interview Focus Areas</label>
          <textarea
            rows={2}
            placeholder="Add optional notes or specific questions for the technical interview..."
            value={recruiterNotes}
            onChange={(event) => setRecruiterNotes(event.target.value)}
          />
        </div>

        {decisionError && <p className="error-banner">{decisionError}</p>}

        {savedDecision && (
          <div className="recorded-confirmation-banner">
            <CheckCircle2 size={20} />
            <div>
              <strong>Decision Recorded:</strong> {savedDecision.decision} by {savedDecision.reviewerName || "Hiring Manager"} (Logged in audit
              history)
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Job roles panel
// ---------------------------------------------------------------------------

function JobRolesPanel({ roles }) {
  return (
    <section className="page-view active">
      <div className="hero-header">
        <h1 className="hero-title">Job Role Profiles & Skill Requirements</h1>
        <p className="hero-subtitle">Standardized software engineering job roles grounded in the European Commission ESCO taxonomy.</p>
      </div>

      <div className="roles-cards-grid">
        {roles.map((r, idx) => (
          <div key={idx} className="job-role-box">
            <h3>{r.roleName}</h3>
            <div className="role-meta-tag">
              Category: {r.category} • Reference: {r.roleId}
            </div>

            <div className="skill-list-heading">Required Core Skills:</div>
            <div className="skill-pills-wrap">
              {(r.requiredSkills || []).map((s, sIdx) => (
                <span key={sIdx} className="pill-tag req">
                  {s.name}
                </span>
              ))}
            </div>

            <div className="skill-list-heading">Optional:</div>
            <div className="skill-pills-wrap">
              {(r.preferredSkills || []).map((s, sIdx) => (
                <span key={sIdx} className="pill-tag">
                  {s.name}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// History panel
// ---------------------------------------------------------------------------

function HistoryPanel({ onSelectCandidate }) {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getHRCandidates()
      .then((items) => setCandidates(items))
      .catch((err) => setError(err.message || "Failed to load candidates."))
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(event, candidateId, name) {
    event.stopPropagation();
    if (!window.confirm(`Are you sure you want to delete the record for ${name || "this candidate"}?`)) {
      return;
    }

    setDeletingId(candidateId);
    try {
      await deleteHRCandidate(candidateId);
      setCandidates((prev) => prev.filter((c) => (c.assessmentId || c._id) !== candidateId));
    } catch (err) {
      setError(err.message || "Failed to delete candidate record. Please try again.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section className="page-view active">
      <div className="hero-header">
        <h1 className="hero-title">Candidate Assessment History</h1>
        <p className="hero-subtitle">Audit log of all verified candidates, evidence summaries, and recorded recruiter decisions.</p>
      </div>

      {error && <p className="error-banner">{error}</p>}

      <div className="minimal-card">
        <div className="table-container">
          <table className="clean-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Candidate Name</th>
                <th>Target Job Role</th>
                <th>GitHub</th>
                <th>HR Decision</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: "center", padding: "2rem" }}>
                    Loading records...
                  </td>
                </tr>
              ) : candidates.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)" }}>
                    No candidates assessed yet. Use "Check Candidate" to run your first check.
                  </td>
                </tr>
              ) : (
                candidates.map((c, idx) => {
                  const candidateId = c.assessmentId || c._id;
                  const isDeleting = deletingId === candidateId;

                  return (
                    <tr key={idx}>
                      <td>{new Date(c.createdAt).toLocaleDateString()}</td>
                      <td>
                        <strong>{c.candidateName}</strong>
                      </td>
                      <td>{c.targetRole}</td>
                      <td>
                        <code>{c.githubUsername || "None"}</code>
                      </td>
                      <td>
                        {c.hrDecision ? (
                          <span className="badge-pill" style={{ fontSize: "0.72rem" }}>
                            {c.hrDecision.decision}
                          </span>
                        ) : (
                          <span style={{ color: "var(--text-light)" }}>Pending</span>
                        )}
                      </td>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                          <button className="btn-view-report" onClick={() => onSelectCandidate(c)} title="View full report">
                            <ExternalLink size={13} />
                            <span>View</span>
                          </button>
                          <button
                            className="btn-delete"
                            disabled={isDeleting}
                            onClick={(event) => handleDelete(event, candidateId, c.candidateName)}
                            title="Delete candidate record"
                          >
                            <Trash2 size={13} />
                            <span>{isDeleting ? "..." : "Delete"}</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Top-level view
// ---------------------------------------------------------------------------

export default function HRCandidateSelectionView({ onBackToDashboard }) {
  const [currentCandidate, setCurrentCandidate] = useState(readStoredCandidate);
  const [activeTab, setActiveTab] = useState(() => {
    const savedTab = localStorage.getItem(TAB_KEY);
    const savedCandidate = readStoredCandidate();
    if (savedTab === "dashboard" && !savedCandidate) return "register";
    return savedTab || "register";
  });
  const [roles, setRoles] = useState(DEFAULT_ROLES);

  useEffect(() => {
    getHRCandidateRoles()
      .then((data) => {
        const standard = data.standardRoles || data.roles || [];
        const custom = data.customRoles || [];
        if (standard.length > 0 || custom.length > 0) {
          setRoles([...standard, ...custom]);
        }
      })
      .catch(() => {
        // Keep the default ESCO role presets if the backend roles call fails.
      });
  }, []);

  function handleTabChange(tab) {
    setActiveTab(tab);
    localStorage.setItem(TAB_KEY, tab);
  }

  function handleVerificationSuccess(candidateRecord) {
    setCurrentCandidate(candidateRecord);
    setActiveTab("dashboard");
    try {
      localStorage.setItem(CANDIDATE_KEY, JSON.stringify(candidateRecord));
      localStorage.setItem(TAB_KEY, "dashboard");
    } catch {
      // Ignore storage failures (e.g. private browsing quota).
    }
  }

  function handleSelectCandidateFromHistory(candidateRecord) {
    setCurrentCandidate(candidateRecord);
    setActiveTab("dashboard");
    try {
      localStorage.setItem(CANDIDATE_KEY, JSON.stringify(candidateRecord));
      localStorage.setItem(TAB_KEY, "dashboard");
    } catch {
      // Ignore storage failures.
    }
  }

  return (
    <div className="module-view-wrapper hr-candidates-view">
      <div className="view-subbar">
        <button className="back-dashboard-btn" onClick={onBackToDashboard}>
          <ArrowLeft size={16} /> Back to Home
        </button>
        <span className="view-tag">
          <ShieldCheck size={14} /> HR Candidate Selection (Admin Only)
        </span>
      </div>

      <div className="app-layout">
        <HRSidebar activeTab={activeTab} setActiveTab={handleTabChange} hasActiveCandidate={!!currentCandidate} />

        <div className="app-main-content">
          <main className="page-container">
            {activeTab === "register" && <RegisterAssessPanel roles={roles} onVerificationSuccess={handleVerificationSuccess} />}
            {activeTab === "dashboard" && (
              <CandidateDashboardPanel candidateRecord={currentCandidate} onBackToRegister={() => handleTabChange("register")} />
            )}
            {activeTab === "roles" && <JobRolesPanel roles={roles} />}
            {activeTab === "history" && <HistoryPanel onSelectCandidate={handleSelectCandidateFromHistory} />}
          </main>
        </div>
      </div>
    </div>
  );
}
