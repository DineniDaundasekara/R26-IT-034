const mongoose = require('mongoose');

const CandidateSchema = new mongoose.Schema({
  assessmentId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  candidateName: {
    type: String,
    required: true
  },
  email: {
    type: String
  },
  githubUsername: {
    type: String
  },
  linkedinUrl: {
    type: String,
    default: null
  },
  linkedinProfile: {
    profilePicUrl: { type: String, default: null },
    currentRole: {
      title: { type: String, default: null },
      company: { type: String, default: null },
      location: { type: String, default: null },
      isCurrent: { type: Boolean, default: false }
    },
    certifications: [{
      name: { type: String },
      authority: { type: String },
      url: { type: String },
      year: { type: Number }
    }]
  },
  targetRole: {
    type: String,
    required: true
  },
  targetRoleId: {
    type: String,
    default: 'full_stack_mern'
  },

  assessment: {
    finalVerdict: {
      status: { type: String },
      verdictType: { type: String },
      matchScore: { type: Number },
      summaryComment: { type: String },
      matchedSkills: [{ type: String }],
      skillsToImprove: [{ type: String }]
    },
    verificationCounts: { type: mongoose.Schema.Types.Mixed },
    skillVerifications: [{ type: mongoose.Schema.Types.Mixed }],
    projectVerifications: [{ type: mongoose.Schema.Types.Mixed }],
    repositoryEngineeringEvidence: { type: mongoose.Schema.Types.Mixed },
    overallAssessment: { type: mongoose.Schema.Types.Mixed },
    hrDecisionSupport: [{ type: mongoose.Schema.Types.Mixed }]
  },

  hrDecision: {
    decision: { type: String },
    notes: { type: String },
    reviewerName: { type: String },
    decidedAt: { type: Date }
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
}, { strict: false });

module.exports = mongoose.model('Candidate', CandidateSchema);

