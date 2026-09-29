import React, { useState } from 'react';
import { CheckCircle, XCircle, AlertCircle, FileCheck2, UserCheck, MessageSquare, Send } from 'lucide-react';
import { recordDecision } from '../api';

export default function DecisionSupport({ candidateRecord, onDecisionRecorded }) {
  if (!candidateRecord) return null;

  const [notes, setNotes] = useState('');
  const [reviewerName, setReviewerName] = useState('Hiring Manager');
  const [submitting, setSubmitting] = useState(false);
  const [savedDecision, setSavedDecision] = useState(candidateRecord.hrDecision);

  const handleDecision = async (decisionType) => {
    setSubmitting(true);
    try {
      const resp = await recordDecision(candidateRecord.assessmentId, {
        decision: decisionType,
        notes: notes,
        reviewerName: reviewerName
      });
      setSavedDecision(resp.record ? resp.record.hrDecision : { decision: decisionType, notes, reviewerName });
      if (onDecisionRecorded) {
        onDecisionRecorded(resp.record || resp);
      }
    } catch (err) {
      console.error('Failed to save recruiter decision:', err);
      alert('Could not record decision: ' + (err.message || 'Error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="decision-support-panel">
      <div className="section-title-row">
        <h3 className="section-title">Recruiter Decision & Interview Action Panel</h3>
        <span className="section-subtitle">Audit logging and candidate disposition</span>
      </div>

      {savedDecision ? (
        <div className="saved-decision-banner">
          <div className="decision-banner-header">
            <UserCheck size={18} className="text-green" />
            <strong className="decision-title">Logged Decision: {savedDecision.decision}</strong>
          </div>
          {savedDecision.notes && (
            <p className="decision-notes-text">"{savedDecision.notes}"</p>
          )}
          <div className="decision-meta-row">
            <span>Reviewer: {savedDecision.reviewerName || 'Hiring Manager'}</span>
            <span>•</span>
            <span>Recorded: {new Date(savedDecision.decidedAt || Date.now()).toLocaleString()}</span>
          </div>
        </div>
      ) : (
        <div className="decision-input-form">
          <div className="decision-actions-row">
            <button
              type="button"
              className="btn-decision-proceed"
              disabled={submitting}
              onClick={() => handleDecision('Proceed to Technical Interview')}
            >
              <CheckCircle size={16} />
              Proceed to Interview
            </button>

            <button
              type="button"
              className="btn-decision-probe"
              disabled={submitting}
              onClick={() => handleDecision('Request Additional Portfolio / Timeline Clarification')}
            >
              <AlertCircle size={16} />
              Request Clarification
            </button>

            <button
              type="button"
              className="btn-decision-reject"
              disabled={submitting}
              onClick={() => handleDecision('Decline Application')}
            >
              <XCircle size={16} />
              Decline Application
            </button>
          </div>

          <div className="decision-notes-group">
            <label className="notes-label">
              <MessageSquare size={14} />
              Reviewer Assessment Notes / Action Item:
            </label>
            <textarea
              className="notes-textarea"
              rows={3}
              placeholder="Enter recruiter feedback or key interview focus areas..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
