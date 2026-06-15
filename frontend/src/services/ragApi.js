import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const ragApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Chat API
export const chatAPI = {
  sendMessage: (data) => ragApi.post('/api/rag/chat', data),
  getHistory: (conversationId) => ragApi.get(`/api/rag/chat/history/${conversationId}`),
  clearHistory: (conversationId) => ragApi.delete(`/api/rag/chat/history/${conversationId}`),
  getSuggestedQuestions: () => ragApi.get('/api/rag/suggested-questions'),
};

// Document API
export const documentAPI = {
  upload: (formData) => ragApi.post('/api/rag/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  process: (data) => ragApi.post('/api/rag/documents/process', data, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  }),
  search: (params) => ragApi.get('/api/rag/documents', { params }),
  delete: (documentName) => ragApi.delete(`/api/rag/documents/${documentName}`),
};

// Index API
export const indexAPI = {
  getStats: () => ragApi.get('/api/rag/index/stats'),
  reindex: (data) => ragApi.post('/api/rag/index/reindex', data),
  importMaintenanceLogs: (limit = 100) => ragApi.post(`/api/rag/index/import-maintenance-logs?limit=${limit}`),
  importFailureReports: (limit = 100) => ragApi.post(`/api/rag/index/import-failure-reports?limit=${limit}`),
};

// Chat API endpoints
export const sendMessage = async (question, conversationId = null, documentType = 'all', maxResults = 5) => {
  const response = await chatAPI.sendMessage({
    question,
    conversation_id: conversationId,
    document_type_filter: documentType,
    max_results: maxResults,
  });
  return response.data;
};

export const getChatHistory = async (conversationId) => {
  const response = await chatAPI.getHistory(conversationId);
  return response.data;
};

export const clearChatHistory = async (conversationId) => {
  const response = await chatAPI.clearHistory(conversationId);
  return response.data;
};

export const getSuggestedQuestions = async () => {
  const response = await chatAPI.getSuggestedQuestions();
  return response.data;
};

// Document operations
export const uploadDocument = async (file, documentName, documentType, description = '', tags = []) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_name', documentName);
  formData.append('document_type', documentType);
  formData.append('description', description);
  formData.append('tags', tags.join(','));
  
  const response = await documentAPI.upload(formData);
  return response.data;
};

export const processDocument = async (filePath, documentName, documentType, chunkSize = 500, chunkOverlap = 50) => {
  const response = await ragApi.post('/api/rag/documents/process', null, {
    params: {
      file_path: filePath,
      document_name: documentName,
      document_type: documentType,
      chunk_size: chunkSize,
      chunk_overlap: chunkOverlap,
    },
  });
  return response.data;
};

export const searchDocuments = async (query, documentType = 'all', maxResults = 10) => {
  const response = await documentAPI.search({
    query,
    document_type: documentType,
    max_results: maxResults,
  });
  return response.data;
};

export const deleteDocumentIndex = async (documentName) => {
  const response = await documentAPI.delete(documentName);
  return response.data;
};

export const getIndexStats = async () => {
  const response = await indexAPI.getStats();
  return response.data;
};

export const reindexDocuments = async (documentId = null, chunkSize = 500, chunkOverlap = 50) => {
  const response = await indexAPI.reindex({
    document_id: documentId,
    chunk_size: chunkSize,
    chunk_overlap: chunkOverlap,
  });
  return response.data;
};

export const importMaintenanceLogs = async (limit = 100) => {
  const response = await indexAPI.importMaintenanceLogs(limit);
  return response.data;
};

export const importFailureReports = async (limit = 100) => {
  const response = await indexAPI.importFailureReports(limit);
  return response.data;
};

export default ragApi;