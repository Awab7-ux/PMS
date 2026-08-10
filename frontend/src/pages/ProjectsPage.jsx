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

  const load = () => {
    if (!orgId) return;
    projectApi.list({ organization_id: orgId, search, per_page: 50 })
      .then(r => setProjects(r.data || []))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [orgId, search]);

  const handleCreate = async (e) => {
    e.preventDefault();
    await projectApi.create({ ...form, organization_id: orgId });
    setShowModal(false);
    setForm({ name: '', description: '', status: 'Planning', priority: 'Medium' });
    load();
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
        <div><h1>Projects</h1><p>Manage your projects</p></div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ New Project</button>
      </div>

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
                  <td>{p.progress_percent}%</td>
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
                <button type="submit" className="btn btn-primary">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
