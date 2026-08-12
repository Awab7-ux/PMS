import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi, userApi, orgApi, setTokens, clearTokens, getTokens } from '../services/api';

const AuthContext = createContext(null);

function normalizeOrgList(data) {
  return Array.isArray(data) ? data : [];
}

function defaultOrgSlug(username) {
  const slug = (username || 'workspace').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  return slug || 'workspace';
}

async function ensureOrganization(user) {
  const orgs = await orgApi.list();
  const orgList = normalizeOrgList(orgs.data);
  if (orgList.length) {
    return orgList[0];
  }
  const slug = defaultOrgSlug(user.username);
  try {
    const created = await orgApi.create({ name: `${user.full_name}'s Workspace`, slug });
    return created.data;
  } catch {
    const created = await orgApi.create({
      name: `${user.full_name}'s Workspace`,
      slug: `${slug}-${Date.now().toString(36)}`,
    });
    return created.data;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [organization, setOrganization] = useState(null);

  const loadUser = useCallback(async () => {
    const { access } = getTokens();
    if (!access) {
      setLoading(false);
      return;
    }
    try {
      const res = await userApi.me();
      setUser(res.data);
      const org = await ensureOrganization(res.data);
      setOrganization(org);
      localStorage.setItem('org_id', org.id);
    } catch {
      clearTokens();
      setUser(null);
      setOrganization(null);
      localStorage.removeItem('org_id');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadUser(); }, [loadUser]);

  const login = async (email, password) => {
    const res = await authApi.login({ email, password });
    setTokens(res.data.access_token, res.data.refresh_token);
    await loadUser();
    return res;
  };

  const register = async (data) => {
    const res = await authApi.register(data);
    return res;
  };

  const logout = async () => {
    try { await authApi.logout(); } catch { /* ignore */ }
    clearTokens();
    setUser(null);
    setOrganization(null);
    localStorage.removeItem('org_id');
  };

  const orgId = organization?.id || localStorage.getItem('org_id');

  return (
    <AuthContext.Provider value={{ user, loading, organization, orgId, setOrganization, login, register, logout, reload: loadUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
