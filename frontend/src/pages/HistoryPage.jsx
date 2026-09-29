import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Trash2, ExternalLink } from 'lucide-react';

export default function HistoryPage({ onSelectCandidate }) {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    axios.get('/api/candidates')
      .then(resp => {
        setCandidates(resp.data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load candidates:', err);
        setLoading(false);
      });
  }, []);

  const handleDelete = async (e, candidateId, name) => {
    e.stopPropagation();
    if (!window.confirm(`Are you sure you want to delete the record for ${name || 'this candidate'}?`)) {
      return;
    }

    setDeletingId(candidateId);
    try {
      await axios.delete(`/api/candidates/${candidateId}`);
      setCandidates(prev => prev.filter(c => (c.assessmentId || c._id) !== candidateId));
    } catch (err) {
      console.error('Failed to delete candidate:', err);
      alert('Failed to delete candidate record. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <section className="page-view active">
      <div className="hero-header">
        <h1 className="hero-title">Candidate Assessment History</h1>
        <p className="hero-subtitle">
          Audit log of all verified candidates, evidence summaries, and recorded recruiter decisions.
        </p>
      </div>

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
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem' }}>Loading records...</td></tr>
              ) : candidates.length === 0 ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No candidates assessed yet. Use "Check Candidate" to run your first check.</td></tr>
              ) : (
                candidates.map((c, idx) => {
                  const candidateId = c.assessmentId || c._id;
                  const isDeleting = deletingId === candidateId;

                  return (
                    <tr key={idx}>
                      <td>{new Date(c.createdAt).toLocaleDateString()}</td>
                      <td><strong>{c.candidateName}</strong></td>
                      <td>{c.targetRole}</td>
                      <td><code>{c.githubUsername || 'None'}</code></td>
                      <td>
                        {c.hrDecision ? (
                          <span className="badge-pill" style={{ fontSize: '0.72rem' }}>{c.hrDecision.decision}</span>
                        ) : (
                          <span style={{ color: 'var(--text-light)' }}>Pending</span>
                        )}
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <button
                            className="btn-view-report"
                            onClick={() => onSelectCandidate(c)}
                            title="View full report"
                          >
                            <ExternalLink size={13} />
                            <span>View</span>
                          </button>
                          <button
                            className="btn-delete"
                            disabled={isDeleting}
                            onClick={(e) => handleDelete(e, candidateId, c.candidateName)}
                            title="Delete candidate record"
                          >
                            <Trash2 size={13} />
                            <span>{isDeleting ? '...' : 'Delete'}</span>
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
