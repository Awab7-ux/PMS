import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { projectApi, taskApi, userApi } from '../services/api';
import {
  PageHeader, Card, Modal, LoadingState, EmptyState, Alert, Badge,
  Input, Select, Textarea, FormGroup, FormSection
} from '../components';

const statuses = ['BACKLOG', 'TODO', 'IN_PROGRESS', 'REVIEW', 'DONE'];
const priorities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
const blankTask = { title: '', description: '', assignee_id: '', priority: 'MEDIUM', status: 'TODO', due_date: '' };

export default function TasksPage() {
  const { orgId } = useAuth();
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    assignee_id: '',
    due_date: '',
    sort_by: 'updated_at',
    sort_dir: 'desc'
  });
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(blankTask);

  const loadTasks = useCallback(async () => {
    if (!projectId) {
      setTasks([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await taskApi.list({ project_id: projectId, per_page: 100, search, ...filters });
      setTasks(res.data || []);
    } catch (err) {
      setError(err.message || 'Unable to load tasks right now.');
    } finally {
      setLoading(false);
    }
  }, [projectId, search, filters]);

  useEffect(() => {
    if (!orgId) {
      setLoading(false);
      return;
    }
    Promise.all([
      projectApi.list({ organization_id: orgId, per_page: 100 }),
      userApi.list({ organization_id: orgId, per_page: 100 })
    ])
      .then(([projectRes, userRes]) => {
        const list = projectRes.data || [];
        setProjects(list);
        setUsers(userRes.data || []);
        setProjectId(current => current || list[0]?.id || '');
      })
      .catch(err => {
        setError(err.message || 'Unable to load task workspace.');
        setLoading(false);
      });
  }, [orgId]);

  useEffect(() => {
    const timer = setTimeout(loadTasks, 250);
    return () => clearTimeout(timer);
  }, [loadTasks]);

  const createTask = async (event) => {
    event.preventDefault();
    try {
      await taskApi.create({
        ...form,
        project_id: projectId,
        assignee_id: form.assignee_id || null,
        due_date: form.due_date || null
      });
      setForm(blankTask);
      setShowCreate(false);
      loadTasks();
    } catch (err) {
      setError(err.message || 'Unable to create this task.');
    }
  };

  const taskAssignee = (task) =>
    task.assignee?.full_name ||
    users.find(user => user.id === task.assignee_id)?.full_name ||
    'Unassigned';

  const changeStatus = async (task, status) => {
    const previousTasks = tasks;
    setTasks(current =>
      current.map(item => (item.id === task.id ? { ...item, status } : item))
    );
    try {
      await taskApi.update(task.id, { status });
    } catch (err) {
      setTasks(previousTasks);
      setError(err.message || 'Unable to update task status.');
    }
  };

  return (
    <div>
      <PageHeader
        title="Tasks"
        description="Plan the next piece of work and keep ownership clear."
        icon="✓"
        action={
          <button
            className="btn btn-primary"
            disabled={!projectId}
            onClick={() => setShowCreate(true)}
          >
            + New task
          </button>
        }
      />

      {error && (
        <Alert
          type="error"
          title="Error"
          message={error}
          onClose={() => setError('')}
          action={{ label: 'Try again', onClick: loadTasks }}
        />
      )}

      <Card>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: 12,
            padding: 16
          }}
        >
          <Select
            label="Project"
            value={projectId}
            onChange={event => setProjectId(event.target.value)}
            options={
              projects.length
                ? projects.map(p => ({ value: p.id, label: p.name }))
                : [{ value: '', label: 'No projects available' }]
            }
          />
          <Input
            placeholder="Search title or description…"
            value={search}
            onChange={event => setSearch(event.target.value)}
            type="search"
          />
          <Select
            label="Status"
            value={filters.status}
            onChange={event => setFilters({ ...filters, status: event.target.value })}
            options={[
              { value: '', label: 'All statuses' },
              ...statuses.map(s => ({ value: s, label: s }))
            ]}
          />
          <Select
            label="Priority"
            value={filters.priority}
            onChange={event => setFilters({ ...filters, priority: event.target.value })}
            options={[
              { value: '', label: 'All priorities' },
              ...priorities.map(p => ({ value: p, label: p }))
            ]}
          />
          <Select
            label="Assignee"
            value={filters.assignee_id}
            onChange={event => setFilters({ ...filters, assignee_id: event.target.value })}
            options={[
              { value: '', label: 'All assignees' },
              ...users.map(u => ({ value: u.id, label: u.full_name }))
            ]}
          />
          <Input
            type="date"
            label="Due date"
            value={filters.due_date}
            onChange={event => setFilters({ ...filters, due_date: event.target.value })}
          />
          <Select
            label="Sort"
            value={`${filters.sort_by}:${filters.sort_dir}`}
            onChange={event => {
              const [sort_by, sort_dir] = event.target.value.split(':');
              setFilters({ ...filters, sort_by, sort_dir });
            }}
            options={[
              { value: 'updated_at:desc', label: 'Recently updated' },
              { value: 'created_at:desc', label: 'Newest first' },
              { value: 'due_date:asc', label: 'Due date' },
              { value: 'priority:desc', label: 'Priority' },
              { value: 'title:asc', label: 'Title' }
            ]}
          />
        </div>
      </Card>

      {loading ? (
        <LoadingState message="Loading tasks..." />
      ) : (
        <Card>
          {tasks.length === 0 ? (
            <EmptyState
              icon="✓"
              title="No tasks"
              message="No tasks match these filters. Create a task or adjust the filters."
              action={
                <button
                  className="btn btn-primary"
                  disabled={!projectId}
                  onClick={() => setShowCreate(true)}
                >
                  Create First Task
                </button>
              }
            />
          ) : (
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>Task</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Assignee</th>
                    <th>Due date</th>
                    <th>Progress</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map(task => (
                    <tr key={task.id}>
                      <td>
                        <Link to={`/tasks/${task.id}`} className="btn-link">
                          {task.title}
                        </Link>
                      </td>
                      <td>
                        <Select
                          value={task.status}
                          onChange={event => changeStatus(task, event.target.value)}
                          options={statuses.map(s => ({ value: s, label: s }))}
                          style={{ minWidth: 120 }}
                        />
                      </td>
                      <td>
                        <Badge
                          variant={
                            task.priority === 'CRITICAL'
                              ? 'danger'
                              : task.priority === 'HIGH'
                                ? 'warning'
                                : task.priority === 'MEDIUM'
                                  ? 'info'
                                  : 'secondary'
                          }
                        >
                          {task.priority}
                        </Badge>
                      </td>
                      <td>{taskAssignee(task)}</td>
                      <td>{task.due_date || '—'}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div
                            className="progress"
                            style={{ flex: 1, minWidth: 72 }}
                          >
                            <div
                              style={{
                                width: `${task.progress_percent || 0}%`,
                                height: '4px',
                                borderRadius: '2px',
                                background: 'var(--primary)'
                              }}
                            />
                          </div>
                          <span style={{ minWidth: 40 }}>
                            {task.progress_percent || 0}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      <Modal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        title="Create New Task"
        size="lg"
      >
        <form onSubmit={createTask}>
          <FormSection>
            <FormGroup label="Title" required>
              <Input
                value={form.title}
                onChange={event => setForm({ ...form, title: event.target.value })}
                placeholder="Enter task title"
                required
                autoFocus
              />
            </FormGroup>

            <FormGroup label="Description">
              <Textarea
                value={form.description}
                onChange={event =>
                  setForm({ ...form, description: event.target.value })
                }
                placeholder="Describe the task..."
                rows={4}
              />
            </FormGroup>

            <div
              style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}
            >
              <FormGroup label="Assignee">
                <Select
                  value={form.assignee_id}
                  onChange={event =>
                    setForm({ ...form, assignee_id: event.target.value })
                  }
                  options={[
                    { value: '', label: 'Unassigned' },
                    ...users.map(u => ({ value: u.id, label: u.full_name }))
                  ]}
                />
              </FormGroup>

              <FormGroup label="Due date">
                <Input
                  type="date"
                  value={form.due_date}
                  onChange={event =>
                    setForm({ ...form, due_date: event.target.value })
                  }
                />
              </FormGroup>
            </div>

            <div
              style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}
            >
              <FormGroup label="Status" required>
                <Select
                  value={form.status}
                  onChange={event =>
                    setForm({ ...form, status: event.target.value })
                  }
                  options={statuses.map(s => ({ value: s, label: s }))}
                />
              </FormGroup>

              <FormGroup label="Priority" required>
                <Select
                  value={form.priority}
                  onChange={event =>
                    setForm({ ...form, priority: event.target.value })
                  }
                  options={priorities.map(p => ({ value: p, label: p }))}
                />
              </FormGroup>
            </div>
          </FormSection>

          <div
            style={{
              display: 'flex',
              gap: 8,
              justifyContent: 'flex-end',
              marginTop: 24
            }}
          >
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowCreate(false)}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Create Task
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
