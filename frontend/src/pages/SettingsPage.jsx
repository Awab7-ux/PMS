import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { userApi, orgApi } from '../services/api';

export default function SettingsPage() {
  const { user, organization, reload, setOrganization } = useAuth();
  const [profile, setProfile] = useState({
    full_name: user?.full_name || '',
    username: user?.username || '',
    avatar_url: user?.avatar_url || '',
  });
  const [passwords, setPasswords] = useState({ current_password: '', new_password: '' });
  const [orgForm, setOrgForm] = useState({ name: organization?.name || '' });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [tab, setTab] = useState('profile');

  const handleProfile = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      await userApi.updateMe(profile);
      setMessage('Profile updated successfully');
      reload();
    } catch (err) {
      setError(err.message);
    }
  };

  const handlePassword = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      await userApi.changePassword(passwords);
      setMessage('Password changed successfully');
      setPasswords({ current_password: '', new_password: '' });
    } catch (err) {
      setError(err.message);
    }
  };

  const handleOrg = async (e) => {
    e.preventDefault();
    if (!organization?.id) return;
    setError('');
    setMessage('');
    try {
      const res = await orgApi.get(organization.id);
      setOrganization(res.data);
      setMessage('Organization settings saved');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div><h1>Settings</h1><p>Manage your account and preferences</p></div>
      </div>

      {message && <div className="alert alert-success">{message}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
        {['profile', 'password', 'organization'].map(t => (
          <button key={t} className={`btn ${tab === t ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTab(t)}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === 'profile' && (
        <div className="card" style={{ maxWidth: 520 }}>
          <h3 style={{ marginBottom: 16 }}>Profile</h3>
          <form onSubmit={handleProfile}>
            <div className="form-group">
              <label className="label">Full Name</label>
              <input className="input" value={profile.full_name} onChange={e => setProfile({ ...profile, full_name: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="label">Username</label>
              <input className="input" value={profile.username} onChange={e => setProfile({ ...profile, username: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="label">Avatar URL</label>
              <input className="input" value={profile.avatar_url} onChange={e => setProfile({ ...profile, avatar_url: e.target.value })} />
            </div>
            <button className="btn btn-primary">Save Profile</button>
          </form>
        </div>
      )}

      {tab === 'password' && (
        <div className="card" style={{ maxWidth: 520 }}>
          <h3 style={{ marginBottom: 16 }}>Change Password</h3>
          <form onSubmit={handlePassword}>
            <div className="form-group">
              <label className="label">Current Password</label>
              <input className="input" type="password" value={passwords.current_password} onChange={e => setPasswords({ ...passwords, current_password: e.target.value })} required />
            </div>
            <div className="form-group">
              <label className="label">New Password</label>
              <input className="input" type="password" value={passwords.new_password} onChange={e => setPasswords({ ...passwords, new_password: e.target.value })} required minLength={12} />
            </div>
            <button className="btn btn-primary">Update Password</button>
          </form>
        </div>
      )}

      {tab === 'organization' && organization && (
        <div className="card" style={{ maxWidth: 520 }}>
          <h3 style={{ marginBottom: 16 }}>Organization</h3>
          <form onSubmit={handleOrg}>
            <div className="form-group">
              <label className="label">Organization Name</label>
              <input className="input" value={orgForm.name} onChange={e => setOrgForm({ name: e.target.value })} />
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: 16 }}>
              Slug: {organization.slug} · ID: {organization.id}
            </p>
            <button className="btn btn-primary">Save</button>
          </form>
        </div>
      )}
    </div>
  );
}
