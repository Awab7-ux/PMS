import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { orgApi } from '../services/api';

export default function AcceptInvitationPage() {
  const { token } = useParams(); const { reload } = useAuth(); const navigate = useNavigate();
  const [error, setError] = useState(''); const [saving, setSaving] = useState(false);
  const accept = async () => { setSaving(true); setError(''); try { await orgApi.acceptInvitation(token); await reload(); navigate('/dashboard', { replace: true }); } catch (err) { setError(err.message || 'This invitation cannot be accepted.'); } finally { setSaving(false); } };
  return <main className="auth-page"><section className="card auth-card"><h1>Join organization</h1><p className="subtitle">Accept this invitation to join the organization. Your signed-in email must match the invitation recipient.</p>{error && <div className="alert alert-error" role="alert">{error}</div>}<button className="btn btn-primary" onClick={accept} disabled={saving}>{saving ? 'Accepting…' : 'Accept invitation'}</button></section></main>;
}
