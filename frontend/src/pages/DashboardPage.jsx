import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { reportApi, projectApi, notificationApi } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6'];

export default function DashboardPage() {
  const { orgId } = useAuth();
  const [stats, setStats] = useState(null);
  const [projects, setProjects] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!orgId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all([
      reportApi.analytics(orgId).catch(() => ({ data: {} })),
      projectApi.list({ organization_id: orgId, per_page: 5 }).catch(() => ({ data: [] })),
      notificationApi.list({ per_page: 5 }).catch(() => ({ data: [] })),
    ]).then(([analytics, projRes, notifRes]) => {
      setStats(analytics.data);
      setProjects(Array.isArray(projRes.data) ? projRes.data : []);
      setNotifications(Array.isArray(notifRes.data) ? notifRes.data : []);
    }).finally(() => setLoading(false));
  }, [orgId]);

  if (loading) return <div className="loader">Loading dashboard...</div>;

  if (!orgId) {
    return (
      <div>
        <div className="page-header">
          <div>
            <h1>Dashboard</h1>
            <p>No organization is available for your account yet.</p>
          </div>
        </div>
        <div className="card empty-state">Please sign out and sign in again, or contact your administrator.</div>
      </div>
    );
  }

  const statusData = Object.entries(stats?.tasks_by_status || {}).map(([name, value]) => ({
    name: name.replace('_', ' '),
    value,
  }));
  const priorityData = Object.entries(stats?.tasks_by_priority || {}).map(([name, value]) => ({
    name,
    value,
  }));

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

      <div className="grid-2" style={{ marginBottom: 24 }}>
        <div className="card">
          <h3 style={{ marginBottom: 16 }}>Tasks by Status</h3>
          {statusData.length === 0 ? (
            <div className="empty-state">No task data</div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={statusData}>
                <XAxis dataKey="name" stroke="#9aa0b4" fontSize={11} />
                <YAxis stroke="#9aa0b4" fontSize={11} />
                <Tooltip contentStyle={{ background: '#1a1d27', border: '1px solid #2d3142' }} />
                <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
        <div className="card">
          <h3 style={{ marginBottom: 16 }}>Tasks by Priority</h3>
          {priorityData.length === 0 ? (
            <div className="empty-state">No task data</div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={priorityData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label>
                  {priorityData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#1a1d27', border: '1px solid #2d3142' }} />
              </PieChart>
            </ResponsiveContainer>
          )}
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
