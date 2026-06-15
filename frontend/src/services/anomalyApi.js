import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const anomalyApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Prediction API
export const predictionAPI = {
  predict: (data) => anomalyApi.post('/api/anomaly/predict', data),
  predictBulk: (readings) => anomalyApi.post('/api/anomaly/predict-bulk', readings),
};

// Health Score API
export const healthScoreAPI = {
  getDetail: (params) => anomalyApi.get('/api/anomaly/health-score', { params }),
  getStatus: () => anomalyApi.get('/api/anomaly/health-status'),
  getEquipmentHealth: (equipmentName) => anomalyApi.get(`/api/anomaly/equipment-health/${equipmentName}`),
};

// Alert API
export const alertAPI = {
  getAll: (params) => anomalyApi.get('/api/anomaly/alerts', { params }),
  acknowledge: (data) => anomalyApi.post('/api/anomaly/alerts/acknowledge', data),
  resolve: (alertId) => anomalyApi.post(`/api/anomaly/alerts/${alertId}/resolve`),
  getSummary: () => anomalyApi.get('/api/anomaly/alerts/summary'),
};

// Sensor Data API
export const sensorDataAPI = {
  create: (data) => anomalyApi.post('/api/anomaly/sensor-data', data),
  getAll: (params) => anomalyApi.get('/api/anomaly/sensor-data', { params }),
  getLatest: (equipmentName) => anomalyApi.get(`/api/anomaly/sensor-data/latest?equipment_name=${equipmentName}`),
};

// Dashboard API
export const dashboardAPI = {
  getDashboard: () => anomalyApi.get('/api/anomaly/dashboard'),
};

// Model Training API
export const modelAPI = {
  train: () => anomalyApi.post('/api/anomaly/train-model'),
};

// Convenience functions
export const predictAnomaly = async (sensorData) => {
  const response = await predictionAPI.predict(sensorData);
  return response.data;
};

export const getHealthStatus = async () => {
  const response = await healthScoreAPI.getStatus();
  return response.data;
};

export const getEquipmentHealth = async (equipmentName) => {
  const response = await healthScoreAPI.getEquipmentHealth(equipmentName);
  return response.data;
};

export const getAlerts = async (params = {}) => {
  const response = await alertAPI.getAll(params);
  return response.data;
};

export const acknowledgeAlert = async (alertId, acknowledgedBy = 'system') => {
  const response = await alertAPI.acknowledge({ alert_id: alertId, acknowledged_by: acknowledgedBy });
  return response.data;
};

export const resolveAlert = async (alertId) => {
  const response = await alertAPI.resolve(alertId);
  return response.data;
};

export const getAlertSummary = async () => {
  const response = await alertAPI.getSummary();
  return response.data;
};

export const createSensorData = async (data) => {
  const response = await sensorDataAPI.create(data);
  return response.data;
};

export const getSensorData = async (params = {}) => {
  const response = await sensorDataAPI.getAll(params);
  return response.data;
};

export const getDashboard = async () => {
  const response = await dashboardAPI.getDashboard();
  return response.data;
};

export const trainModel = async () => {
  const response = await modelAPI.train();
  return response.data;
};

export default anomalyApi;