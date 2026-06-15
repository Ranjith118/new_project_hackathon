import axios from 'axios';

const API = 'http://localhost:8000/api/doc-intelligence';

export const docIntelligenceApi = {
  // Upload file
  upload: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return axios.post(`${API}/upload`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  // Process (run AI analysis)
  process: (docId) => axios.post(`${API}/process/${docId}`),

  // List documents
  listDocuments: (params) => axios.get(`${API}/documents`, { params }),

  // Get single document with full knowledge
  getDocument: (docId) => axios.get(`${API}/documents/${docId}`),

  // Delete document
  deleteDocument: (docId) => axios.delete(`${API}/documents/${docId}`),

  // Get knowledge for equipment
  getEquipmentKnowledge: (equipmentName) =>
    axios.get(`${API}/knowledge/${encodeURIComponent(equipmentName)}`),

  // Search knowledge base
  search: (query, topK = 5) =>
    axios.get(`${API}/search`, { params: { query, top_k: topK } }),

  // Chat
  chat: (question, conversationId, equipmentFilter) => {
    const fd = new FormData();
    fd.append('question', question);
    if (conversationId) fd.append('conversation_id', conversationId);
    if (equipmentFilter) fd.append('equipment_filter', equipmentFilter);
    return axios.post(`${API}/chat`, fd);
  },

  // Stats
  getStats: () => axios.get(`${API}/stats`),
};
