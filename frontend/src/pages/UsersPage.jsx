import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { userApi } from '../services/api';

export default function UsersPage() {
  const { orgId, user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!orgId) return;
    setLoading(true);
    userApi.list({ organization_id: orgId, search, per_page: 50 })
      .then(r => setUsers(r.data || []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [orgId, search]);

  if (loading) return <div className="loader">Loading users...</div>;

  return (
    <div>
      <div className="page-header">
        <div><h1>Users</h1><p>Organization members</p></div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div style={{ marginBottom: 16 }}>
        <input className="input" placeholder="Search users..." value={search} onChange={e => setSearch(e.target.value)} style={{ maxWidth: 400 }} />
      </div>

      {users.length === 0 ? (
        <div className="card empty-state">No users found</div>
      ) : (
        <div className="card table-wrap">
          <table>
            <thead><tr><th>Name</th><th>Email</th><th>Username</th><th>Status</th></tr></thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id}>
                  <td>{u.full_name}{u.id === currentUser?.id ? ' (you)' : ''}</td>
                  <td>{u.email}</td>
                  <td>{u.username}</td>
                  <td>
                    <span className={`badge badge-${u.is_active ? 'done' : 'critical'}`}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
