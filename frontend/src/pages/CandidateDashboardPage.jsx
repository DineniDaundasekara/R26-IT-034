import React, { useState } from 'react';
import { ArrowLeft, Printer, ExternalLink, CheckCircle2, AlertCircle, TrendingUp, FileText, Info, GitCommit, Users, Activity, ShieldCheck, FolderGit2 } from 'lucide-react';
import axios from 'axios';
import LinkedInProfileCard from '../components/LinkedInProfileCard';
import GitHubAnalyticsCard from '../components/GitHubAnalyticsCard';





export default function CandidateDashboardPage({ candidateRecord, onBackToRegister }) {
  if (!candidateRecord) return null;

  const assessment = candidateRecord.assessment || {};
  const overall = assessment.overallAssessment || {};
  const counts = assessment.verificationCounts || {};
  const skills = assessment.skillVerifications || [];
  
  // Sort skills: Verified (SUPPORTED) first, followed by others
  const sortedSkills = [...skills].sort((a, b) => {
    const order = {
      'SUPPORTED': 1,
      'PARTIALLY_SUPPORTED': 2,
      'INSUFFICIENT_EVIDENCE': 3,
      'NOT_DETECTED': 4,
      'POTENTIAL_CONTRADICTION': 5
    };
    return (order[a.status] || 99) - (order[b.status] || 99);
  });

  const projects = assessment.projectVerifications || [];
  const ree = assessment.repositoryEngineeringEvidence || candidateRecord.repositoryEngineeringEvidence || {};
  const reeSummary = ree.summary || {};
  const reeMaint = ree.maintenance || {};
  const reeCollab = ree.collaboration || {};
  const reeAct = ree.activityMaturity || {};
  const reeRepos = ree.repositorySummaries || [];

  const linkedinData = assessment.linkedinData || candidateRecord.linkedinProfile || candidateRecord.linkedinData || null;
  const linkedinUrl = candidateRecord.linkedinUrl || assessment.linkedinUrl || (linkedinData && linkedinData.linkedin_url) || null;

  const [recruiterNotes, setRecruiterNotes] = useState('');

  const [savedDecision, setSavedDecision] = useState(candidateRecord.hrDecision);


  // Final Verdict data with robust fallback
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
    matchScore: overall.profileStatus?.includes("DISCREPANCIES") ? 45 : overall.profileStatus?.includes("PARTIALLY") ? 72 : 88,
    summaryComment: overall.explanation || "Candidate technical evaluation based on verified public code and resume claims.",
    matchedSkills: skills.filter(s => s.status !== "NOT_DETECTED" && s.status !== "POTENTIAL_CONTRADICTION").map(s => s.skillName),
    skillsToImprove: skills.filter(s => s.status === "NOT_DETECTED" || s.status === "PARTIALLY_SUPPORTED" || s.status === "POTENTIAL_CONTRADICTION").map(s => `${s.skillName} (${s.status === 'NOT_DETECTED' ? 'Missing' : 'Requires Upskilling'})`)
  };

  let friendlyStatus = "Verified Match";
  let statusClass = "status-pill-verified";
  let summaryHeading = "Technical Skills Supported by Evidence";

  if (overall.profileStatus?.includes("STRONGLY")) {
    friendlyStatus = "Strong Technical Match";
    statusClass = "status-pill-verified";
    summaryHeading = "Strong Public Evidence Found";
  } else if (overall.profileStatus?.includes("PARTIALLY")) {
    friendlyStatus = "Partially Verified Match";
    statusClass = "status-pill-partial";
    summaryHeading = "Key Skills Verified, Some Recent";
  } else if (overall.profileStatus?.includes("DISCREPANCIES")) {
    friendlyStatus = "Timeline Discrepancy Found";
    statusClass = "status-pill-contradiction";
    summaryHeading = "Check Candidate Timeline in Interview";
  } else {
    friendlyStatus = "Private Experience";
    statusClass = "status-pill-unobserved";
    summaryHeading = "Skills Not Found on Public GitHub";
  }

  const handleDecisionClick = async (decisionText) => {
    try {
      const resp = await axios.post(`/api/candidates/${candidateRecord.assessmentId}/decision`, {
        decision: decisionText,
        notes: recruiterNotes,
        reviewerName: "Hiring Manager"
      });
      setSavedDecision(resp.data.record.hrDecision);
    } catch (err) {
      console.error("Decision save failed:", err);
      alert("Failed to save decision.");
    }
  };

  return (
    <section className="page-view active">
      
      {/* Page Header & Top Actions */}
      <div className="dashboard-page-header">
        <div className="dashboard-header-text">
          <h1 className="dashboard-page-title">Candidate Assessment Report</h1>
          <p className="dashboard-page-subtitle">
            Comprehensive skill verification, empirical repository analytics, and recruiter guidance.
          </p>
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

      {/* Candidate Header Card */}
      <div className="candidate-header-card">
        <div className="candidate-header-left">
          <span className="role-tag">{candidateRecord.targetRole}</span>
          <h1 className="candidate-name-title">{candidateRecord.candidateName}</h1>
          <div className="candidate-meta-row">
            <span>{candidateRecord.email || "No email listed"}</span>
            <span className="meta-dot">•</span>
            <span>GitHub: <code>{candidateRecord.githubUsername || "None"}</code></span>
            <span className="meta-dot">•</span>
            <span>{new Date(candidateRecord.createdAt || Date.now()).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      {/* Direct LinkedIn Profile Card (Profile Pic, Current Role, Certifications) */}
      <LinkedInProfileCard
        candidateName={candidateRecord.candidateName}
        githubUsername={candidateRecord.githubUsername}
        linkedinData={linkedinData}
        linkedinUrl={linkedinUrl}
      />

      {/* 1. Dedicated Final Assessment & Recommendation Verdict Card */}
      <div className={`verdict-master-card verdict-${(finalVerdict.verdictType || 'SUITABLE').toLowerCase()}`}>

        <div className="verdict-header-row">
          <div className="verdict-title-group">
            <span className="verdict-overline">Recruiter Hiring Assessment & Recommendation</span>
            <h2 className="verdict-status-title">
              {finalVerdict.status}
            </h2>
          </div>
        </div>

        {/* 2. Recruiter Summary Comment */}
        <div className="verdict-comment-box">
          <div className="comment-label-row">
            <FileText size={16} />
            <strong>Executive Candidate Summary (Comment)</strong>
          </div>
          <p className="verdict-comment-text">
            {finalVerdict.summaryComment}
          </p>
        </div>

        {/* 3 & 4. Matched Skills & Areas for Improvement Grid */}
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
                  <AlertCircle size={12} />
                  {sk}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Stat Cards: Verified Skills & No Public Evidence */}
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

      {/* Skill-by-Skill Verification Section */}
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
            
            // Format solid duration with days
            const formatObservedDuration = (temporal) => {
              if (!temporal || !temporal.observedPublicYears || temporal.observedPublicYears <= 0) {
                return "Not found in GitHub";
              }
              const y = temporal.observedPublicYears;
              const d = temporal.daysSinceFirstActivity && temporal.daysSinceFirstActivity > 0
                ? temporal.daysSinceFirstActivity
                : Math.round(y * 365.25);
              
              if (y >= 1.0) {
                const solidY = Math.round(y);
                const yrText = solidY === 1 ? "1 Year" : `${solidY} Years`;
                return `${yrText} (${d} days public code)`;
              } else {
                const mos = Math.max(1, Math.round(y * 12));
                const moText = mos === 1 ? "1 Month" : `${mos} Months`;
                return `${moText} (${d} days public code)`;
              }
            };

            const formatClaimedDuration = (claimedY) => {
              if (!claimedY || claimedY <= 0) return "Mentioned on resume";
              const d = Math.round(claimedY * 365);
              if (claimedY >= 1.0) {
                const solidY = Math.round(claimedY);
                const yrText = solidY === 1 ? "1 Year" : `${solidY} Years`;
                return `${yrText} (${d} days mentioned)`;
              } else {
                const mos = Math.max(1, Math.round(claimedY * 12));
                const moText = mos === 1 ? "1 Month" : `${mos} Months`;
                return `${moText} (${d} days mentioned)`;
              }
            };

            const obsY = formatObservedDuration(t);
            const claimY = formatClaimedDuration(sv.claimedYears);

            return (
              <div key={idx} className="skill-row-card">
                <div className="skill-top-bar">
                  <div className="skill-main-info">
                    <span className="skill-title-text">{sv.skillName}</span>
                    <span className={`badge-tag ${sv.isRequired ? 'badge-required' : 'badge-preferred'}`}>
                      {sv.isRequired ? 'Required for Role' : 'Optional'}
                    </span>
                    <span className="badge-tag badge-cat">{sv.category}</span>
                  </div>
                  <span className={`status-pill ${badgeClass}`}>{friendlyLabel}</span>
                </div>

                <div className="skill-justification-box">
                  {sv.justification}
                </div>

                <div className="skill-meta-columns">
                  <div className="meta-item">
                    <span>Mentioned on Resume:</span>
                    <strong>{claimY}</strong>
                  </div>
                  <div className="meta-item">
                    <span>Observed Public GitHub:</span>
                    <strong>{obsY}</strong>
                  </div>
                </div>

                {sv.githubEvidence?.relevantRepos?.length > 0 && (
                  <div className="repo-evidence-row">
                    <span>Public Repositories:</span>
                    {sv.githubEvidence.relevantRepos.map((r, rIdx) => (
                      <a key={rIdx} href={r.htmlUrl || '#'} target="_blank" rel="noreferrer" className="repo-pill-link">
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

      {/* GitHub Behaviour Analytics Card (Modern UI/UX matching screenshot) */}
      <GitHubAnalyticsCard
        candidateRecord={candidateRecord}
        assessment={assessment}
        ree={ree}
      />

      <div className="content-block ree-content-block" style={{ marginTop: '1.5rem' }}>

        {/* Top Repositories Analyzed Table */}
        {reeRepos.length > 0 && (
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
                        {r.hasRelease && <span className="format-chip" style={{ marginLeft: '6px' }}>Release</span>}
                      </td>
                      <td><code>{r.language}</code></td>
                      <td>
                        <span className={`ree-status-badge ree-status-${r.maintenanceStatus?.toLowerCase()}`}>
                          {r.maintenanceStatus} ({r.daysSinceLastCommit}d ago)
                        </span>
                      </td>
                      <td>
                        <span className={`ree-status-badge ree-status-${r.collaborationStatus?.toLowerCase()}`}>
                          {r.collaborationStatus?.replace('_', ' ')} ({r.contributors} contribs)
                        </span>
                      </td>
                      <td>
                        <span className={`ree-status-badge ree-status-${r.activityStatus?.toLowerCase()}`}>
                          {r.commits} commits
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Human Decision Panel */}
      <div className="decision-panel-card">
        <div className="decision-header">
          <h2 className="decision-title">Recruiter Next Steps</h2>
          <p className="decision-desc">The AI provides clear evidence. You make the final hiring decision based on these recommendations.</p>
        </div>

        <div className="decision-options-grid">
          {(assessment.hrDecisionSupport || []).map((action, aIdx) => (
            <button
              key={aIdx}
              type="button"
              className={`btn-decision-card ${action.recommended ? 'recommended' : ''}`}
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
            onChange={(e) => setRecruiterNotes(e.target.value)}
          />
        </div>

        {savedDecision && (
          <div className="recorded-confirmation-banner">
            <CheckCircle size={20} />
            <div>
              <strong>Decision Recorded:</strong> {savedDecision.decision} by {savedDecision.reviewerName || 'Hiring Manager'} (Logged in audit history)
            </div>
          </div>
        )}
      </div>

    </section>
  );
}
