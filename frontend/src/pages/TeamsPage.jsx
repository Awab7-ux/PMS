import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { teamApi } from '../services/api';

export default function TeamsPage() {
  const { orgId } = useAuth();
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ name: '', description: '' });
  const [error, setError] = useState('');

  const load = () => {
    teamApi.list()
      .then(r => setTeams(r.data || []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await teamApi.create({ ...form, organization_id: orgId });
      setShowModal(false);
      setForm({ name: '', description: '' });
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Archive this team?')) return;
    await teamApi.delete(id);
    load();
  };

  if (loading) return <div className="loader">Loading teams...</div>;

  return (
    <div>
      <div className="page-header">
        <div><h1>Teams</h1><p>Manage your organization teams</p></div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ New Team</button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {teams.length === 0 ? (
        <div className="card empty-state">No teams yet. Create your first team.</div>
      ) : (
        <div className="grid-3">
          {teams.map(t => (
            <div key={t.id} className="card">
              <h3><Link to={`/teams/${t.id}`}>{t.name}</Link></h3>
              <p style={{ color: 'var(--text-muted)', margin: '8px 0 16px' }}>{t.description || 'No description'}</p>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="badge badge-medium">{t.member_count ?? 0} members</span>
                <button className="btn btn-danger btn-sm" onClick={() => handleDelete(t.id)}>Archive</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Create Team</h2>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label className="label">Name</label>
                <input className="input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
              </div>
              <div className="form-group">
                <label className="label">Description</label>
                <textarea className="textarea" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
              </div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
