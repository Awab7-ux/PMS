import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi, userApi, setTokens, clearTokens, getTokens } from '../services/api';

const AuthContext = createContext(null);

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
      const orgs = await import('../services/api').then(m => m.orgApi.list());
      if (orgs.data?.length) {
        setOrganization(orgs.data[0]);
        localStorage.setItem('org_id', orgs.data[0].id);
      }
    } catch {
      clearTokens();
      setUser(null);
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
