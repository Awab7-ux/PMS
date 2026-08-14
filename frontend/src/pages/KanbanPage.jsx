import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { projectApi, taskApi } from '../services/api';

const COLUMNS = ['BACKLOG', 'TODO', 'IN_PROGRESS', 'REVIEW', 'DONE'];
const COLUMN_LABELS = { BACKLOG: 'Backlog', TODO: 'Todo', IN_PROGRESS: 'In Progress', REVIEW: 'Review', DONE: 'Done' };

export default function KanbanPage() {
  const { id: projectId } = useParams();
  const [board, setBoard] = useState({});
  const [project, setProject] = useState(null);
  const [dragTask, setDragTask] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [newTask, setNewTask] = useState({ title: '', priority: 'MEDIUM', status: 'TODO' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = () => {
    setLoading(true); setError('');
    Promise.all([taskApi.kanban(projectId), projectApi.get(projectId)])
      .then(([tasks, projectRes]) => { setBoard(tasks.data || {}); setProject(projectRes.data); })
      .catch(err => setError(err.message || 'Unable to load this board.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [projectId]);

  const handleDrop = async (status, order) => {
    if (!dragTask) return;
    try { await taskApi.move(dragTask.id, { status, kanban_order: order }); load(); }
    catch (err) { setError(err.message || 'Unable to move this task.'); }
    finally { setDragTask(null); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try { await taskApi.create({ ...newTask, project_id: projectId }); setShowModal(false); setNewTask({ title: '', priority: 'MEDIUM', status: 'TODO' }); load(); }
    catch (err) { setError(err.message || 'Unable to create task.'); }
    finally { setSaving(false); }
  };

  return (
    <div>
      <div className="page-header">
        <div><h1>Kanban — {project?.name || '...'}</h1></div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ Add Task</button>
      </div>
      {error && <div className="alert alert-error">{error}</div>}

      {loading ? <div className="kanban-board">{COLUMNS.map(column => <div className="kanban-column" key={column}><div className="kanban-column-header">{COLUMN_LABELS[column]}</div><div className="kanban-column-body"><div className="skeleton skeleton-card" /><div className="skeleton skeleton-card" style={{ marginTop: 10 }} /></div></div>)}</div> :

      <div className="kanban-board">
        {COLUMNS.map(status => (
          <div key={status} className="kanban-column"
            onDragOver={e => e.preventDefault()}
            onDrop={() => handleDrop(status, (board[status]?.length || 0))}>
            <div className="kanban-column-header">
              {COLUMN_LABELS[status]}
              <span>{board[status]?.length || 0}</span>
            </div>
            <div className="kanban-column-body">
              {(board[status] || []).map((task, idx) => (
                <div key={task.id} className={`kanban-card ${dragTask?.id === task.id ? 'dragging' : ''}`}
                  draggable
                  onDragStart={() => setDragTask(task)}
                  onDragOver={e => e.preventDefault()}
                  onDrop={e => { e.stopPropagation(); handleDrop(status, idx); }}>
                  <h4>{task.title}</h4>
                  <div className="kanban-card-meta">
                    <span className={`badge badge-${task.priority?.toLowerCase()}`}>{task.priority}</span>
                    {task.due_date && <span>📅 {task.due_date}</span>}
                    {task.progress_percent > 0 && <span>{task.progress_percent}%</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      }

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>New Task</h2>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label className="label">Title</label>
                <input className="input" value={newTask.title} onChange={e => setNewTask({ ...newTask, title: e.target.value })} required />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="label">Status</label>
                  <select className="select" value={newTask.status} onChange={e => setNewTask({ ...newTask, status: e.target.value })}>
                    {COLUMNS.map(s => <option key={s} value={s}>{COLUMN_LABELS[s]}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="label">Priority</label>
                  <select className="select" value={newTask.priority} onChange={e => setNewTask({ ...newTask, priority: e.target.value })}>
                    {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(s => <option key={s}>{s}</option>)}
                  </select>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Creating…' : 'Create task'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
