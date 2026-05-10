const mongoose = require('mongoose');

const CandidateSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, required: true },
  github_username: { type: String, required: true },
  trust_score: { type: Number },
  risk_category: { type: String },
  extracted_features: { type: Object },
  explanations: [{ type: String }],
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Candidate', CandidateSchema);
