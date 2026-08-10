import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { projectApi, taskApi } from '../services/api';

export default function ProjectDetailPage() {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      projectApi.get(id),
      taskApi.list({ project_id: id, per_page: 20 }),
    ]).then(([pRes, tRes]) => {
      setProject(pRes.data);
      setTasks(tRes.data || []);
    }).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="loader">Loading...</div>;
  if (!project) return <div className="empty-state">Project not found</div>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>{project.name}</h1>
          <p>{project.description || 'No description'}</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Link to={`/projects/${id}/kanban`} className="btn btn-primary">Kanban Board</Link>
          <Link to="/projects" className="btn btn-secondary">Back</Link>
        </div>
      </div>

      <div className="grid-4" style={{ marginBottom: 24 }}>
        <div className="card stat-card"><div className="value">{project.status}</div><div className="label">Status</div></div>
        <div className="card stat-card"><div className="value">{project.priority}</div><div className="label">Priority</div></div>
        <div className="card stat-card"><div className="value">{project.progress_percent}%</div><div className="label">Progress</div></div>
        <div className="card stat-card"><div className="value">{tasks.length}</div><div className="label">Tasks</div></div>
      </div>

      <div className="card">
        <h3 style={{ marginBottom: 16 }}>Tasks</h3>
        {tasks.length === 0 ? (
          <div className="empty-state">No tasks yet</div>
        ) : (
          <table>
            <thead><tr><th>Title</th><th>Status</th><th>Priority</th><th>Due</th></tr></thead>
            <tbody>
              {tasks.map(t => (
                <tr key={t.id}>
                  <td><Link to={`/tasks/${t.id}`}>{t.title}</Link></td>
                  <td><span className={`badge badge-${t.status?.toLowerCase()}`}>{t.status}</span></td>
                  <td><span className={`badge badge-${t.priority?.toLowerCase()}`}>{t.priority}</span></td>
                  <td>{t.due_date || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
