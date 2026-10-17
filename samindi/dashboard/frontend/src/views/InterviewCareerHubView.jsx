import React from "react";
import {
  Mic,
  FileText,
  ArrowLeft,
  ArrowRight,
  Sparkles,
  Layers,
  GraduationCap,
} from "lucide-react";

export default function InterviewCareerHubView({ onSelectModule, onBackToDashboard, healthData }) {
  return (
    <div className="module-view-wrapper">
      {/* Top Breadcrumb Bar */}
      <div className="view-subbar">
        <button className="back-dashboard-btn" onClick={onBackToDashboard}>
          <ArrowLeft size={16} /> Back to Home
        </button>
        <span className="view-tag">
          <Layers size={14} /> Interview Readiness & Career Path Guidance Suite
        </span>
      </div>

      <main className="dashboard-container" style={{ maxWidth: "1200px", margin: "0 auto", padding: "1.5rem 1.5rem 3rem" }}>
        {/* Hub Header */}
        <section className="hero-dashboard" style={{ textAlign: "center", marginBottom: "2.5rem" }}>
          <div className="eyebrow-pill" style={{ margin: "0 auto 1rem" }}>
            <Sparkles size={14} /> Unified Career Readiness & Guidance
          </div>
          <h1 className="hero-dashboard-title" style={{ fontSize: "2.2rem", marginBottom: "0.75rem" }}>
            Interview Readiness & Career Path Guidance
          </h1>
          <p className="hero-dashboard-lede" style={{ maxWidth: "780px", margin: "0 auto" }}>
            Choose whether to practise spoken interview answers with real-time acoustic and STAR
            discourse NLP analysis, or upload your CV to map your skills, classify your career path,
            and explore live market job vacancies.
          </p>
        </section>

        {/* Dual Cards Grid matching uploaded design */}
        <section className="module-grid-two">
          {/* Card 1: Interview Readiness & Communication Guidance */}
          <article className="module-interactive-card ir-card">
            <div className="card-top-row">
              <span className="card-badge ir-badge">
                <Mic size={14} /> INTERVIEWREADY · SPOKEN NLP COMPONENT
              </span>
              <span className="status-indicator-tag">
                <span className={`status-dot ${healthData?.communicationModelReady ? "ok" : "warn"}`} />
                {healthData?.communicationModelReady ? "ML Classifier Ready" : "Checking Model"}
              </span>
            </div>

            <h2>Interview Readiness & Communication Guidance</h2>
            <p className="card-description">
              Analyze interview communication preparedness with live microphone recording or audio
              upload. Get supervised machine-learning communication classification, acoustic
              diagnostics (speech rate, pause ratios, silence ratio, audio energy), STAR discourse breakdown,
              and explainable, grounded AI coaching.
            </p>

            <div className="feature-tags-cloud">
              <span>Faster-Whisper</span>
              <span>Acoustic + NLP Features</span>
              <span>Trained ML Pipeline</span>
              <span>STAR Diagnostics</span>
              <span>Grounded AI Coach</span>
            </div>

            <button
              className="action-launch-btn ir-btn"
              onClick={() => onSelectModule("communication")}
            >
              <span>Start Interview Guidance</span>
              <ArrowRight size={18} />
            </button>
          </article>

          {/* Card 2: CV based career path guidance */}
          <article className="module-interactive-card cl-card">
            <div className="card-top-row">
              <span className="card-badge cl-badge">
                <FileText size={14} /> CAREERLENS · SUPERVISED CV COMPONENT
              </span>
              <span className="status-indicator-tag">
                <span className={`status-dot ${healthData?.careerModelReady ? "ok" : "warn"}`} />
                {healthData?.careerModelReady ? "Career Model Ready" : "Checking Model"}
              </span>
            </div>

            <h2>CV based career path guidance</h2>
            <p className="card-description">
              Upload your CV in PDF, DOCX, or TXT format. Classify your optimal career direction with
              our trained NLP model, evaluate decoupled structural quality vs role alignment, and
              compare your skills with live vacancies across Google Jobs, TopJobs, and LinkedIn.
            </p>

            <div className="feature-tags-cloud">
              <span>CV Text Extraction</span>
              <span>TF-IDF + ML Classifier</span>
              <span>Decoupled 2D Evaluation</span>
              <span>Google & TopJobs Live Vacancies</span>
              <span>Explainable Skill Gaps</span>
            </div>

            <button
              className="action-launch-btn cl-btn"
              onClick={() => onSelectModule("career")}
            >
              <span>Explore Career Path Guidance</span>
              <ArrowRight size={18} />
            </button>
          </article>
        </section>
      </main>
    </div>
  );
}
