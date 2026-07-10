const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const AI_SERVICE_BASE_URL = process.env.AI_SERVICE_URL || 'http://127.0.0.1:8000';

/**
 * Client service proxying requests to the Python FastAPI verification microservice.
 */
class AIServiceClient {

  static async checkHealth() {
    try {
      const resp = await axios.get(`${AI_SERVICE_BASE_URL}/health`, { timeout: 5000 });
      return resp.data;
    } catch (err) {
      return { status: 'DEGRADED', message: err.message };
    }
  }

  static async getStandardRoles() {
    const resp = await axios.get(`${AI_SERVICE_BASE_URL}/api/roles`, { timeout: 10000 });
    return resp.data;
  }

  static async getAblationMetrics() {
    const resp = await axios.get(`${AI_SERVICE_BASE_URL}/api/experiments/ablation`, { timeout: 10000 });
    return resp.data;
  }

  static async verifyCandidate({ candidateName, email, githubUsername, targetRoleId, resumeText, filePath, originalFilename, linkedinUrl, apifyToken }) {
    const form = new FormData();
    if (candidateName) form.append('candidate_name', candidateName);
    if (email) form.append('email', email);
    if (githubUsername) form.append('github_username', githubUsername);
    if (linkedinUrl) form.append('linkedin_url', linkedinUrl);
    if (apifyToken) form.append('apify_token', apifyToken);
    form.append('target_role_id', targetRoleId || 'full_stack_mern');



    if (filePath && fs.existsSync(filePath)) {
      form.append('resume_file', fs.createReadStream(filePath), { filename: originalFilename || 'resume.pdf' });
    } else if (resumeText) {
      form.append('resume_text', resumeText);
    } else {
      throw new Error('Either resume text or resume file must be provided.');
    }

    const resp = await axios.post(`${AI_SERVICE_BASE_URL}/api/assess/candidate`, form, {
      headers: form.getHeaders(),
      timeout: 60000
    });

    return resp.data;
  }
}

module.exports = AIServiceClient;
