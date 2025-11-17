import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const createProject = async (projectData) => {
  const response = await api.post('/api/projects', projectData);
  return response.data;
};

export const getProjectSummary = async (projectId) => {
  const response = await api.get(`/api/projects/${projectId}/summary`);
  return response.data;
};

export const generateSummary = async (projectId, teamsWebhook = null) => {
  const response = await api.post(
    `/api/projects/${projectId}/generate-summary`,
    null,
    { params: { teams_webhook: teamsWebhook } }
  );
  return response.data;
};

export const listProjects = async () => {
  const response = await api.get('/api/projects');
  return response.data;
};

export default api;

