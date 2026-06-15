import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const rcaApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// RCA API
export const rcaAPI = {
  analyze: (data) => rcaApi.post('/api/rca/analyze', data),
  analyzeEquipment: (equipmentName) => rcaApi.post(`/api/rca/analyze-equipment/${equipmentName}`),
  getSimilarCases: (params) => rcaApi.get('/api/rca/similar-cases', { params }),
  getPatterns: () => rcaApi.get('/api/rca/patterns'),
  addPattern: (data) => rcaApi.post('/api/rca/patterns', data),
  getReports: (limit) => rcaApi.get('/api/rca/reports', { params: { limit } }),
  getReport: (reportId) => rcaApi.get(`/api/rca/reports/${reportId}`),
  getReportText: (reportId) => rcaApi.get(`/api/rca/reports/${reportId}/text`),
  getReportHtml: (reportId) => rcaApi.get(`/api/rca/reports/${reportId}/html`),
  getDashboard: () => rcaApi.get('/api/rca/dashboard'),
};

// Convenience functions
export const performRCA = async (data) => {
  const response = await rcaAPI.analyze(data);
  return response.data;
};

export const analyzeEquipment = async (equipmentName) => {
  const response = await rcaAPI.analyzeEquipment(equipmentName);
  return response.data;
};

export const getSimilarCases = async (equipment, issue) => {
  const response = await rcaAPI.getSimilarCases({ equipment, issue });
  return response.data;
};

export const getFailurePatterns = async () => {
  const response = await rcaAPI.getPatterns();
  return response.data;
};

export const getRCAReports = async (limit = 20) => {
  const response = await rcaAPI.getReports(limit);
  return response.data;
};

export const getRCAReport = async (reportId) => {
  const response = await rcaAPI.getReport(reportId);
  return response.data;
};

export const getRCAReportText = async (reportId) => {
  const response = await rcaAPI.getReportText(reportId);
  return response.data;
};

export const getRCAReportHtml = async (reportId) => {
  const response = await rcaAPI.getReportHtml(reportId);
  return response.data;
};

export const getRCADashboard = async () => {
  const response = await rcaAPI.getDashboard();
  return response.data;
};

export default rcaApi;