import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { projectApi, taskApi } from '../services/api';

export default function TasksPage() {
  const { orgId } = useAuth();
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!orgId) return;
    projectApi.list({ organization_id: orgId, per_page: 100 }).then(r => {
      const list = r.data || [];
      setProjects(list);
      if (list.length) setProjectId(list[0].id);
    });
  }, [orgId]);

  useEffect(() => {
    if (!projectId) { setLoading(false); return; }
    setLoading(true);
    taskApi.list({ project_id: projectId, per_page: 50 })
      .then(r => setTasks(r.data || []))
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <div className="loader">Loading tasks...</div>;

  return (
    <div>
      <div className="page-header">
        <div><h1>Tasks</h1><p>All tasks across projects</p></div>
      </div>

      <div style={{ marginBottom: 16 }}>
        <select className="select" value={projectId} onChange={e => setProjectId(e.target.value)} style={{ maxWidth: 300 }}>
          {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>

      <div className="card table-wrap">
        {tasks.length === 0 ? (
          <div className="empty-state">No tasks in this project</div>
        ) : (
          <table>
            <thead><tr><th>Title</th><th>Status</th><th>Priority</th><th>Due Date</th><th>Progress</th></tr></thead>
            <tbody>
              {tasks.map(t => (
                <tr key={t.id}>
                  <td><Link to={`/tasks/${t.id}`}>{t.title}</Link></td>
                  <td><span className={`badge badge-${t.status?.toLowerCase()}`}>{t.status}</span></td>
                  <td><span className={`badge badge-${t.priority?.toLowerCase()}`}>{t.priority}</span></td>
                  <td>{t.due_date || '—'}</td>
                  <td>{t.progress_percent}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
