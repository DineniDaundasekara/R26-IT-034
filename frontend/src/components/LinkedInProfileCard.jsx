import React, { useState } from 'react';
import { Award, Briefcase, ExternalLink, MapPin, UserCheck, Shield, CheckCircle } from 'lucide-react';

export default function LinkedInProfileCard({
  candidateName = 'Candidate',
  githubUsername = '',
  linkedinData = null,
  linkedinUrl = null
}) {
  const [imgError, setImgError] = useState(false);

  // Safe data extraction
  const data = linkedinData || {};
  const currentRole = data.current_role || {};
  const certifications = Array.isArray(data.certifications) ? data.certifications : [];
  
  // Candidate profile picture: prioritize scraped LinkedIn photo, or fall back to GitHub verified developer avatar
  const cleanGithub = typeof githubUsername === 'string' ? githubUsername.trim().replace(/^@/, '').replace(/^https?:\/\/github\.com\//i, '').replace(/\/+$/, '') : '';
  const candidateAvatar = cleanGithub ? `https://github.com/${cleanGithub}.png` : null;
  const rawPic = data.profile_pic_url || candidateAvatar;
  const profilePic = (!imgError && rawPic) ? rawPic : null;

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
            <p>Direct profile picture, current employment, and certifications were not imported. Verification proceeded using resume claims and public GitHub evidence.</p>
          </div>
        </div>
      </div>
    );
  }

  // Get Initials for fallback avatar
  const initials = (candidateName || 'Candidate')
    .split(' ')
    .map(p => p[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  const activeUrl = linkedinUrl || data.linkedin_url;
  const isLiveApify = data.source === 'apify';

  return (
    <div className="linkedin-card">
      <div className="linkedin-card-inner">
        
        {/* Left: Profile Avatar & Identity */}
        <div className="linkedin-avatar-col">
          <div className="linkedin-avatar-wrap">
            {profilePic ? (
              <img
                src={profilePic}
                alt={candidateName}
                className="linkedin-avatar-img"
                onError={() => setImgError(true)}
              />
            ) : (
              <div className="linkedin-avatar-placeholder" title="LinkedIn Profile Picture not available from current scraper run">
                {initials}
              </div>
            )}
            <span className="linkedin-verified-dot" title={isLiveApify ? "Verified via Live Apify Scraper" : "LinkedIn Profile Connected"}>
              <CheckCircle size={14} />
            </span>
          </div>
        </div>

        {/* Middle: Name, Current Employment, Location */}
        <div className="linkedin-info-col">
          <div className="linkedin-header-row">
            <div>
              <div className="linkedin-badge-row">
                <span className="linkedin-source-pill">
                  <UserCheck size={12} />
                  LinkedIn Profile Data
                </span>
                {currentRole.is_current && (
                  <span className="status-pill status-pill-verified">
                    Active Employment
                  </span>
                )}
              </div>
              <h3 className="linkedin-candidate-title">{candidateName}</h3>
            </div>


            {activeUrl && (
              <a
                href={activeUrl}
                target="_blank"
                rel="noreferrer"
                className="linkedin-external-btn"
                title="Open Public LinkedIn Profile"
              >
                <span>View LinkedIn</span>
                <ExternalLink size={13} />
              </a>
            )}
          </div>

          {/* Current Job Role */}
          <div className="linkedin-role-box">
            <div className="linkedin-role-line">
              <Briefcase size={15} className="role-icon" />
              <strong className="role-title">
                {currentRole.title || 'Technical Professional'}
              </strong>
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

      {/* Bottom: Listed Certifications */}
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
                      <a
                        href={cert.url}
                        target="_blank"
                        rel="noreferrer"
                        className="cert-link-icon"
                        title="Verify Certificate"
                      >
                        <ExternalLink size={11} />
                      </a>
                    )}
                  </div>
                  <div className="cert-badge-meta">
                    <span className="cert-authority">{cert.authority || 'Accredited Authority'}</span>
                    {cert.year && <span className="cert-year">• {cert.year}</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="certs-empty-msg">
            No formal certifications listed on public profile.
          </div>
        )}
      </div>

    </div>
  );
}
