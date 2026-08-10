import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { reportApi, projectApi, taskApi, notificationApi } from '../services/api';

export default function DashboardPage() {
  const { orgId } = useAuth();
  const [stats, setStats] = useState(null);
  const [projects, setProjects] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!orgId) return;
    Promise.all([
      reportApi.analytics(orgId).catch(() => ({ data: {} })),
      projectApi.list({ organization_id: orgId, per_page: 5 }).catch(() => ({ data: [] })),
      notificationApi.list({ per_page: 5 }).catch(() => ({ data: [] })),
    ]).then(([analytics, projRes, notifRes]) => {
      setStats(analytics.data);
      setProjects(projRes.data || []);
      setNotifications(notifRes.data || []);
    }).finally(() => setLoading(false));
  }, [orgId]);

  if (loading) return <div className="loader">Loading dashboard...</div>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p>Overview of your projects and tasks</p>
        </div>
      </div>

      <div className="grid-4" style={{ marginBottom: 24 }}>
        <div className="card stat-card">
          <div className="value">{stats?.total_projects ?? 0}</div>
          <div className="label">Total Projects</div>
        </div>
        <div className="card stat-card">
          <div className="value">{stats?.active_projects ?? 0}</div>
          <div className="label">Active Projects</div>
        </div>
        <div className="card stat-card">
          <div className="value">{stats?.total_tasks ?? 0}</div>
          <div className="label">Total Tasks</div>
        </div>
        <div className="card stat-card">
          <div className="value">{stats?.overdue_tasks ?? 0}</div>
          <div className="label">Overdue Tasks</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3 style={{ marginBottom: 16 }}>Recent Projects</h3>
          {projects.length === 0 ? (
            <div className="empty-state">No projects yet. <Link to="/projects">Create one</Link></div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Name</th><th>Status</th><th>Progress</th></tr></thead>
                <tbody>
                  {projects.map(p => (
                    <tr key={p.id}>
                      <td><Link to={`/projects/${p.id}`}>{p.name}</Link></td>
                      <td><span className={`badge badge-${p.status?.toLowerCase().replace(' ', '_')}`}>{p.status}</span></td>
                      <td>{p.progress_percent}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 16 }}>Recent Notifications</h3>
          {notifications.length === 0 ? (
            <div className="empty-state">No notifications</div>
          ) : (
            notifications.map(n => (
              <div key={n.id} style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <strong>{n.title}</strong>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{n.message}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
