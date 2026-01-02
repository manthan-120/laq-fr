/**
 * API service layer for communicating with FastAPI backend
 */

import axios from 'axios';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Upload API
export const uploadPDF = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/api/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

// Search API
export const searchLAQs = async (query, topK = 5, threshold = 0.6) => {
  const response = await api.post('/api/search/', {
    query,
    top_k: topK,
    threshold,
  });

  return response.data;
};

// Chat API
export const chatWithLAQs = async (question, topK = 5) => {
  const response = await api.post('/api/chat/', {
    question,
    top_k: topK,
  });

  return response.data;
};

// Database API
export const getDatabaseInfo = async () => {
  const response = await api.get('/api/database/info');
  return response.data;
};

export const clearDatabase = async () => {
  const response = await api.delete('/api/database/clear');
  return response.data;
};

// ✅ NEW: Fetch all LAQs for Dashboard
export const getAllLAQs = async () => {
  const response = await api.get('/api/dashboard/laqs');
  return response.data;
};

// Health Check
export const healthCheck = async () => {
  const response = await api.get('/api/health');
  return response.data;
};

// Submit manual LAQ entry with files
export const submitManualLAQ = async (payload, filesMap) => {
  const formData = new FormData();
  formData.append('payload', JSON.stringify(payload));

  // filesMap may be an array of File objects or an object of filename->File
  if (filesMap) {
    const values = Array.isArray(filesMap) ? filesMap : Object.values(filesMap)
    // Deduplicate files by filename to avoid uploading same annexure multiple times
    const uniqueByName = {}
    values.forEach((f) => {
      if (!f) return
      // Only consider actual File/Blob objects
      if (f instanceof File || (typeof Blob !== 'undefined' && f instanceof Blob)) {
        const name = f.name || `file_${Object.keys(uniqueByName).length}`
        if (!uniqueByName[name]) uniqueByName[name] = f
      }
    })

    // Append each unique file once. Use a consistent form field name (e.g. 'file')
    // and include the original filename as the third parameter so backend UploadFile.filename matches payload
    Object.entries(uniqueByName).forEach(([name, file]) => {
      formData.append('file', file, name)
    })
  }

  // Use native fetch to avoid axios instance default headers interfering
  const url = API_BASE_URL + '/api/manual-entry/'
  const resp = await fetch(url, {
    method: 'POST',
    body: formData,
    credentials: 'include',
  })

  if (!resp.ok) {
    const text = await resp.text()
    throw new Error(`Server responded ${resp.status}: ${text}`)
  }

  return resp.json()
};

export default api;