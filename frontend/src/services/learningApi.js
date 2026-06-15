import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const learningApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Learning API
export const learningAPI = {
  // Feedback
  addFeedback: (data) => learningApi.post('/api/learning/feedback', data),
  getFeedback: (params) => learningApi.get('/api/learning/feedback', { params }),
  getFeedbackByModule: (module) => learningApi.get(`/api/learning/feedback/module/${module}`),
  getModuleFeedbackSummary: (module) => learningApi.get(`/api/learning/feedback/summary/${module}`),
  
  // Outcomes
  addOutcome: (data) => learningApi.post('/api/learning/outcome', data),
  getOutcomes: (params) => learningApi.get('/api/learning/outcomes', { params }),
  getOutcomeSummary: () => learningApi.get('/api/learning/outcomes/summary'),
  
  // Performance
  getPerformanceDashboard: () => learningApi.get('/api/learning/performance/dashboard'),
  getPerformanceTrends: (params) => learningApi.get('/api/learning/performance/trends', { params }),
  getModelPerformance: () => learningApi.get('/api/learning/performance/models'),
  getRecommendationScores: () => learningApi.get('/api/learning/performance/recommendation-scores'),
  
  // Retraining
  getRetrainingSummary: () => learningApi.get('/api/learning/retraining/summary'),
  getRetrainingJobs: (params) => learningApi.get('/api/learning/retraining/jobs', { params }),
  triggerRetraining: (modelName) => learningApi.post('/api/learning/retraining/trigger', null, { params: { model_name: modelName } }),
  
  // Summary
  getLearningSummary: (params) => learningApi.get('/api/learning/summary', { params }),
  getQuickSummary: () => learningApi.get('/api/learning/summary/quick'),
};

// Convenience functions
export const addFeedback = async (data) => {
  const response = await learningAPI.addFeedback(data);
  return response.data;
};

export const getFeedback = async (module, days) => {
  const response = await learningAPI.getFeedback({ module, days });
  return response.data;
};

export const getOutcomeSummary = async () => {
  const response = await learningAPI.getOutcomeSummary();
  return response.data;
};

export const getPerformanceDashboard = async () => {
  const response = await learningAPI.getPerformanceDashboard();
  return response.data;
};

export const getModelPerformance = async () => {
  const response = await learningAPI.getModelPerformance();
  return response.data;
};

export const getPerformanceTrends = async (days) => {
  const response = await learningAPI.getPerformanceTrends({ days });
  return response.data;
};

export const getRetrainingSummary = async () => {
  const response = await learningAPI.getRetrainingSummary();
  return response.data;
};

export const getRetrainingJobs = async (limit) => {
  const response = await learningAPI.getRetrainingJobs({ limit });
  return response.data;
};

export const getLearningSummary = async (period, days) => {
  const response = await learningAPI.getLearningSummary({ period, days });
  return response.data;
};

export const getQuickSummary = async () => {
  const response = await learningAPI.getQuickSummary();
  return response.data;
};

export default learningApi;