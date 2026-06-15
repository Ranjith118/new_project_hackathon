import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const predictionApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Prediction API
export const predictionAPI = {
  predictFailure: (data) => predictionApi.post('/api/prediction/failure', data),
  predictRUL: (data) => predictionApi.post('/api/prediction/rul', data),
  getDegradation: (equipmentName) => predictionApi.get(`/api/prediction/degradation/${equipmentName}`),
  assessRisk: (equipmentName) => predictionApi.get(`/api/prediction/risk/${equipmentName}`),
  getWarnings: (params) => predictionApi.get('/api/prediction/warnings', { params }),
  getRecommendations: (equipmentName) => predictionApi.get(`/api/prediction/recommendations/${equipmentName}`),
  getEquipmentPredictions: () => predictionApi.get('/api/prediction/equipment-predictions'),
  getDashboard: () => predictionApi.get('/api/prediction/dashboard'),
  trainFailureModel: () => predictionApi.post('/api/prediction/train-failure'),
  trainRULModel: () => predictionApi.post('/api/prediction/train-rul'),
  getModelMetrics: () => predictionApi.get('/api/prediction/model-metrics'),
};

// Convenience functions
export const predictFailure = async (data) => {
  const response = await predictionAPI.predictFailure(data);
  return response.data;
};

export const predictRUL = async (data) => {
  const response = await predictionAPI.predictRUL(data);
  return response.data;
};

export const getDegradation = async (equipmentName) => {
  const response = await predictionAPI.getDegradation(equipmentName);
  return response.data;
};

export const assessRisk = async (equipmentName) => {
  const response = await predictionAPI.assessRisk(equipmentName);
  return response.data;
};

export const getWarnings = async (params = {}) => {
  const response = await predictionAPI.getWarnings(params);
  return response.data;
};

export const getRecommendations = async (equipmentName) => {
  const response = await predictionAPI.getRecommendations(equipmentName);
  return response.data;
};

export const getEquipmentPredictions = async () => {
  const response = await predictionAPI.getEquipmentPredictions();
  return response.data;
};

export const getPredictiveDashboard = async () => {
  const response = await predictionAPI.getDashboard();
  return response.data;
};

export const trainFailureModel = async () => {
  const response = await predictionAPI.trainFailureModel();
  return response.data;
};

export const trainRULModel = async () => {
  const response = await predictionAPI.trainRULModel();
  return response.data;
};

export const getModelMetrics = async () => {
  const response = await predictionAPI.getModelMetrics();
  return response.data;
};

export default predictionApi;