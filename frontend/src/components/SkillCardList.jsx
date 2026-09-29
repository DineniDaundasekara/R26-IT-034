import React from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, HelpCircle, Code, Clock, Calendar, ShieldCheck } from 'lucide-react';

export default function SkillCardList({ skills = [] }) {
  if (!skills || skills.length === 0) {
    return <div className="empty-state-box">No skill verification records available.</div>;
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'SUPPORTED':
        return {
          label: 'Verified with Public Code',
          pillClass: 'status-pill-verified',
          icon: <CheckCircle2 size={14} color="#16a34a" />
        };
      case 'PARTIALLY_SUPPORTED':
        return {
          label: 'Partially Verified',
          pillClass: 'status-pill-partial',
          icon: <AlertTriangle size={14} color="#d97706" />
        };
      case 'POTENTIAL_CONTRADICTION':
        return {
          label: 'Timeline Discrepancy',
          pillClass: 'status-pill-contradiction',
          icon: <AlertCircle size={14} color="#dc2626" />
        };
      case 'INSUFFICIENT_EVIDENCE':
      default:
        return {
          label: 'Private Experience',
          pillClass: 'status-pill-unobserved',
          icon: <HelpCircle size={14} color="#64748b" />
        };
    }
  };

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

  return (
    <div className="skills-verification-container">
      <div className="section-title-row">
        <h3 className="section-title">Technical Skill Cross-Source Audit</h3>
        <span className="section-subtitle">{skills.length} skills evaluated against ESCO taxonomy & public GitHub</span>
      </div>

      <div className="skill-cards-grid">
        {sortedSkills.map((s, idx) => {
          const badge = getStatusBadge(s.status);
          const gh = s.githubEvidence || {};
          const temporal = gh.temporalMetrics || {};

          return (
            <div key={idx} className={`skill-card ${badge.pillClass}-border`}>
              <div className="skill-card-top">
                <div className="skill-title-block">
                  <span className="skill-name">{s.skillName}</span>
                  {s.isRequired && <span className="badge-required">Mandatory</span>}
                </div>
                <span className={`status-pill ${badge.pillClass}`}>
                  {badge.icon}
                  <span>{badge.label}</span>
                </span>
              </div>

              {/* Solid Duration Details */}
              <div className="skill-metrics-row">
                <div className="metric-item">
                  <Calendar size={13} className="metric-icon" />
                  <span className="metric-label">Mentioned on CV:</span>
                  <strong className="metric-value">
                    {temporal.claimedSolidDuration || (s.claimedYears ? `${s.claimedYears} Year(s)` : 'Mentioned')}
                  </strong>
                </div>

                <div className="metric-item">
                  <Clock size={13} className="metric-icon" />
                  <span className="metric-label">Public GitHub:</span>
                  <strong className="metric-value">
                    {temporal.observedSolidDuration || (gh.hasEvidence ? `${gh.relevantProjectsCount} Repo(s)` : '0 Days (Private)')}
                  </strong>
                </div>
              </div>

              {/* Justification Comment */}
              {s.justification && (
                <p className="skill-justification-text">
                  {s.justification}
                </p>
              )}

              {/* Relevant Repos Tags */}
              {gh.relevantRepos && gh.relevantRepos.length > 0 && (
                <div className="skill-repos-tag-wrap">
                  <span className="repos-label">Public Artifacts:</span>
                  {gh.relevantRepos.map((repo, rIdx) => (
                    <span key={rIdx} className="repo-code-tag">
                      <Code size={11} />
                      {repo.name}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
