import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { projectApi } from '../services/api';

export default function ProjectsPage() {
  const { orgId } = useAuth();
  const [projects, setProjects] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', status: 'Planning', priority: 'Medium' });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const load = () => {
    if (!orgId) { setLoading(false); return; }
    setLoading(true);
    projectApi.list({ organization_id: orgId, search, per_page: 50 })
      .then(r => setProjects(r.data || []))
      .catch(err => setError(err.message || 'Unable to load projects.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [orgId, search]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true); setError('');
    try {
      await projectApi.create({ ...form, organization_id: orgId });
      setShowModal(false); setForm({ name: '', description: '', status: 'Planning', priority: 'Medium' }); load();
    } catch (err) { setError(err.message || 'Unable to create project.'); } finally { setSaving(false); }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this project?')) return;
    await projectApi.delete(id);
    load();
  };

  if (loading) return <div className="loader">Loading projects...</div>;

  return (
    <div>
      <div className="page-header">
        <div><h1>Projects</h1><p>Plan, track, and deliver work with confidence.</p></div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ New Project</button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div style={{ marginBottom: 16 }}>
        <input className="input" placeholder="Search projects..." value={search} onChange={e => setSearch(e.target.value)} style={{ maxWidth: 400 }} />
      </div>

      {projects.length === 0 ? (
        <div className="card empty-state">No projects found. Create your first project.</div>
      ) : (
        <div className="card table-wrap">
          <table>
            <thead><tr><th>Name</th><th>Code</th><th>Status</th><th>Priority</th><th>Progress</th><th>Actions</th></tr></thead>
            <tbody>
              {projects.map(p => (
                <tr key={p.id}>
                  <td><Link to={`/projects/${p.id}`}>{p.name}</Link></td>
                  <td>{p.code || '—'}</td>
                  <td>{p.status}</td>
                  <td><span className={`badge badge-${p.priority?.toLowerCase()}`}>{p.priority}</span></td>
                  <td><div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><div className="progress" style={{ width: 88 }}><span style={{ width: `${p.progress_percent || 0}%` }} /></div>{p.progress_percent || 0}%</div></td>
                  <td>
                    <Link to={`/projects/${p.id}/kanban`} className="btn btn-secondary btn-sm" style={{ marginRight: 8 }}>Kanban</Link>
                    <button className="btn btn-danger btn-sm" onClick={() => handleDelete(p.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Create Project</h2>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label className="label">Name</label>
                <input className="input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
              </div>
              <div className="form-group">
                <label className="label">Description</label>
                <textarea className="textarea" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="label">Status</label>
                  <select className="select" value={form.status} onChange={e => setForm({ ...form, status: e.target.value })}>
                    {['Planning', 'Active', 'On Hold', 'Completed', 'Archived'].map(s => <option key={s}>{s}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="label">Priority</label>
                  <select className="select" value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })}>
                    {['Low', 'Medium', 'High', 'Critical'].map(s => <option key={s}>{s}</option>)}
                  </select>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Creating…' : 'Create project'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
