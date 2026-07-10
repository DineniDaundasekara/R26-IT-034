const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const Candidate = require('../models/Candidate');
const AIServiceClient = require('../services/aiServiceClient');

// Configure Multer storage
const uploadDir = path.join(__dirname, '../../uploads');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadDir),
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9);
    cb(null, uniqueSuffix + '-' + file.originalname);
  }
});

const upload = multer({ storage });

// Assess a candidate
router.post('/assess', upload.single('resume_file'), async (req, res) => {
  let uploadedFilePath = null;
  try {
    const { candidate_name, email, github_username, linkedin_url, apify_token, target_role_id, resume_text } = req.body;
    
    if (req.file) {
      uploadedFilePath = req.file.path;
    }

    // Proxy assessment to Python AI Verification Microservice
    const aiResult = await AIServiceClient.verifyCandidate({
      candidateName: candidate_name,
      email: email,
      githubUsername: github_username,
      linkedinUrl: linkedin_url,
      apifyToken: apify_token,
      targetRoleId: target_role_id,
      resumeText: resume_text,
      filePath: uploadedFilePath,
      originalFilename: req.file ? req.file.originalname : undefined
    });


    // Clean up uploaded temp file
    if (uploadedFilePath && fs.existsSync(uploadedFilePath)) {
      try { fs.unlinkSync(uploadedFilePath); } catch (e) {}
    }

    // Save or update in MongoDB
    let candidateDoc;
    try {
      const liData = aiResult.linkedinProfile || aiResult.linkedinData || (aiResult.assessment && aiResult.assessment.linkedinData) || null;
      candidateDoc = new Candidate({
        assessmentId: aiResult.assessmentId,
        candidateName: aiResult.candidateName,
        email: aiResult.email,
        githubUsername: aiResult.githubUsername,
        linkedinUrl: linkedin_url || aiResult.linkedinUrl || null,
        linkedinProfile: liData,
        targetRole: aiResult.targetRole,
        targetRoleId: aiResult.targetRoleId,
        assessment: {
          ...(aiResult.assessment || aiResult),
          repositoryEngineeringEvidence: aiResult.repositoryEngineeringEvidence || (aiResult.assessment && aiResult.assessment.repositoryEngineeringEvidence),
          linkedinData: liData
        },
        hrDecision: null,
        createdAt: new Date()
      });

      await candidateDoc.save();
    } catch (dbErr) {
      console.warn('[MongoDB] Save failed, returning in-memory record:', dbErr.message);
    }

    return res.status(200).json(candidateDoc ? candidateDoc.toObject() : aiResult);

  } catch (err) {
    if (uploadedFilePath && fs.existsSync(uploadedFilePath)) {
      try { fs.unlinkSync(uploadedFilePath); } catch (e) {}
    }
    console.error('Candidate assessment error:', err.message);
    return res.status(500).json({ error: 'Assessment failed', message: err.message });
  }
});

// Get all candidates
router.get('/', async (req, res) => {
  try {
    if (require('mongoose').connection.readyState === 1) {
      const candidates = await Candidate.find().sort({ createdAt: -1 });
      return res.status(200).json(candidates);
    }
    return res.status(200).json([]);
  } catch (err) {
    console.warn('[MongoDB] Candidates list fallback to empty array:', err.message);
    return res.status(200).json([]);
  }
});


// Get single candidate detail
router.get('/:id', async (req, res) => {
  try {
    const candidate = await Candidate.findOne({ assessmentId: req.params.id });
    if (!candidate) {
      return res.status(404).json({ error: 'Candidate not found' });
    }
    return res.status(200).json(candidate);
  } catch (err) {
    return res.status(500).json({ error: 'Failed to fetch candidate', message: err.message });
  }
});

// Record recruiter HITL decision
router.post('/:id/decision', async (req, res) => {
  try {
    const { decision, notes, reviewerName } = req.body;
    const candidate = await Candidate.findOne({ assessmentId: req.params.id });
    if (!candidate) {
      return res.status(404).json({ error: 'Candidate not found' });
    }

    candidate.hrDecision = {
      decision: decision,
      notes: notes || '',
      reviewerName: reviewerName || 'Hiring Manager',
      decidedAt: new Date()
    };

    await candidate.save();
    return res.status(200).json({ status: 'SUCCESS', record: candidate });
  } catch (err) {
    return res.status(500).json({ error: 'Failed to record decision', message: err.message });
  }
});

// Delete candidate record
router.delete('/:id', async (req, res) => {
  try {
    const assessmentId = req.params.id;
    if (require('mongoose').connection.readyState === 1) {
      await Candidate.deleteOne({ $or: [{ assessmentId: assessmentId }, { _id: assessmentId }] });
    }

    // Also proxy delete to Python microservice
    try {
      const axios = require('axios');
      await axios.delete(`${process.env.AI_SERVICE_URL || 'http://127.0.0.1:8000'}/api/candidates/${assessmentId}`);
    } catch (proxyErr) {
      console.warn('[AI Service Client] Python delete proxy failed or record already deleted:', proxyErr.message);
    }

    return res.status(200).json({ status: 'SUCCESS', message: 'Candidate deleted successfully.' });
  } catch (err) {
    return res.status(500).json({ error: 'Failed to delete candidate', message: err.message });
  }
});

module.exports = router;
