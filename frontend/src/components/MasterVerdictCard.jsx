import React from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Sparkles } from 'lucide-react';

export default function MasterVerdictCard({ finalVerdict, candidateName, targetRole }) {
  if (!finalVerdict) return null;

  const isSuitable = finalVerdict.verdictType === "SUITABLE";
  const isPartial = finalVerdict.verdictType === "PARTIALLY_SUITABLE";
  const isNotSuitable = finalVerdict.verdictType === "NOT_SUITABLE";

  const cardThemeClass = isSuitable
    ? "verdict-card-suitable"
    : isPartial
    ? "verdict-card-partial"
    : "verdict-card-notsuitable";

  const badgeClass = isSuitable
    ? "verdict-badge-green"
    : isPartial
    ? "verdict-badge-amber"
    : "verdict-badge-red";

  const iconColor = isSuitable ? "#16a34a" : isPartial ? "#d97706" : "#dc2626";

  return (
    <div className={`master-verdict-card ${cardThemeClass}`}>
      <div className="verdict-header">
        <div className="verdict-badge-row">
          <span className={`verdict-pill ${badgeClass}`}>
            {isSuitable && <CheckCircle2 size={16} color={iconColor} />}
            {isPartial && <AlertTriangle size={16} color={iconColor} />}
            {isNotSuitable && <AlertCircle size={16} color={iconColor} />}
            <span>FINAL HIRING VERDICT</span>
          </span>
          <span className="verdict-role-sub">{targetRole}</span>
        </div>
      </div>

      <h2 className="verdict-main-text">{finalVerdict.status}</h2>

      {finalVerdict.summaryComment && (
        <p className="verdict-comment-text">
          <Sparkles size={16} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'text-bottom' }} />
          {finalVerdict.summaryComment}
        </p>
      )}

      {/* Matched Skills & Areas for Improvement */}
      <div className="verdict-skills-grid">
        {finalVerdict.matchedSkills && finalVerdict.matchedSkills.length > 0 && (
          <div className="verdict-skill-group">
            <h4 className="skill-group-title text-green">
              <CheckCircle2 size={14} />
              Matched Technical Skills ({finalVerdict.matchedSkills.length})
            </h4>
            <div className="skill-badge-wrap">
              {finalVerdict.matchedSkills.map((skill, idx) => (
                <span key={idx} className="badge-skill-matched">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {finalVerdict.skillsToImprove && finalVerdict.skillsToImprove.length > 0 && (
          <div className="verdict-skill-group">
            <h4 className="skill-group-title text-amber">
              <AlertTriangle size={14} />
              Areas for Improvement ({finalVerdict.skillsToImprove.length})
            </h4>
            <div className="skill-badge-wrap">
              {finalVerdict.skillsToImprove.map((skill, idx) => (
                <span key={idx} className="badge-skill-improve">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
