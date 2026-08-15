import { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { orgApi } from '../services/api';
import '../styles/invitations.css';

const ROLES = ['Project Manager', 'Team Member', 'Client'];
const date = value => value ? new Date(value).toLocaleString() : '—';

export default function InvitationsPage() {
  const { orgId, user } = useAuth();
  const [invitations, setInvitations] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState({ email: '', role: 'Team Member' });
  const [saving, setSaving] = useState(false);
  const [handoff, setHandoff] = useState('');

  const load = async () => {
    if (!orgId) return;
    setLoading(true); setError('');
    try {
      const [invitationResult, memberResult] = await Promise.all([orgApi.invitations(orgId), orgApi.members(orgId)]);
      setInvitations(invitationResult.data || []); setMembers(memberResult.data || []);
    } catch (err) { setError(err.message || 'Unable to load invitations.'); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, [orgId]);
  const canManage = useMemo(() => ['Organization Owner', 'Project Manager'].includes(members.find(m => m.user_id === user?.id)?.role), [members, user]);
  const pendingEmails = new Set(invitations.filter(i => i.status === 'pending').map(i => i.email.toLowerCase()));

  const create = async e => {
    e.preventDefault(); setError(''); setNotice('');
    if (!/^\S+@\S+\.\S+$/.test(form.email)) { setError('Enter a valid recipient email.'); return; }
    if (pendingEmails.has(form.email.trim().toLowerCase())) { setError('There is already a pending invitation for this email.'); return; }
    setSaving(true);
    try {
      const result = await orgApi.invite(orgId, { email: form.email.trim(), role: form.role });
      const token = result.data?.token;
      setHandoff(token ? `${window.location.origin}/invitations/accept/${token}` : '');
      setModal(false); setForm({ email: '', role: 'Team Member' }); setNotice('Invitation created.'); await load();
    } catch (err) { setError(err.message || 'Unable to create invitation.'); }
    finally { setSaving(false); }
  };
  const cancel = async invitation => {
    if (!window.confirm(`Cancel the invitation for ${invitation.email}?`)) return;
    try { await orgApi.cancelInvitation(invitation.id); setNotice('Invitation cancelled.'); await load(); }
    catch (err) { setError(err.message || 'Unable to cancel invitation.'); }
  };
  const copyHandoff = async () => { try { await navigator.clipboard.writeText(handoff); setNotice('Development invitation link copied.'); } catch { setError('Unable to copy the invitation link.'); } };

  if (loading) return <div className="invitation-skeleton" aria-label="Loading invitations"><div className="skeleton skeleton-line" /><div className="skeleton skeleton-card" /><div className="skeleton skeleton-card" /></div>;
  if (!canManage) return <div className="card empty-state"><h2>Invitation management is restricted</h2><p>Only organization owners and project managers can manage invitations.</p></div>;
  return <div className="invitations-page">
    <div className="page-header"><div><h1>Invitations</h1><p>Invite people to join {orgId ? 'your organization' : 'the organization'}.</p></div><button className="btn btn-primary" onClick={() => { setHandoff(''); setModal(true); }}>+ Invite member</button></div>
    {error && <div className="alert alert-error" role="alert">{error} <button className="btn btn-secondary btn-sm" onClick={load}>Retry</button></div>}
    {notice && <div className="alert alert-success" role="status">{notice}</div>}
    {handoff && <div className="card invitation-handoff"><strong>Development/testing handoff</strong><p>Email delivery is not configured. Copy this one-time invitation link now; it is not shown again in the list.</p><div><code>{handoff}</code><button className="btn btn-secondary btn-sm" onClick={copyHandoff}>Copy link</button></div></div>}
    {invitations.length === 0 ? <div className="card empty-state"><h2>No invitations yet</h2><p>Create an invitation to add someone to this organization.</p></div> : <div className="card table-wrap"><table><thead><tr><th>Recipient</th><th>Role</th><th>Invited by</th><th>Created</th><th>Expires</th><th>Status</th><th /></tr></thead><tbody>{invitations.map(invitation => <tr key={invitation.id}><td>{invitation.email}</td><td>{invitation.role}</td><td>{invitation.inviter_name || '—'}</td><td>{date(invitation.created_at)}</td><td>{date(invitation.expires_at)}</td><td><span className={`badge invitation-status-${invitation.status}`}>{invitation.status}</span></td><td>{invitation.status === 'pending' && <button className="btn btn-danger btn-sm" onClick={() => cancel(invitation)} aria-label={`Cancel invitation for ${invitation.email}`}>Cancel</button>}</td></tr>)}</tbody></table></div>}
    {modal && <div className="modal-overlay" role="presentation" onClick={() => setModal(false)}><div className="modal" role="dialog" aria-modal="true" aria-labelledby="invite-title" onClick={e => e.stopPropagation()}><h2 id="invite-title">Invite organization member</h2><form onSubmit={create}><div className="form-group"><label className="label" htmlFor="invite-email">Recipient email</label><input id="invite-email" className="input" type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required autoFocus /></div><div className="form-group"><label className="label" htmlFor="invite-role">Organization role</label><select id="invite-role" className="select" value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>{ROLES.map(role => <option key={role}>{role}</option>)}</select></div><div className="invitation-actions"><button type="button" className="btn btn-secondary" onClick={() => setModal(false)}>Cancel</button><button className="btn btn-primary" disabled={saving}>{saving ? 'Sending…' : 'Create invitation'}</button></div></form></div></div>}
  </div>;
}
