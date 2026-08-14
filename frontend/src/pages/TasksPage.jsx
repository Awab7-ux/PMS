import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { projectApi, taskApi, userApi } from '../services/api';

const statuses = ['BACKLOG', 'TODO', 'IN_PROGRESS', 'REVIEW', 'DONE'];
const priorities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
const blankTask = { title: '', description: '', assignee_id: '', priority: 'MEDIUM', status: 'TODO', due_date: '' };

export default function TasksPage() {
  const { orgId } = useAuth();
  const [projects, setProjects] = useState([]); const [users, setUsers] = useState([]); const [projectId, setProjectId] = useState('');
  const [tasks, setTasks] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  const [search, setSearch] = useState(''); const [filters, setFilters] = useState({ status: '', priority: '', assignee_id: '', due_date: '', sort_by: 'updated_at', sort_dir: 'desc' });
  const [showCreate, setShowCreate] = useState(false); const [form, setForm] = useState(blankTask); const [saving, setSaving] = useState(false);

  const loadTasks = useCallback(async () => {
    if (!projectId) { setTasks([]); setLoading(false); return; }
    setLoading(true); setError('');
    try { const res = await taskApi.list({ project_id: projectId, per_page: 100, search, ...filters }); setTasks(res.data || []); }
    catch (err) { setError(err.message || 'Unable to load tasks right now.'); }
    finally { setLoading(false); }
  }, [projectId, search, filters]);

  useEffect(() => {
    if (!orgId) { setLoading(false); return; }
    Promise.all([projectApi.list({ organization_id: orgId, per_page: 100 }), userApi.list({ organization_id: orgId, per_page: 100 })])
      .then(([projectRes, userRes]) => { const list = projectRes.data || []; setProjects(list); setUsers(userRes.data || []); setProjectId(current => current || list[0]?.id || ''); })
      .catch(err => { setError(err.message || 'Unable to load task workspace.'); setLoading(false); });
  }, [orgId]);
  useEffect(() => { const timer = setTimeout(loadTasks, 250); return () => clearTimeout(timer); }, [loadTasks]);

  const createTask = async (event) => {
    event.preventDefault(); setSaving(true); setError('');
    try { await taskApi.create({ ...form, project_id: projectId, assignee_id: form.assignee_id || null, due_date: form.due_date || null }); setForm(blankTask); setShowCreate(false); loadTasks(); }
    catch (err) { setError(err.message || 'Unable to create this task.'); }
    finally { setSaving(false); }
  };
  const taskAssignee = (task) => task.assignee?.full_name || users.find(user => user.id === task.assignee_id)?.full_name || 'Unassigned';
  const changeStatus = async (task, status) => {
    const previousTasks = tasks;
    setTasks(current => current.map(item => item.id === task.id ? { ...item, status } : item));
    try { await taskApi.update(task.id, { status }); }
    catch (err) { setTasks(previousTasks); setError(err.message || 'Unable to update task status.'); }
  };

  return <div>
    <div className="page-header"><div><h1>Tasks</h1><p>Plan the next piece of work and keep ownership clear.</p></div><button className="btn btn-primary" disabled={!projectId} onClick={() => setShowCreate(true)}>+ New task</button></div>
    {error && <div className="alert alert-error">{error} <button type="button" className="btn btn-secondary btn-sm" onClick={loadTasks}>Try again</button></div>}
    <div className="page-toolbar">
      <select className="select" value={projectId} onChange={event => setProjectId(event.target.value)} style={{ maxWidth: 250 }} aria-label="Project">{projects.length ? projects.map(project => <option key={project.id} value={project.id}>{project.name}</option>) : <option>No projects available</option>}</select>
      <input className="input" value={search} onChange={event => setSearch(event.target.value)} placeholder="Search title or description…" aria-label="Search tasks" />
      <select className="select" value={filters.status} onChange={event => setFilters({ ...filters, status: event.target.value })} aria-label="Filter by status"><option value="">All statuses</option>{statuses.map(value => <option key={value}>{value}</option>)}</select>
      <select className="select" value={filters.priority} onChange={event => setFilters({ ...filters, priority: event.target.value })} aria-label="Filter by priority"><option value="">All priorities</option>{priorities.map(value => <option key={value}>{value}</option>)}</select>
      <select className="select" value={filters.assignee_id} onChange={event => setFilters({ ...filters, assignee_id: event.target.value })} aria-label="Filter by assignee"><option value="">All assignees</option>{users.map(user => <option key={user.id} value={user.id}>{user.full_name}</option>)}</select>
      <input className="input" type="date" value={filters.due_date} onChange={event => setFilters({ ...filters, due_date: event.target.value })} aria-label="Filter by due date" title="Filter by due date" />
      <select className="select" value={`${filters.sort_by}:${filters.sort_dir}`} onChange={event => { const [sort_by, sort_dir] = event.target.value.split(':'); setFilters({ ...filters, sort_by, sort_dir }); }} aria-label="Sort tasks"><option value="updated_at:desc">Recently updated</option><option value="created_at:desc">Newest first</option><option value="due_date:asc">Due date</option><option value="priority:desc">Priority</option><option value="title:asc">Title</option></select>
    </div>
    {loading ? <div className="card"><div className="skeleton skeleton-line" /><div className="skeleton skeleton-line" /><div className="skeleton skeleton-line short" /></div> : <div className="card table-wrap">{tasks.length === 0 ? <div className="empty-state">No tasks match these filters. Create a task or adjust the filters.</div> : <table><thead><tr><th>Task</th><th>Status</th><th>Priority</th><th>Assignee</th><th>Due date</th><th>Progress</th></tr></thead><tbody>{tasks.map(task => <tr key={task.id}><td><Link to={`/tasks/${task.id}`}>{task.title}</Link></td><td><select className="select" value={task.status} onChange={event => changeStatus(task, event.target.value)} aria-label={`Change status for ${task.title}`}>{statuses.map(value => <option key={value}>{value}</option>)}</select></td><td><span className={`badge badge-${task.priority?.toLowerCase()}`}>{task.priority}</span></td><td>{taskAssignee(task)}</td><td>{task.due_date || '—'}</td><td><div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><div className="progress" style={{ width: 72 }}><span style={{ width: `${task.progress_percent || 0}%` }} /></div>{task.progress_percent || 0}%</div></td></tr>)}</tbody></table>}</div>}
    {showCreate && <div className="modal-overlay" onClick={() => setShowCreate(false)}><div className="modal" onClick={event => event.stopPropagation()} role="dialog" aria-modal="true" aria-labelledby="create-task-title"><h2 id="create-task-title">Create task</h2><form onSubmit={createTask}><div className="form-group"><label className="label">Title</label><input className="input" value={form.title} onChange={event => setForm({ ...form, title: event.target.value })} required autoFocus /></div><div className="form-group"><label className="label">Description</label><textarea className="textarea" value={form.description} onChange={event => setForm({ ...form, description: event.target.value })} /></div><div className="form-row"><div className="form-group"><label className="label">Assignee</label><select className="select" value={form.assignee_id} onChange={event => setForm({ ...form, assignee_id: event.target.value })}><option value="">Unassigned</option>{users.map(user => <option key={user.id} value={user.id}>{user.full_name}</option>)}</select></div><div className="form-group"><label className="label">Due date</label><input className="input" type="date" value={form.due_date} onChange={event => setForm({ ...form, due_date: event.target.value })} /></div></div><div className="form-row"><div className="form-group"><label className="label">Status</label><select className="select" value={form.status} onChange={event => setForm({ ...form, status: event.target.value })}>{statuses.map(value => <option key={value}>{value}</option>)}</select></div><div className="form-group"><label className="label">Priority</label><select className="select" value={form.priority} onChange={event => setForm({ ...form, priority: event.target.value })}>{priorities.map(value => <option key={value}>{value}</option>)}</select></div></div><div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}><button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button><button className="btn btn-primary" disabled={saving}>{saving ? 'Creating…' : 'Create task'}</button></div></form></div></div>}
  </div>;
}
