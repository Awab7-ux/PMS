import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { reportApi } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';

const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6', '#a855f7'];

export default function ReportsPage() {
  const { orgId } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!orgId) return;
    reportApi.analytics(orgId)
      .then(r => setStats(r.data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [orgId]);

  if (loading) return <div className="loader">Loading reports...</div>;
  if (error) return <div className="alert alert-error">{error}</div>;

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
        <div><h1>Reports & Analytics</h1><p>Organization performance overview</p></div>
      </div>

      <div className="grid-4" style={{ marginBottom: 24 }}>
        <div className="card stat-card"><div className="value">{stats?.total_projects ?? 0}</div><div className="label">Total Projects</div></div>
        <div className="card stat-card"><div className="value">{stats?.active_projects ?? 0}</div><div className="label">Active</div></div>
        <div className="card stat-card"><div className="value">{stats?.completed_tasks ?? 0}</div><div className="label">Completed Tasks</div></div>
        <div className="card stat-card"><div className="value">{stats?.overdue_tasks ?? 0}</div><div className="label">Overdue</div></div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3 style={{ marginBottom: 16 }}>Tasks by Status</h3>
          {statusData.length === 0 ? (
            <div className="empty-state">No data</div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={statusData}>
                <XAxis dataKey="name" stroke="#9aa0b4" fontSize={12} />
                <YAxis stroke="#9aa0b4" fontSize={12} />
                <Tooltip contentStyle={{ background: '#1a1d27', border: '1px solid #2d3142' }} />
                <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 16 }}>Tasks by Priority</h3>
          {priorityData.length === 0 ? (
            <div className="empty-state">No data</div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={priorityData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
                  {priorityData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#1a1d27', border: '1px solid #2d3142' }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="card" style={{ marginTop: 24 }}>
        <h3 style={{ marginBottom: 8 }}>Average Project Progress</h3>
        <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--primary)' }}>
          {Math.round(stats?.average_project_progress ?? 0)}%
        </div>
      </div>
    </div>
  );
}
