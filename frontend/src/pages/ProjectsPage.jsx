import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { projectApi } from '../services/api';
import { joinRoom, leaveRoom, onRealtime } from '../services/realtime';
import { 
  PageHeader, Card, Modal, ConfirmDialog, LoadingState, EmptyState, Alert, Badge,
  Input, Select, Textarea, FormGroup, FormSection
} from '../components';

export default function ProjectsPage() {
  const { orgId } = useAuth();
  const [projects, setProjects] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', status: 'Planning', priority: 'Medium' });
  const [error, setError] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const load = () => {
    if (!orgId) { setLoading(false); return; }
    setLoading(true);
    projectApi.list({ organization_id: orgId, search, per_page: 50 })
      .then(r => setProjects(r.data || []))
      .catch(err => setError(err.message || 'Unable to load projects.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [orgId, search]);
  useEffect(() => {
    if (!orgId) return undefined;
    joinRoom('organization', orgId);
    const updateProject = project => { if (String(project.organization_id) !== String(orgId)) return; setProjects(current => current.some(item => item.id === project.id) ? current.map(item => item.id === project.id ? { ...item, ...project } : item) : current); };
    const refreshProject = task => { if (String(task.organization_id) !== String(orgId)) return; setProjects(current => { if (!current.some(project => String(project.id) === String(task.project_id))) return current; projectApi.get(task.project_id).then(response => setProjects(rows => rows.map(project => String(project.id) === String(task.project_id) ? response.data : project))).catch(() => {}); return current; }); };
    const removeProject = payload => { if (String(payload.organization_id) === String(orgId)) setProjects(current => current.filter(project => String(project.id) !== String(payload.project_id))); };
    const off = [onRealtime('project.created', updateProject), onRealtime('project.updated', updateProject), onRealtime('project.deleted', removeProject), ...['task.created', 'task.updated', 'task.status_changed', 'task.deleted'].map(event => onRealtime(event, refreshProject))];
    return () => { leaveRoom('organization', orgId); off.forEach(stop => stop()); };
  }, [orgId]);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await projectApi.create({ ...form, organization_id: orgId });
      setShowModal(false);
      setForm({ name: '', description: '', status: 'Planning', priority: 'Medium' });
      load();
    } catch (err) {
      setError(err.message || 'Unable to create project.');
    }
  };

  const handleDelete = async (id) => {
    try {
      await projectApi.delete(id);
      setDeleteConfirm(null);
      load();
    } catch (err) {
      setError(err.message || 'Unable to delete project.');
    }
  };

  if (loading) return <LoadingState message="Loading projects..." />;

  return (
    <div>
      <PageHeader 
        title="Projects"
        description="Plan, track, and deliver work with confidence."
        icon="📁"
        action={
          <button 
            className="btn btn-primary"
            onClick={() => setShowModal(true)}
          >
            + New Project
          </button>
        }
      />

      {error && (
        <Alert 
          type="error" 
          title="Error"
          message={error}
          onClose={() => setError('')}
        />
      )}

      <div style={{ marginBottom: 16 }}>
        <Input 
          placeholder="Search projects..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          type="search"
        />
      </div>

      {projects.length === 0 ? (
        <EmptyState 
          icon="📁"
          title="No projects yet"
          message="Create your first project to get started."
          action={
            <button 
              className="btn btn-primary"
              onClick={() => setShowModal(true)}
            >
              Create First Project
            </button>
          }
        />
      ) : (
        <Card>
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Code</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>Progress</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {projects.map(p => (
                  <tr key={p.id}>
                    <td>
                      <Link to={`/projects/${p.id}`} className="btn-link">
                        {p.name}
                      </Link>
                    </td>
                    <td>{p.code || '—'}</td>
                    <td>
                      <Badge variant="secondary">{p.status}</Badge>
                    </td>
                    <td>
                      <Badge variant={
                        p.priority === 'Critical' ? 'danger' :
                        p.priority === 'High' ? 'warning' :
                        p.priority === 'Medium' ? 'info' :
                        'secondary'
                      }>
                        {p.priority}
                      </Badge>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div className="progress" style={{ flex: 1, minWidth: 88 }}>
                          <div style={{ 
                            width: `${p.progress_percent || 0}%`,
                            height: '4px',
                            borderRadius: '2px',
                            background: 'var(--primary)'
                          }} />
                        </div>
                        <span style={{ minWidth: 40 }}>{p.progress_percent || 0}%</span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <Link 
                          to={`/projects/${p.id}/kanban`}
                          className="btn btn-secondary btn-sm"
                        >
                          View
                        </Link>
                        <button 
                          className="btn btn-danger btn-sm"
                          onClick={() => setDeleteConfirm(p.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <Modal 
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Create New Project"
        size="lg"
      >
        <form onSubmit={handleCreate}>
          <FormSection>
            <FormGroup label="Project Name" required>
              <Input 
                value={form.name}
                onChange={e => setForm({ ...form, name: e.target.value })}
                placeholder="Enter project name"
                required
              />
            </FormGroup>

            <FormGroup label="Description">
              <Textarea 
                value={form.description}
                onChange={e => setForm({ ...form, description: e.target.value })}
                placeholder="Describe your project..."
                rows={4}
              />
            </FormGroup>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <FormGroup label="Status" required>
                <Select 
                  value={form.status}
                  onChange={e => setForm({ ...form, status: e.target.value })}
                  options={[
                    { value: 'Planning', label: 'Planning' },
                    { value: 'Active', label: 'Active' },
                    { value: 'On Hold', label: 'On Hold' },
                    { value: 'Completed', label: 'Completed' },
                    { value: 'Archived', label: 'Archived' }
                  ]}
                />
              </FormGroup>

              <FormGroup label="Priority" required>
                <Select 
                  value={form.priority}
                  onChange={e => setForm({ ...form, priority: e.target.value })}
                  options={[
                    { value: 'Low', label: 'Low' },
                    { value: 'Medium', label: 'Medium' },
                    { value: 'High', label: 'High' },
                    { value: 'Critical', label: 'Critical' }
                  ]}
                />
              </FormGroup>
            </div>
          </FormSection>

          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 24 }}>
            <button 
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowModal(false)}
            >
              Cancel
            </button>
            <button 
              type="submit"
              className="btn btn-primary"
            >
              Create Project
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={deleteConfirm !== null}
        title="Delete Project?"
        message="This project and all associated data will be permanently deleted. This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        isDangerous
        onConfirm={() => {
          if (deleteConfirm) handleDelete(deleteConfirm);
        }}
        onCancel={() => setDeleteConfirm(null)}
      />
    </div>
  );
}
