import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { teamApi, userApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function TeamDetailPage() {
  const { id } = useParams();
  const { orgId } = useAuth();
  const [team, setTeam] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState('');
  const [error, setError] = useState('');

  const load = () => {
    Promise.all([
      teamApi.get(id),
      orgId ? userApi.list({ organization_id: orgId, per_page: 100 }) : Promise.resolve({ data: [] }),
    ]).then(([tRes, uRes]) => {
      setTeam(tRes.data);
      setUsers(uRes.data || []);
    }).catch(err => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [id, orgId]);

  const handleAddMember = async (e) => {
    e.preventDefault();
    if (!userId) return;
    setError('');
    try {
      await teamApi.addMember(id, { user_id: userId });
      setUserId('');
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRemove = async (memberId) => {
    if (!confirm('Remove this member?')) return;
    await teamApi.removeMember(id, memberId);
    load();
  };

  if (loading) return <div className="loader">Loading...</div>;
  if (!team) return <div className="empty-state">Team not found</div>;

  const members = team.members || [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>{team.name}</h1>
          <p>{team.description || 'No description'}</p>
        </div>
        <Link to="/teams" className="btn btn-secondary">Back</Link>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <h3 style={{ marginBottom: 16 }}>Members ({members.length})</h3>
        {members.length === 0 ? (
          <div className="empty-state">No members yet</div>
        ) : (
          <table>
            <thead><tr><th>Name</th><th>Email</th><th>Role</th><th></th></tr></thead>
            <tbody>
              {members.map(m => (
                <tr key={m.user_id || m.id}>
                  <td>{m.full_name || m.user?.full_name}</td>
                  <td>{m.email || m.user?.email}</td>
                  <td>{m.role || 'Member'}</td>
                  <td>
                    <button className="btn btn-danger btn-sm" onClick={() => handleRemove(m.user_id || m.id)}>Remove</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <form onSubmit={handleAddMember} style={{ marginTop: 24, display: 'flex', gap: 8, alignItems: 'flex-end' }}>
          <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
            <label className="label">Add member</label>
            <select className="select" value={userId} onChange={e => setUserId(e.target.value)}>
              <option value="">Select user...</option>
              {users.filter(u => !members.some(m => (m.user_id || m.id) === u.id)).map(u => (
                <option key={u.id} value={u.id}>{u.full_name} ({u.email})</option>
              ))}
            </select>
          </div>
          <button className="btn btn-primary">Add</button>
        </form>
      </div>
    </div>
  );
}
