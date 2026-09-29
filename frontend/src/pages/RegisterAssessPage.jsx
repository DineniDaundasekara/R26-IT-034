import React, { useState } from 'react';
import { UploadCloud, FileText, CheckCircle2, Trash2, ArrowRight } from 'lucide-react';
import axios from 'axios';

export default function RegisterAssessPage({ roles, onVerificationSuccess }) {
  const [candidateName, setCandidateName] = useState('');
  const [email, setEmail] = useState('');
  const [github, setGithub] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [apifyToken, setApifyToken] = useState('');
  const [targetRoleId, setTargetRoleId] = useState('full_stack_mern');
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);

  const selectedRole = roles.find(r => r.roleId === targetRoleId) || roles[0];

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleRemoveFile = (e) => {
    e.stopPropagation();
    setFile(null);
    const fileInput = document.getElementById('react-resume-file');
    if (fileInput) fileInput.value = '';
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 KB';
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    return `${(kb / 1024).toFixed(2)} MB`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!candidateName.trim()) {
      alert('Please enter the candidate name.');
      return;
    }
    if (!file) {
      alert('Please upload a candidate resume PDF document.');
      return;
    }

    setLoading(true);

    try {
      // Normalize github and linkedin inputs
      let cleanGithub = github.trim();
      cleanGithub = cleanGithub
        .replace(/^https?:\/\/(www\.)?github\.com\//i, '')
        .replace(/^github\.com\//i, '')
        .replace(/^@/, '')
        .replace(/\/+$/, '');
      if (cleanGithub.includes('/')) cleanGithub = cleanGithub.split('/')[0];
      if (cleanGithub.includes('?')) cleanGithub = cleanGithub.split('?')[0];

      let cleanLinkedin = linkedinUrl.trim();
      if (cleanLinkedin && !cleanLinkedin.startsWith('http://') && !cleanLinkedin.startsWith('https://')) {
        if (cleanLinkedin.startsWith('linkedin.com') || cleanLinkedin.startsWith('www.linkedin.com')) {
          cleanLinkedin = `https://${cleanLinkedin}`;
        } else if (cleanLinkedin.startsWith('in/')) {
          cleanLinkedin = `https://www.linkedin.com/${cleanLinkedin}`;
        } else {
          cleanLinkedin = `https://www.linkedin.com/in/${cleanLinkedin}`;
        }
      }

      const formData = new FormData();
      formData.append('candidate_name', candidateName);
      formData.append('email', email);
      formData.append('github_username', cleanGithub);
      if (cleanLinkedin) formData.append('linkedin_url', cleanLinkedin);
      if (apifyToken) formData.append('apify_token', apifyToken);
      formData.append('target_role_id', targetRoleId);
      formData.append('resume_file', file);

      const resp = await axios.post('/api/candidates/assess', formData);
      onVerificationSuccess(resp.data);

    } catch (err) {
      console.error('Verification failed:', err);
      alert(`Verification error: ${err.response?.data?.message || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="page-view active">
      <div className="hero-header">
        <h1 className="hero-title">Verify Candidate Technical Skills with Real Evidence</h1>
        <p className="hero-subtitle">
          Upload a candidate's resume PDF to cross-reference their claimed skills, coding timelines, and projects against independent public GitHub code.
        </p>
      </div>

      <div className="form-wrapper">
        <div className="minimal-card">
          <form onSubmit={handleSubmit}>
            
            {/* Step 1: Candidate Info */}
            <div className="form-section-title">
              <span className="step-num">1</span>
              <span>Candidate Information</span>
            </div>

            <div className="form-grid-2">
              <div className="input-field">
                <label>Full Name <span className="req">*</span></label>
                <input
                  type="text"
                  placeholder="e.g. Alex Doe"
                  value={candidateName}
                  onChange={(e) => setCandidateName(e.target.value)}
                  required
                />
              </div>

              <div className="input-field">
                <label>Email Address</label>
                <input
                  type="email"
                  placeholder="e.g. alex@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div className="form-grid-2">
              <div className="input-field">
                <label>GitHub Username <span className="helper">(Optional)</span></label>
                <div className="input-prefix-wrap">
                  <span className="prefix">github.com/</span>
                  <input
                    type="text"
                    placeholder="username"
                    value={github}
                    onChange={(e) => setGithub(e.target.value)}
                  />
                </div>
              </div>

              <div className="input-field">
                <label>LinkedIn Profile URL <span className="helper">(Optional)</span></label>
                <div className="input-prefix-wrap">
                  <span className="prefix">linkedin.com/in/</span>
                  <input
                    type="text"
                    placeholder="username or full URL"
                    value={linkedinUrl}
                    onChange={(e) => setLinkedinUrl(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <div className="input-field" style={{ marginBottom: '1.2rem' }}>
              <label>Target Job Role <span className="req">*</span></label>
              <select
                value={targetRoleId}
                onChange={(e) => setTargetRoleId(e.target.value)}
              >
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
                    <span key={idx} className="pill-tag req">{s.name} (Required)</span>
                  ))}
                  {(selectedRole.preferredSkills || []).map((s, idx) => (
                    <span key={idx} className="pill-tag">{s.name} (Optional)</span>
                  ))}
                </div>
              </div>
            )}

            {/* Step 2: Dedicated PDF Upload Section */}
            <div className="form-section-title" style={{ marginTop: '1.75rem' }}>
              <span className="step-num">2</span>
              <span>Candidate Resume / CV (PDF)</span>
            </div>

            <div
              className={`pdf-dropzone ${isDragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
              onClick={() => document.getElementById('react-resume-file').click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input
                type="file"
                id="react-resume-file"
                accept=".pdf,.docx,.doc,.txt"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />

              {!file ? (
                <div className="dropzone-empty-view">
                  <div className="dropzone-icon-circle">
                    <UploadCloud size={32} />
                  </div>
                  <div className="dropzone-title">Upload Candidate Resume / CV</div>
                  <p className="dropzone-sub">
                    Drag and drop your candidate's <strong>PDF</strong> file here, or <span className="browse-link">browse from computer</span>
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
                    <button
                      type="button"
                      className="btn-remove-file"
                      onClick={handleRemoveFile}
                      title="Remove and select another file"
                    >
                      <Trash2 size={16} />
                      <span>Change File</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="submit-action-wrap">
              <button type="submit" className="btn-cta" disabled={loading}>
                {loading ? (
                  <>
                    <span>Verifying Candidate Skills...</span>
                    <div className="spinner"></div>
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
