import { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { orgApi } from '../services/api';
import { PageHeader, Card, Modal, LoadingState, EmptyState, Alert, Badge, Input, Select, FormGroup, FormSection } from '../components';
import '../styles/invitations.css';

const ROLES = ['Project Manager', 'Team Member', 'Client'];
const formatDate = value => value ? new Date(value).toLocaleString() : '—';

export default function InvitationsPage() {
  const { orgId, user } = useAuth();
  const [invitations, setInvitations] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState({ email: '', role: 'Team Member' });
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
    e.preventDefault();
    setError('');
    setNotice('');
    if (!/^\S+@\S+\.\S+$/.test(form.email)) {
      setError('Enter a valid recipient email.');
      return;
    }
    if (pendingEmails.has(form.email.trim().toLowerCase())) {
      setError('There is already a pending invitation for this email.');
      return;
    }
    try {
      const result = await orgApi.invite(orgId, { email: form.email.trim(), role: form.role });
      const token = result.data?.token;
      setHandoff(token ? `${window.location.origin}/invitations/accept/${token}` : '');
      setModal(false);
      setForm({ email: '', role: 'Team Member' });
      setNotice('Invitation created.');
      await load();
    } catch (err) {
      setError(err.message || 'Unable to create invitation.');
    }
  };
  const cancel = async invitation => {
    if (!window.confirm(`Cancel the invitation for ${invitation.email}?`)) return;
    try {
      await orgApi.cancelInvitation(invitation.id);
      setNotice('Invitation cancelled.');
      await load();
    } catch (err) {
      setError(err.message || 'Unable to cancel invitation.');
    }
  };

  const copyHandoff = async () => {
    try {
      await navigator.clipboard.writeText(handoff);
      setNotice('Development invitation link copied.');
    } catch {
      setError('Unable to copy the invitation link.');
    }
  };

  if (loading) return <LoadingState message="Loading invitations..." />;
  if (!canManage) {
    return (
      <EmptyState
        icon="bi-lock"
        title="Invitation management is restricted"
        message="Only organization owners and project managers can manage invitations."
      />
    );
  }
  return (
    <div className="invitations-page">
      <PageHeader
        title="Invitations"
        description={`Invite people to join ${orgId ? 'your organization' : 'the organization'}.`}
        icon="📧"
        action={
          <button
            className="btn btn-primary"
            onClick={() => {
              setHandoff('');
              setModal(true);
            }}
          >
            + Invite member
          </button>
        }
      />

      {error && (
        <Alert
          type="error"
          title="Error"
          message={error}
          onClose={() => setError('')}
          action={{ label: 'Retry', onClick: load }}
        />
      )}

      {notice && (
        <Alert type="success" title="Success" message={notice} onClose={() => setNotice('')} />
      )}

      {handoff && (
        <Card style={{ padding: 16, marginBottom: 16 }}>
          <h3 style={{ marginTop: 0 }}>Development/testing handoff</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Email delivery is not configured. Copy this one-time invitation link now; it is not shown again in the list.
          </p>
          <div
            style={{
              display: 'flex',
              gap: 12,
              alignItems: 'center',
              padding: 12,
              background: 'var(--bg-secondary)',
              borderRadius: '8px',
              marginTop: 12
            }}
          >
            <code style={{ flex: 1, fontFamily: 'monospace', fontSize: '0.85rem', wordBreak: 'break-all' }}>
              {handoff}
            </code>
            <button
              className="btn btn-secondary btn-sm"
              onClick={copyHandoff}
              style={{ whiteSpace: 'nowrap' }}
            >
              Copy link
            </button>
          </div>
        </Card>
      )}

      {invitations.length === 0 ? (
        <EmptyState
          icon="📧"
          title="No invitations yet"
          message="Create an invitation to add someone to this organization."
          action={
            <button
              className="btn btn-primary"
              onClick={() => {
                setHandoff('');
                setModal(true);
              }}
            >
              Send Invitation
            </button>
          }
        />
      ) : (
        <Card>
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Recipient</th>
                  <th>Role</th>
                  <th>Invited by</th>
                  <th>Created</th>
                  <th>Expires</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {invitations.map(invitation => (
                  <tr key={invitation.id}>
                    <td>{invitation.email}</td>
                    <td>
                      <Badge variant="secondary">{invitation.role}</Badge>
                    </td>
                    <td>{invitation.inviter_name || '—'}</td>
                    <td>{formatDate(invitation.created_at)}</td>
                    <td>{formatDate(invitation.expires_at)}</td>
                    <td>
                      <Badge
                        variant={
                          invitation.status === 'accepted'
                            ? 'success'
                            : invitation.status === 'expired'
                              ? 'danger'
                              : 'info'
                        }
                      >
                        {invitation.status}
                      </Badge>
                    </td>
                    <td>
                      {invitation.status === 'pending' && (
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => cancel(invitation)}
                          aria-label={`Cancel invitation for ${invitation.email}`}
                        >
                          Cancel
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <Modal
        isOpen={modal}
        onClose={() => setModal(false)}
        title="Invite organization member"
        size="md"
      >
        <form onSubmit={create}>
          <FormSection>
            <FormGroup label="Recipient email" required>
              <Input
                type="email"
                value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })}
                placeholder="Enter email address"
                required
                autoFocus
              />
            </FormGroup>

            <FormGroup label="Organization role" required>
              <Select
                value={form.role}
                onChange={e => setForm({ ...form, role: e.target.value })}
                options={ROLES.map(role => ({ value: role, label: role }))}
              />
            </FormGroup>
          </FormSection>

          <div
            style={{
              display: 'flex',
              gap: 8,
              justifyContent: 'flex-end',
              marginTop: 24
            }}
          >
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setModal(false)}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Create invitation
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
