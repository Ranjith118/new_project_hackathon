import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const decisionSupportApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Decision Support API
export const decisionSupportAPI = {
  // Criticality
  getAllCriticality: () => decisionSupportApi.get('/api/decision-support/criticality'),
  getCriticalitySummary: () => decisionSupportApi.get('/api/decision-support/criticality/summary'),
  getCriticalEquipment: () => decisionSupportApi.get('/api/decision-support/criticality/critical'),
  
  // Risk
  getAllRisks: () => decisionSupportApi.get('/api/decision-support/risk'),
  getRiskSummary: () => decisionSupportApi.get('/api/decision-support/risk/summary'),
  getCriticalRisks: () => decisionSupportApi.get('/api/decision-support/risk/critical'),
  
  // Priorities
  getAllPriorities: () => decisionSupportApi.get('/api/decision-support/priorities'),
  getPrioritySummary: () => decisionSupportApi.get('/api/decision-support/priorities/summary'),
  
  // Bottlenecks
  getAllBottlenecks: () => decisionSupportApi.get('/api/decision-support/bottlenecks'),
  getBottleneckSummary: () => decisionSupportApi.get('/api/decision-support/bottlenecks/summary'),
  getCriticalBottlenecks: () => decisionSupportApi.get('/api/decision-support/bottlenecks/critical'),
  
  // Schedule
  generateSchedule: (params) => decisionSupportApi.post('/api/decision-support/schedule', null, { params }),
  getLatestSchedule: () => decisionSupportApi.get('/api/decision-support/schedule/latest'),
  
  // Summary
  generateSummary: (data) => decisionSupportApi.post('/api/decision-support/summary', data),
  
  // Dashboard
  getPlantHealth: () => decisionSupportApi.get('/api/decision-support/plant-health'),
  getEquipmentRanking: (limit) => decisionSupportApi.get('/api/decision-support/equipment-ranking', { params: { limit } }),
};

// Convenience functions
export const getAllCriticality = async () => {
  const response = await decisionSupportAPI.getAllCriticality();
  return response.data;
};

export const getCriticalitySummary = async () => {
  const response = await decisionSupportAPI.getCriticalitySummary();
  return response.data;
};

export const getAllRisks = async () => {
  const response = await decisionSupportAPI.getAllRisks();
  return response.data;
};

export const getRiskSummary = async () => {
  const response = await decisionSupportAPI.getRiskSummary();
  return response.data;
};

export const getAllPriorities = async () => {
  const response = await decisionSupportAPI.getAllPriorities();
  return response.data;
};

export const getPrioritySummary = async () => {
  const response = await decisionSupportAPI.getPrioritySummary();
  return response.data;
};

export const getAllBottlenecks = async () => {
  const response = await decisionSupportAPI.getAllBottlenecks();
  return response.data;
};

export const getBottleneckSummary = async () => {
  const response = await decisionSupportAPI.getBottleneckSummary();
  return response.data;
};

export const generateSchedule = async (maxDowntime, technicians) => {
  const response = await decisionSupportAPI.generateSchedule({
    max_daily_downtime: maxDowntime,
    available_technicians: technicians
  });
  return response.data;
};

export const getLatestSchedule = async () => {
  const response = await decisionSupportAPI.getLatestSchedule();
  return response.data;
};

export const generateSummary = async (plantName, includeDetailed) => {
  const response = await decisionSupportAPI.generateSummary({
    plant_name: plantName,
    include_detailed: includeDetailed
  });
  return response.data;
};

export const getPlantHealthDashboard = async () => {
  const response = await decisionSupportAPI.getPlantHealth();
  return response.data;
};

export const getEquipmentRanking = async (limit = 20) => {
  const response = await decisionSupportAPI.getEquipmentRanking(limit);
  return response.data;
};

export default decisionSupportApi;