import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { taskApi, commentApi } from '../services/api';

export default function TaskDetailPage() {
  const { id } = useParams();
  const [task, setTask] = useState(null);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [newSubtask, setNewSubtask] = useState('');
  const [loading, setLoading] = useState(true);

  const load = () => {
    Promise.all([
      taskApi.get(id),
      commentApi.list(id),
    ]).then(([tRes, cRes]) => {
      setTask(tRes.data);
      setComments(cRes.data || []);
    }).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [id]);

  const handleComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    await commentApi.create(id, { content: newComment });
    setNewComment('');
    load();
  };

  const handleSubtask = async (e) => {
    e.preventDefault();
    if (!newSubtask.trim()) return;
    await taskApi.createSubtask(id, { title: newSubtask });
    setNewSubtask('');
    load();
  };

  const toggleSubtask = async (sub) => {
    await taskApi.updateSubtask(id, sub.id, { is_completed: !sub.is_completed });
    load();
  };

  if (loading) return <div className="loader">Loading...</div>;
  if (!task) return <div className="empty-state">Task not found</div>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>{task.title}</h1>
          <p>{task.description || 'No description'}</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <span className={`badge badge-${task.status?.toLowerCase()}`}>{task.status}</span>
          <span className={`badge badge-${task.priority?.toLowerCase()}`}>{task.priority}</span>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3 style={{ marginBottom: 16 }}>Subtasks ({task.progress_percent}%)</h3>
          {(task.subtasks || []).map(sub => (
            <label key={sub.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0' }}>
              <input type="checkbox" checked={sub.is_completed} onChange={() => toggleSubtask(sub)} />
              <span style={{ textDecoration: sub.is_completed ? 'line-through' : 'none' }}>{sub.title}</span>
            </label>
          ))}
          <form onSubmit={handleSubtask} style={{ marginTop: 12, display: 'flex', gap: 8 }}>
            <input className="input" placeholder="Add subtask..." value={newSubtask} onChange={e => setNewSubtask(e.target.value)} />
            <button className="btn btn-primary btn-sm">Add</button>
          </form>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 16 }}>Comments</h3>
          {comments.map(c => (
            <div key={c.id} style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
              <strong>{c.author_name || 'User'}</strong>
              <p style={{ marginTop: 4 }}>{c.content}</p>
            </div>
          ))}
          <form onSubmit={handleComment} style={{ marginTop: 12 }}>
            <textarea className="textarea" placeholder="Write a comment..." value={newComment} onChange={e => setNewComment(e.target.value)} />
            <button className="btn btn-primary btn-sm" style={{ marginTop: 8 }}>Post</button>
          </form>
        </div>
      </div>
    </div>
  );
}
