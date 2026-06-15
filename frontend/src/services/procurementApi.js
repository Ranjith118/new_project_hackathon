import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const procurementApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Procurement API
export const procurementAPI = {
  // Spare Parts
  getAllSpares: (params) => procurementApi.get('/api/procurement/spares', { params }),
  getSpare: (partId) => procurementApi.get(`/api/procurement/spares/${partId}`),
  createSpare: (data) => procurementApi.post('/api/procurement/spares', data),
  updateSpare: (partId, data) => procurementApi.put(`/api/procurement/spares/${partId}`, data),
  deleteSpare: (partId) => procurementApi.delete(`/api/procurement/spares/${partId}`),
  
  // Inventory
  getInventoryStatus: () => procurementApi.get('/api/procurement/inventory-status'),
  getInventorySummary: () => procurementApi.get('/api/procurement/inventory-summary'),
  getAlerts: () => procurementApi.get('/api/procurement/alerts'),
  getCriticalAlerts: () => procurementApi.get('/api/procurement/alerts/critical'),
  
  // Reorder
  getReorderRecommendations: () => procurementApi.get('/api/procurement/reorder'),
  getReorderSummary: () => procurementApi.get('/api/procurement/reorder-summary'),
  
  // Suppliers
  getSuppliers: () => procurementApi.get('/api/procurement/suppliers'),
  getSupplier: (supplierId) => procurementApi.get(`/api/procurement/suppliers/${supplierId}`),
  getSupplierPerformance: (supplierId) => procurementApi.get(`/api/procurement/suppliers/${supplierId}/performance`),
  
  // Mappings
  getPartMappings: (data) => procurementApi.post('/api/procurement/mappings', data),
  
  // Procurement Plan
  generateProcurementPlan: (data) => procurementApi.post('/api/procurement/plan', data),
  getProcurementRisks: (params) => procurementApi.get('/api/procurement/risks', { params }),
  
  // Dashboard
  getDashboard: () => procurementApi.get('/api/procurement/dashboard'),
};

// Convenience functions
export const getAllSpares = async (category, equipmentType) => {
  const response = await procurementAPI.getAllSpares({ category, equipment_type: equipmentType });
  return response.data;
};

export const getSpare = async (partId) => {
  const response = await procurementAPI.getSpare(partId);
  return response.data;
};

export const createSpare = async (data) => {
  const response = await procurementAPI.createSpare(data);
  return response.data;
};

export const updateSpare = async (partId, data) => {
  const response = await procurementAPI.updateSpare(partId, data);
  return response.data;
};

export const getInventorySummary = async () => {
  const response = await procurementAPI.getInventorySummary();
  return response.data;
};

export const getInventoryAlerts = async () => {
  const response = await procurementAPI.getAlerts();
  return response.data;
};

export const getReorderRecommendations = async () => {
  const response = await procurementAPI.getReorderRecommendations();
  return response.data;
};

export const getSuppliers = async () => {
  const response = await procurementAPI.getSuppliers();
  return response.data;
};

export const getProcurementDashboard = async () => {
  const response = await procurementAPI.getDashboard();
  return response.data;
};

export const generateProcurementPlan = async (data) => {
  const response = await procurementAPI.generateProcurementPlan(data);
  return response.data;
};

export const getPartMappings = async (equipmentType, rootCause, failureProbability) => {
  const response = await procurementAPI.getPartMappings({
    equipment_type: equipmentType,
    root_cause: rootCause,
    failure_probability: failureProbability
  });
  return response.data;
};

export default procurementApi;