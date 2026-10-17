import React from "react";
import {
  Mic,
  FileText,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  Layers,
  GraduationCap,
  Activity,
  TrendingUp,
  UserCheck,
} from "lucide-react";

export default function DashboardView({ onSelectModule, healthData, user }) {
  const firstName = user?.fullName?.split(" ")[0] || "there";

  function scrollToTools() {
    document.getElementById("career-tools")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <main className="dashboard-container">
      {/* Hero Header */}
      <section className="hero-dashboard">
        <div className="eyebrow-pill">
          <Sparkles size={14} /> AI-Driven Research Platform
        </div>
        <p className="home-welcome">Welcome back, {firstName}</p>
        <h1 className="hero-dashboard-title">
          AI-Powered Career Intelligence Platform
        </h1>
        <p className="hero-dashboard-lede">
          An explainable career development and recruitment decision-support platform designed to
          help individuals improve career readiness, explore career development opportunities,
          understand future career risks, and support transparent employer decision-making.
        </p>
        <button type="button" className="hero-cta-btn" onClick={scrollToTools}>
          <span>Explore Career Tools</span>
          <ArrowRight size={16} />
        </button>
      </section>

      {/* Main Interactive Cards / Buttons */}
      <section className="module-grid-two" id="career-tools">
        {/* Combined Module 1 & 2: Interview Readiness & Career Path Guidance */}
        <article className="module-interactive-card ir-card">
          <div className="card-top-row">
            <span className="card-badge ir-badge">
              <Layers size={14} /> PathReady AI Suite · Spoken NLP & CV Guidance
            </span>
            <span className="status-indicator-tag">
              <span className={`status-dot ${healthData?.communicationModelReady && healthData?.careerModelReady ? "ok" : "warn"}`} />
              {healthData?.communicationModelReady && healthData?.careerModelReady ? "Guidance Models Ready" : "Checking Models"}
            </span>
          </div>

          <h2>Interview Readiness & Career Path Guidance</h2>
          <p className="card-description">
            Dual AI-driven career development suite: practise spoken interview answers with real-time
            acoustic and STAR discourse analysis (InterviewReady), or upload your CV to map your skill
            profile, classify optimal career trajectories, and explore live job market vacancies (CareerLens).
          </p>

          <div className="feature-tags-cloud">
            <span>Faster-Whisper ASR</span>
            <span>Acoustic & STAR Diagnostics</span>
            <span>Supervised CV Classifier</span>
            <span>Decoupled 2D Evaluation</span>
            <span>Live Vacancies Search</span>
            <span>Grounded AI Coaching</span>
          </div>

          <button
            className="action-launch-btn ir-btn"
            onClick={() => onSelectModule("interview-career")}
          >
            <span>Explore Readiness & Career Guidance</span>
            <ArrowRight size={18} />
          </button>
        </article>

        {/* Module 3: Career risk & industry stability analysis */}
        <article className="module-interactive-card cr-card">
          <div className="card-top-row">
            <span className="card-badge cr-badge">
              <ShieldAlert size={14} /> Career Safety · Explainable Risk Component
            </span>
            <span className="status-indicator-tag">
              <span className={`status-dot ${healthData?.careerRiskModelReady ? "ok" : "warn"}`} />
              {healthData?.careerRiskModelReady ? "Risk Model Ready" : "Checking Model"}
            </span>
          </div>

          <h2>Career Safety & Industry Stability</h2>
          <p className="card-description">
            Assess long-term career sustainability using automation exposure, industry stability,
            skill transferability and adaptability indicators from a trained Random Forest model,
            with explainable career risk mitigation guidance and a personalized 30/60/90-day
            resilience action plan.
          </p>

          <div className="feature-tags-cloud">
            <span>Random Forest Classifier</span>
            <span>Auxiliary Indicator Models</span>
            <span>Explainable Risk Mapping</span>
            <span>30/60/90-Day Action Plan</span>
            <span>Assessment History</span>
          </div>

          <button
            className="action-launch-btn cr-btn"
            onClick={() => onSelectModule("career-risk")}
          >
            <span>Check Career Safety</span>
            <ArrowRight size={18} />
          </button>
        </article>

        {/* Module 4: Employability Simulator (Behaviour-Aware Career Simulation) */}
        <article className="module-interactive-card em-card">
          <div className="card-top-row">
            <span className="card-badge em-badge">
              <Activity size={14} /> Employability Simulator · 3 Validated Models
            </span>
            <span className="status-indicator-tag">
              <span className={`status-dot ${healthData?.employabilityModelsReady ? "ok" : "warn"}`} />
              {healthData?.employabilityModelsReady ? "Models Ready" : "Checking Models"}
            </span>
          </div>

          <h2>Behaviour-Aware Career Simulation</h2>
          <p className="card-description">
            Explore how internship experience, workplace competence, and psychological capital
            influence employability through three validated regression models, with construct-level
            explainable breakdowns and personalized development guidance.
          </p>

          <div className="feature-tags-cloud">
            <span>Internship Experience (XGBoost)</span>
            <span>Competence (Linear Regression)</span>
            <span>Psychological Capital (ElasticNet)</span>
            <span>Construct-Level Guidance</span>
          </div>

          <button
            className="action-launch-btn em-btn"
            onClick={() => onSelectModule("employability")}
          >
            <span>Explore Career Simulation</span>
            <ArrowRight size={18} />
          </button>
        </article>

        {/* Module 5 (admin only): HR Candidate Selection */}
        {user?.role === "admin" && (
          <article className="module-interactive-card sv-card">
            <div className="card-top-row">
              <span className="card-badge sv-badge">
                <UserCheck size={14} /> HR Tool · Admin Only
              </span>
              <span className="status-indicator-tag">
                <span className={`status-dot ${healthData?.hrCandidateModelReady ? "ok" : "warn"}`} />
                {healthData?.hrCandidateModelReady ? "Verification Engine Ready" : "Checking Model"}
              </span>
            </div>

            <h2>HR Candidate Selection</h2>
            <p className="card-description">
              Admin-only recruiter tool: cross-reference a candidate resume against independent
              public GitHub artifacts and a direct LinkedIn profile lookup, producing an
              explainable, evidence-grounded assessment with a human-in-the-loop hiring decision
              panel.
            </p>

            <div className="feature-tags-cloud">
              <span>ESCO v1.1 Knowledge Graph</span>
              <span>GitHub Evidence Mining</span>
              <span>Direct LinkedIn Lookup</span>
              <span>4-Way Epistemic Verification</span>
            </div>

            <button
              className="action-launch-btn sv-btn"
              onClick={() => onSelectModule("hr-candidates")}
            >
              <span>Open HR Candidate Selection</span>
              <ArrowRight size={18} />
            </button>
          </article>
        )}
      </section>

      {/* Why Use Career Intelligence? */}
      <section className="why-panel">
        <div className="viva-panel-header">
          <span className="viva-label">Platform Principles</span>
          <h3>Why Use Career Intelligence?</h3>
        </div>

        <div className="why-grid">
          <div className="why-item">
            <div className="metric-icon"><Sparkles size={20} /></div>
            <h4>Explainable Guidance</h4>
            <p>Understand the reasoning behind career-related recommendations.</p>
          </div>
          <div className="why-item">
            <div className="metric-icon"><TrendingUp size={20} /></div>
            <h4>Personalized Development</h4>
            <p>Receive guidance based on relevant skills, behaviours and professional evidence.</p>
          </div>
          <div className="why-item">
            <div className="metric-icon"><ShieldCheck size={20} /></div>
            <h4>Responsible AI</h4>
            <p>Support human decision-making instead of replacing it with automated judgments.</p>
          </div>
        </div>
      </section>

      {/* Research Viva Panel Technical Summary */}
      <section className="viva-overview-panel">
        <div className="viva-panel-header">
          <span className="viva-label">Research Architecture</span>
          <h3>Four-Component System Overview</h3>
          <p>
            Designed for transparent, evidence-based candidate assessment without hallucinated metrics or artificial score inflation.
          </p>
        </div>

        <div className="viva-metrics-grid">
          <div className="viva-metric-item">
            <div className="metric-icon"><Mic size={20} /></div>
            <h4>Spoken Communication NLP</h4>
            <p>
              Combines Faster-Whisper ASR, 9 acoustic signal features (MFCC, F0, silence, speech rate), and NLP discourse parsing with a trained multi-class classifier.
            </p>
            <div className="metric-highlight">Categories: Poor · Average · Good · Excellent</div>
          </div>

          <div className="viva-metric-item">
            <div className="metric-icon"><FileText size={20} /></div>
            <h4>Decoupled Career-Path Evaluation</h4>
            <p>
              TF-IDF supervised career-path classification decoupled from a separate structural CV quality vs. target-role market alignment assessment, preventing false penalties during career transitions.
            </p>
            <div className="metric-highlight">Model: TF-IDF + LinearSVC / LogisticRegression</div>
          </div>

          <div className="viva-metric-item">
            <div className="metric-icon"><Layers size={20} /></div>
            <h4>Explainable Career Risk Modeling</h4>
            <p>
              A trained Random Forest classifier plus auxiliary indicator sub-models produce a career risk level with system-derived stability, automation-exposure, and adaptability explanations.
            </p>
            <div className="metric-highlight">Model: Random Forest + Auxiliary Indicators</div>
          </div>

          <div className="viva-metric-item">
            <div className="metric-icon"><Activity size={20} /></div>
            <h4>Behaviour-Aware Employability Simulation</h4>
            <p>
              Three frozen regression models translate internship experience, competence, and
              psychological capital survey responses into a continuous employability prediction
              with construct-level strengths and development priorities.
            </p>
            <div className="metric-highlight">Models: XGBoost + Linear Regression + ElasticNet</div>
          </div>
        </div>
      </section>
    </main>
  );
}
