import React from 'react';

export default function JobRolesPage({ roles }) {
  return (
    <section className="page-view active">
      <div className="hero-header">
        <h1 className="hero-title">Job Role Profiles & Skill Requirements</h1>
        <p className="hero-subtitle">
          Standardized software engineering job roles grounded in the European Commission ESCO taxonomy.
        </p>
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
                <span key={sIdx} className="pill-tag req">{s.name}</span>
              ))}
            </div>

            <div className="skill-list-heading">Optional:</div>
            <div className="skill-pills-wrap">
              {(r.preferredSkills || []).map((s, sIdx) => (
                <span key={sIdx} className="pill-tag">{s.name}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
