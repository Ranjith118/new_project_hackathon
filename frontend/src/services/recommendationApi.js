import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const recommendationApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Recommendation API
export const recommendationAPI = {
  getRecommendations: (data) => recommendationApi.post('/api/recommendation', data),
  getRepairGuide: (equipmentName, repairType) => recommendationApi.get(`/api/recommendation/repair-guide/${equipmentName}`, { params: { repair_type: repairType } }),
  getRepairTypes: () => recommendationApi.get('/api/recommendation/repair-types'),
  getMaintenanceSchedule: (data) => recommendationApi.post('/api/recommendation/schedule', data),
  getSpareParts: (params) => recommendationApi.post('/api/recommendation/spares', null, { params }),
  getCompletePlan: (data) => recommendationApi.post('/api/recommendation/complete-plan', data),
  getDashboard: () => recommendationApi.get('/api/recommendation/dashboard'),
  getHistory: (limit) => recommendationApi.get('/api/recommendation/history', { params: { limit } }),
};

// Convenience functions
export const getRecommendations = async (data) => {
  const response = await recommendationAPI.getRecommendations(data);
  return response.data;
};

export const getRepairGuide = async (equipmentName, repairType = 'bearing_replacement') => {
  const response = await recommendationAPI.getRepairGuide(equipmentName, repairType);
  return response.data;
};

export const getRepairTypes = async () => {
  const response = await recommendationAPI.getRepairTypes();
  return response.data;
};

export const getMaintenanceSchedule = async (data) => {
  const response = await recommendationAPI.getMaintenanceSchedule(data);
  return response.data;
};

export const getSpareParts = async (equipment, equipmentType, rootCause, failureProbability) => {
  const response = await recommendationAPI.getSpareParts({
    equipment,
    equipment_type: equipmentType,
    root_cause: rootCause,
    failure_probability: failureProbability
  });
  return response.data;
};

export const getCompletePlan = async (data) => {
  const response = await recommendationAPI.getCompletePlan(data);
  return response.data;
};

export const getRecommendationDashboard = async () => {
  const response = await recommendationAPI.getDashboard();
  return response.data;
};

export const getRecommendationHistory = async (limit = 20) => {
  const response = await recommendationAPI.getHistory(limit);
  return response.data;
};

export default recommendationApi;