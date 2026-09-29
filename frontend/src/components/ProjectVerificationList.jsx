import React from 'react';
import { FolderGit2, ExternalLink, CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react';

export default function ProjectVerificationList({ projects = [] }) {
  if (!projects || projects.length === 0) {
    return null;
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'SUPPORTED':
        return {
          label: 'Matched Public Repository',
          pillClass: 'status-pill-verified',
          icon: <CheckCircle2 size={13} color="#16a34a" />
        };
      case 'PARTIALLY_SUPPORTED':
        return {
          label: 'Partial Match',
          pillClass: 'status-pill-partial',
          icon: <CheckCircle2 size={13} color="#d97706" />
        };
      case 'INSUFFICIENT_EVIDENCE':
      default:
        return {
          label: 'Private Enterprise Repository',
          pillClass: 'status-pill-unobserved',
          icon: <HelpCircle size={13} color="#64748b" />
        };
    }
  };

  return (
    <div className="projects-verification-container">
      <div className="section-title-row">
        <h3 className="section-title">Resume Project Artifact Alignment</h3>
        <span className="section-subtitle">{projects.length} project claims cross-referenced with public repositories</span>
      </div>

      <div className="project-cards-grid">
        {projects.map((p, idx) => {
          const badge = getStatusBadge(p.status);

          return (
            <div key={idx} className="project-card">
              <div className="project-card-header">
                <div className="project-title-group">
                  <FolderGit2 size={16} className="text-muted" />
                  <strong className="project-name">{p.projectName}</strong>
                </div>
                <span className={`status-pill ${badge.pillClass}`}>
                  {badge.icon}
                  <span>{badge.label}</span>
                </span>
              </div>

              {p.description && (
                <p className="project-desc-text">{p.description}</p>
              )}

              {p.technologies && p.technologies.length > 0 && (
                <div className="project-tech-badges">
                  {p.technologies.map((t, tIdx) => (
                    <span key={tIdx} className="tech-badge">
                      {t}
                    </span>
                  ))}
                </div>
              )}

              {p.matchedRepository && (
                <div className="matched-repo-box">
                  <span className="matched-repo-label">Corroborating Repo:</span>
                  <a
                    href={p.repositoryUrl || `https://github.com/${p.matchedRepository}`}
                    target="_blank"
                    rel="noreferrer"
                    className="matched-repo-link"
                  >
                    <code>{p.matchedRepository}</code>
                    <ExternalLink size={12} />
                  </a>
                </div>
              )}

              {p.justification && (
                <p className="project-justification-note">{p.justification}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
