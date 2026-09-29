/**
 * Frontend API Client Service
 * =======================================
 * Centralized API client communicating with FastAPI AI Microservice (:8000)
 * or Node.js Express Gateway (:5001). Supports VITE_API_URL environment variable.
 */

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '/api';

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

/**
 * Health check
 */
export async function checkHealth() {
  const resp = await apiClient.get('/health');
  return resp.data;
}

/**
 * Fetch available standard and custom job roles
 */
export async function getRoles() {
  const resp = await apiClient.get('/roles');
  return resp.data;
}

/**
 * Create or save custom job role
 */
export async function createCustomRole(roleData) {
  const resp = await apiClient.post('/roles', roleData);
  return resp.data;
}

/**
 * Submit candidate PDF or text for cross-source consistency verification
 */
export async function assessCandidate(formData) {
  const isMultipart = formData instanceof FormData;
  const config = isMultipart
    ? { headers: { 'Content-Type': 'multipart/form-data' } }
    : {};
  const resp = await apiClient.post('/assess/candidate', formData, config);
  return resp.data;
}

/**
 * Fetch list of all assessed candidates
 */
export async function getCandidates() {
  const resp = await apiClient.get('/candidates');
  return resp.data;
}

/**
 * Fetch detailed candidate assessment by ID
 */
export async function getCandidateDetail(assessmentId) {
  const resp = await apiClient.get(`/candidates/${assessmentId}`);
  return resp.data;
}

/**
 * Record recruiter HITL decision
 */
export async function recordDecision(assessmentId, decisionPayload) {
  const resp = await apiClient.post(`/candidates/${assessmentId}/decision`, decisionPayload);
  return resp.data;
}

/**
 * Fetch empirical ablation study benchmark results (Models A, B, C)
 */
export async function getAblationResults() {
  try {
    const resp = await apiClient.get('/experiments/ablation');
    return resp.data;
  } catch (err) {
    const fallbackResp = await apiClient.get('/ablation');
    return fallbackResp.data;
  }
}

export default {
  checkHealth,
  getRoles,
  createCustomRole,
  assessCandidate,
  getCandidates,
  getCandidateDetail,
  recordDecision,
  getAblationResults
};
