import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Equipment API
export const equipmentAPI = {
  getAll: (params = {}) => api.get('/api/equipment', { params }),
  getById: (id) => api.get(`/api/equipment/${id}`),
  create: (data) => api.post('/api/equipment', data),
  update: (id, data) => api.put(`/api/equipment/${id}`, data),
  delete: (id) => api.delete(`/api/equipment/${id}`),
};

// Maintenance Logs API
export const maintenanceLogsAPI = {
  getAll: (params = {}) => api.get('/api/maintenance-logs', { params }),
  getById: (id) => api.get(`/api/maintenance-logs/${id}`),
  create: (data) => api.post('/api/maintenance-logs', data),
  update: (id, data) => api.put(`/api/maintenance-logs/${id}`, data),
  delete: (id) => api.delete(`/api/maintenance-logs/${id}`),
};

// Sensor Data API
export const sensorDataAPI = {
  getAll: (params = {}) => api.get('/api/sensor-data', { params }),
  getById: (id) => api.get(`/api/sensor-data/${id}`),
  create: (data) => api.post('/api/sensor-data', data),
  bulkCreate: (data) => api.post('/api/sensor-data/bulk', data),
  delete: (id) => api.delete(`/api/sensor-data/${id}`),
};

// Failure Reports API
export const failureReportsAPI = {
  getAll: (params = {}) => api.get('/api/failure-reports', { params }),
  getById: (id) => api.get(`/api/failure-reports/${id}`),
  create: (data) => api.post('/api/failure-reports', data),
  update: (id, data) => api.put(`/api/failure-reports/${id}`, data),
  delete: (id) => api.delete(`/api/failure-reports/${id}`),
};

// Spare Parts API
export const sparePartsAPI = {
  getAll: (params = {}) => api.get('/api/spare-parts', { params }),
  getById: (id) => api.get(`/api/spare-parts/${id}`),
  create: (data) => api.post('/api/spare-parts', data),
  update: (id, data) => api.put(`/api/spare-parts/${id}`, data),
  delete: (id) => api.delete(`/api/spare-parts/${id}`),
};

// Upload API
export const uploadAPI = {
  uploadManual: (formData) => api.post('/api/upload/manual', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  uploadSOP: (formData) => api.post('/api/upload/sop', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  uploadMaintenanceLog: (formData) => api.post('/api/upload/maintenance-log', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  uploadFailureReport: (formData) => api.post('/api/upload/failure-report', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  uploadSensorData: (formData) => api.post('/api/upload/sensor-data', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  uploadSpares: (formData) => api.post('/api/upload/spares', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getFiles: (params = {}) => api.get('/api/upload/files', { params }),
  downloadFile: (id) => `${API_BASE_URL}/api/upload/${id}/download`,
  deleteFile: (id) => api.delete(`/api/upload/${id}`),
};

// Dashboard API
export const dashboardAPI = {
  getStats: () => api.get('/api/dashboard/stats'),
  getRecentUploads: () => api.get('/api/dashboard/recent-uploads'),
  getEquipmentStatus: () => api.get('/api/dashboard/equipment-status'),
  getFullDashboard: () => api.get('/api/dashboard'),
};

export default api;