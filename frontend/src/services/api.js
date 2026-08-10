const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

function getTokens() {
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  };
}

function setTokens(access, refresh) {
  if (access) localStorage.setItem('access_token', access);
  if (refresh) localStorage.setItem('refresh_token', refresh);
}

export function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

async function refreshAccessToken() {
  const { refresh } = getTokens();
  if (!refresh) return null;
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${refresh}` },
  });
  if (!res.ok) return null;
  const json = await res.json();
  if (json.success && json.data?.access_token) {
    setTokens(json.data.access_token, refresh);
    return json.data.access_token;
  }
  return null;
}

export async function apiRequest(path, options = {}) {
  const { access } = getTokens();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (access) headers.Authorization = `Bearer ${access}`;

  let res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401 && !options._retry) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers.Authorization = `Bearer ${newToken}`;
      res = await fetch(`${API_BASE}${path}`, { ...options, headers, _retry: true });
    } else {
      clearTokens();
      window.location.href = '/login';
      throw new ApiError('Session expired', 401);
    }
  }

  const json = await res.json().catch(() => ({}));
  if (!res.ok || json.success === false) {
    throw new ApiError(json.message || json.error || 'Request failed', res.status, json);
  }
  return json;
}

export const authApi = {
  register: (data) => apiRequest('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  login: (data) => apiRequest('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  logout: () => apiRequest('/auth/logout', { method: 'POST' }),
  forgotPassword: (email) => apiRequest('/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) }),
  resetPassword: (token, new_password) => apiRequest('/auth/reset-password', { method: 'POST', body: JSON.stringify({ token, new_password }) }),
  verifyEmail: (token) => apiRequest('/auth/verify-email', { method: 'POST', body: JSON.stringify({ token }) }),
};

export const userApi = {
  me: () => apiRequest('/users/me'),
  updateMe: (data) => apiRequest('/users/me', { method: 'PATCH', body: JSON.stringify(data) }),
  changePassword: (data) => apiRequest('/users/me/password', { method: 'PATCH', body: JSON.stringify(data) }),
  list: (params) => apiRequest(`/users?${new URLSearchParams(params)}`),
};

export const orgApi = {
  list: () => apiRequest('/organizations'),
  create: (data) => apiRequest('/organizations', { method: 'POST', body: JSON.stringify(data) }),
  get: (id) => apiRequest(`/organizations/${id}`),
};

export const projectApi = {
  list: (params) => apiRequest(`/projects?${new URLSearchParams(params)}`),
  create: (data) => apiRequest('/projects', { method: 'POST', body: JSON.stringify(data) }),
  get: (id) => apiRequest(`/projects/${id}`),
  update: (id, data) => apiRequest(`/projects/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id) => apiRequest(`/projects/${id}`, { method: 'DELETE' }),
};

export const taskApi = {
  list: (params) => apiRequest(`/tasks?${new URLSearchParams(params)}`),
  create: (data) => apiRequest('/tasks', { method: 'POST', body: JSON.stringify(data) }),
  get: (id) => apiRequest(`/tasks/${id}`),
  update: (id, data) => apiRequest(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id) => apiRequest(`/tasks/${id}`, { method: 'DELETE' }),
  kanban: (projectId) => apiRequest(`/tasks/kanban/${projectId}`),
  move: (id, data) => apiRequest(`/tasks/${id}/move`, { method: 'POST', body: JSON.stringify(data) }),
  reorder: (projectId, items) => apiRequest(`/tasks/kanban/${projectId}/reorder`, { method: 'POST', body: JSON.stringify({ items }) }),
  createSubtask: (taskId, data) => apiRequest(`/tasks/${taskId}/subtasks`, { method: 'POST', body: JSON.stringify(data) }),
  updateSubtask: (taskId, subId, data) => apiRequest(`/tasks/${taskId}/subtasks/${subId}`, { method: 'PATCH', body: JSON.stringify(data) }),
};

export const commentApi = {
  list: (taskId) => apiRequest(`/tasks/${taskId}/comments`),
  create: (taskId, data) => apiRequest(`/tasks/${taskId}/comments`, { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => apiRequest(`/comments/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id) => apiRequest(`/comments/${id}`, { method: 'DELETE' }),
};

export const notificationApi = {
  list: (params) => apiRequest(`/notifications?${new URLSearchParams(params)}`),
  unreadCount: () => apiRequest('/notifications/unread-count'),
  markRead: (id) => apiRequest(`/notifications/${id}/read`, { method: 'POST' }),
  markAllRead: () => apiRequest('/notifications/read-all', { method: 'POST' }),
};

export const teamApi = {
  list: () => apiRequest('/teams'),
  create: (data) => apiRequest('/teams', { method: 'POST', body: JSON.stringify(data) }),
  get: (id) => apiRequest(`/teams/${id}`),
  update: (id, data) => apiRequest(`/teams/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id) => apiRequest(`/teams/${id}`, { method: 'DELETE' }),
  addMember: (teamId, data) => apiRequest(`/teams/${teamId}/members`, { method: 'POST', body: JSON.stringify(data) }),
  removeMember: (teamId, userId) => apiRequest(`/teams/${teamId}/members/${userId}`, { method: 'DELETE' }),
};

export const fileApi = {
  list: (params) => apiRequest(`/files?${new URLSearchParams(params)}`),
  upload: async (file, meta = {}) => {
    const { access } = getTokens();
    const form = new FormData();
    form.append('file', file);
    if (meta.task_id) form.append('task_id', meta.task_id);
    if (meta.project_id) form.append('project_id', meta.project_id);
    const res = await fetch(`${API_BASE}/files/upload`, {
      method: 'POST',
      headers: access ? { Authorization: `Bearer ${access}` } : {},
      body: form,
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok || json.success === false) {
      throw new ApiError(json.message || 'Upload failed', res.status, json);
    }
    return json;
  },
  downloadUrl: (fileId) => `${API_BASE}/files/${fileId}/download`,
  delete: (id) => apiRequest(`/files/${id}`, { method: 'DELETE' }),
};

export const reportApi = {
  analytics: (orgId) => apiRequest(`/reports/analytics?organization_id=${orgId}`),
  activity: (params) => apiRequest(`/activity?${new URLSearchParams(params)}`),
};

export const calendarApi = {
  events: (params) => apiRequest(`/calendar/events?${new URLSearchParams(params)}`),
};

export const searchApi = {
  global: (params) => apiRequest(`/search?${new URLSearchParams(params)}`),
};

export { setTokens, getTokens, ApiError };
