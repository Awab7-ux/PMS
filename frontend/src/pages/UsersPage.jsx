import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { orgApi } from '../services/api';
import { PageHeader, Card, LoadingState, EmptyState, Alert, Badge, Select } from '../components';

export default function UsersPage() {
  const { orgId, user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [pendingInvitations, setPendingInvitations] = useState(0);

  const load = () => {
    if (!orgId) return;
    setLoading(true);
    Promise.all([orgApi.members(orgId), orgApi.invitations(orgId).catch(() => ({ data: [] }))])
      .then(([r, invitations]) => { setUsers(r.data || []); setPendingInvitations((invitations.data || []).filter(item => item.status === 'pending').length); })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, [orgId]);

  const myMembership = users.find(m => m.user_id === currentUser?.id);
  const canManage = ['Organization Owner', 'Project Manager'].includes(myMembership?.role);
  const changeRole = async (member, role) => {
    try { await orgApi.updateMember(orgId, member.user_id, { role }); load(); } catch (err) { setError(err.message); }
  };
  const remove = async (member) => {
    if (!window.confirm(`Remove ${member.user?.full_name || 'this member'} from the organization?`)) return;
    try { await orgApi.removeMember(orgId, member.user_id); load(); } catch (err) { setError(err.message); }
  };

  if (loading) return <LoadingState message="Loading users..." />;

  return (
    <div>
      <PageHeader
        title="Organization members"
        description="People with access to this workspace."
        icon="👥"
      />

      {error && <Alert type="error" title="Error" message={error} onClose={() => setError('')} />}

      {canManage && pendingInvitations > 0 && (
        <Card style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, padding: 16 }}>
          <div>
            <h3 style={{ margin: 0 }}>Pending invitations</h3>
            <p style={{ color: 'var(--text-muted)', marginBottom: 0, fontSize: '0.9rem' }}>
              {pendingInvitations} awaiting a response
            </p>
          </div>
          <Link className="btn btn-secondary" to="/invitations">
            Manage invitations
          </Link>
        </Card>
      )}

      {users.length === 0 ? (
        <EmptyState
          icon="👥"
          title="No members yet"
          message="This organization has no members."
        />
      ) : (
        <Card>
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Joined</th>
                  {canManage && <th>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id}>
                    <td>
                      {u.user?.full_name}
                      {u.user_id === currentUser?.id && (
                        <Badge variant="info" style={{ marginLeft: 8 }}>you</Badge>
                      )}
                    </td>
                    <td>{u.user?.email}</td>
                    <td>
                      {canManage && !u.is_owner ? (
                        <Select
                          value={u.role || ''}
                          onChange={e => changeRole(u, e.target.value)}
                          options={[
                            { value: 'Project Manager', label: 'Project Manager' },
                            { value: 'Team Member', label: 'Team Member' },
                            { value: 'Client', label: 'Client' }
                          ]}
                          style={{ minWidth: 140 }}
                        />
                      ) : (
                        <Badge variant="secondary">{u.role}</Badge>
                      )}
                    </td>
                    <td>{u.joined_at ? new Date(u.joined_at).toLocaleDateString() : '—'}</td>
                    {canManage && (
                      <td>
                        {!u.is_owner && (
                          <button
                            className="btn btn-danger btn-sm"
                            onClick={() => remove(u)}
                          >
                            Remove
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
