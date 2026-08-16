import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useAuth } from '../context/AuthContext';
import { notificationApi, projectApi, reportApi } from '../services/api';
import { joinRoom, leaveRoom, onRealtime } from '../services/realtime';
import { PageHeader, Card, StatCard, Alert, LoadingState, EmptyState, SkeletonLoader } from '../components';
import '../styles/dashboard.css';

const COLORS = ['#2563eb', '#16a34a', '#f59e0b', '#dc2626', '#7c3aed'];
const cleanLabel = value => value?.replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, letter => letter.toUpperCase());

function MetricCard({ label, value, hint, tone = 'blue' }) {
  const toneColorMap = {
    blue: '#4f46e5',
    violet: '#7c3aed',
    green: '#059669',
    red: '#dc2626',
    yellow: '#d97706',
    orange: '#ea580c'
  };

  return <StatCard icon="bi-graph-up" label={label} value={value} hint={hint} tone={tone === 'blue' ? 'blue' : tone === 'green' ? 'green' : tone === 'red' ? 'red' : 'blue'} />;
}

export default function DashboardPage() {
  const { orgId, user } = useAuth();
  const [stats, setStats] = useState(null); const [projects, setProjects] = useState([]); const [notifications, setNotifications] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  const refreshTimer = useRef();
  const load = () => {
    if (!orgId) { setLoading(false); return; }
    setLoading(true); setError('');
    Promise.all([reportApi.analytics(orgId), projectApi.list({ organization_id: orgId, per_page: 5 }), notificationApi.list({ per_page: 5 })])
      .then(([analytics, projectResult, notificationResult]) => { setStats(analytics.data); setProjects(projectResult.data || []); setNotifications(notificationResult.data || []); })
      .catch(err => setError(err.message || 'Dashboard data could not be loaded.'))
      .finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, [orgId]);
  useEffect(() => {
    if (!orgId) return undefined;
    joinRoom('organization', orgId);
    const refresh = payload => {
      if (String(payload.organization_id) !== String(orgId)) return;
      clearTimeout(refreshTimer.current);
      refreshTimer.current = setTimeout(() => {
        Promise.all([reportApi.analytics(orgId), projectApi.list({ organization_id: orgId, per_page: 5 })])
          .then(([analytics, projectResult]) => { setStats(analytics.data); setProjects(projectResult.data || []); })
          .catch(() => {});
      }, 250);
    };
    const off = ['task.created', 'task.updated', 'task.status_changed', 'task.deleted', 'project.created', 'project.updated', 'project.deleted'].map(event => onRealtime(event, refresh));
    return () => { clearTimeout(refreshTimer.current); leaveRoom('organization', orgId); off.forEach(stop => stop()); };
  }, [orgId]);
  const statusData = useMemo(() => Object.entries(stats?.tasks_by_status || {}).map(([name, value]) => ({ name: cleanLabel(name), value })), [stats]);
  const priorityData = useMemo(() => Object.entries(stats?.tasks_by_priority || {}).map(([name, value]) => ({ name: cleanLabel(name), value })), [stats]);
  const highPriority = (stats?.tasks_by_priority?.HIGH || 0) + (stats?.tasks_by_priority?.CRITICAL || 0);
  const behindProjects = projects.filter(project => Number(project.overdue_tasks || 0) > 0);

  if (loading) return <LoadingState message="Loading workspace overview..." />;
  if (!orgId) return <EmptyState icon="bi-building" title="No Organization" message="No organization is available for your account yet." />;

  return <div className="dashboard-page">
    <PageHeader 
      title={`Good morning, ${user?.full_name?.split(' ')[0] || 'there'}`}
      description="Here's what's happening across your workspace."
      icon="👋"
    />
    
    {error && (
      <Alert 
        type="error" 
        title="Error loading dashboard"
        message={error}
        action={{ label: 'Retry', onClick: load }}
      />
    )}

    <section className="dashboard-metrics" aria-label="Workspace metrics">
      <MetricCard label="Total projects" value={stats?.total_projects ?? 0} hint={`${stats?.active_projects ?? 0} active`} />
      <MetricCard label="Active tasks" value={Math.max(0, (stats?.total_tasks || 0) - (stats?.completed_tasks || 0))} hint={`${stats?.total_tasks ?? 0} total`} tone="violet" />
      <MetricCard label="Completed tasks" value={stats?.completed_tasks ?? 0} hint={stats?.completion_rate != null ? `${stats.completion_rate}% completion` : null} tone="green" />
      <MetricCard label="Overdue tasks" value={stats?.overdue_tasks ?? 0} hint="Needs attention" tone="red" />
    </section>
    
    <section className="attention-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Investigation path</p>
          <h2>What needs attention?</h2>
        </div>
        <Link to="/reports" className="btn btn-secondary btn-sm">View all insights</Link>
      </div>
      <div className="attention-grid">
        <Card className="attention-card overdue">
          <span>Overdue</span>
          <strong>{stats?.overdue_tasks ?? 0} overdue tasks</strong>
          <small>Review tasks past their due date</small>
          <Link to="/tasks" className="btn btn-primary btn-sm" style={{ marginTop: 'auto' }}>View tasks</Link>
        </Card>
        <Card className="attention-card">
          <span>Projects</span>
          <strong>{behindProjects.length} projects need review</strong>
          <small>Projects with overdue work in the current list</small>
          <Link to="/projects" className="btn btn-primary btn-sm" style={{ marginTop: 'auto' }}>View projects</Link>
        </Card>
        <Card className="attention-card">
          <span>Priority</span>
          <strong>{highPriority} urgent tasks unresolved</strong>
          <small>High and critical priority work</small>
          <Link to="/tasks" className="btn btn-primary btn-sm" style={{ marginTop: 'auto' }}>Open tasks</Link>
        </Card>
        <Card className="attention-card action">
          <span>Next action</span>
          <strong>Review your active task queue</strong>
          <small>Move important work forward today</small>
          <Link to="/tasks" className="btn btn-primary btn-sm" style={{ marginTop: 'auto' }}>Open tasks</Link>
        </Card>
      </div>
    </section>
    
    <section className="dashboard-charts grid-2">
      <Card header={
        <div className="chart-card-heading">
          <div>
            <h2>Where is the workload?</h2>
            <p>Tasks grouped by current status.</p>
          </div>
          <Link to="/reports" className="btn-link">Reports</Link>
        </div>
      }>
        {statusData.length ? (
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={statusData} margin={{ top: 8, right: 5, left: -20, bottom: 0 }}>
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}/>
              <YAxis allowDecimals={false} tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false}/>
              <Tooltip cursor={{ fill: '#eff6ff' }} contentStyle={{ border: '1px solid #e2e8f0', borderRadius: 9, boxShadow: '0 8px 20px rgba(15,23,42,.1)' }}/>
              <Bar dataKey="value" fill="#2563eb" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <EmptyState icon="bi-bar-chart" title="No data" message="No task data yet." />
        )}
      </Card>

      <Card header={
        <div className="chart-card-heading">
          <div>
            <h2>Which work is most important?</h2>
            <p>Open workload by priority.</p>
          </div>
        </div>
      }>
        {priorityData.length ? (
          <>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={priorityData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={52} outerRadius={84} paddingAngle={3}>
                  {priorityData.map((_, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ border: '1px solid #e2e8f0', borderRadius: 9 }}/>
              </PieChart>
            </ResponsiveContainer>
            <div className="chart-legend">
              {priorityData.map((item, index) => (
                <span key={item.name}>
                  <i style={{ background: COLORS[index % COLORS.length] }} />
                  {item.name}: {item.value}
                </span>
              ))}
            </div>
          </>
        ) : (
          <EmptyState icon="bi-pie-chart" title="No data" message="No task data yet." />
        )}
      </Card>
    </section>
    
    <section className="grid-2 dashboard-bottom">
      <Card header={
        <div className="chart-card-heading">
          <div>
            <h2>Projects in motion</h2>
            <p>Recent projects and their real completion progress.</p>
          </div>
          <Link to="/projects" className="btn-link">All projects</Link>
        </div>
      }>
        {projects.length ? (
          <div className="project-list">
            {projects.map(project => (
              <Link className="project-row" to={`/projects/${project.id}`} key={project.id}>
                <span className="project-initial">{project.name.slice(0, 1).toUpperCase()}</span>
                <span className="project-row-name">
                  <strong>{project.name}</strong>
                  <small>{project.status || 'No status'}</small>
                </span>
                <span className="project-row-progress">
                  <span>{project.progress_percent || 0}%</span>
                  <i><b style={{ width: `${project.progress_percent || 0}%` }} /></i>
                </span>
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState 
            icon="bi-folder" 
            title="No projects yet" 
            message="Get started by creating your first project"
            action={<Link to="/projects" className="btn btn-primary">Create project</Link>}
          />
        )}
      </Card>

      <Card header={
        <div className="chart-card-heading">
          <div>
            <h2>Recent updates</h2>
            <p>Activity delivered to your notification inbox.</p>
          </div>
          <Link to="/notifications" className="btn-link">All notifications</Link>
        </div>
      }>
        {notifications.length ? (
          <div className="dashboard-notifications">
            {notifications.map(item => (
              <div key={item.id}>
                <span className={item.is_read ? 'read-dot' : 'unread-dot'} />
                <span>
                  <strong>{item.title}</strong>
                  <small>{item.message}</small>
                </span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState 
            icon="bi-inbox" 
            title="You're all caught up" 
            message="No new notifications"
          />
        )}
      </Card>
    </section>
  </div>;
}
