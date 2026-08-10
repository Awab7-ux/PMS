import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { calendarApi } from '../services/api';

function getMonthRange(d = new Date()) {
  const start = new Date(d.getFullYear(), d.getMonth(), 1);
  const end = new Date(d.getFullYear(), d.getMonth() + 1, 0);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
    label: start.toLocaleString('default', { month: 'long', year: 'numeric' }),
  };
}

export default function CalendarPage() {
  const { orgId } = useAuth();
  const [range, setRange] = useState(getMonthRange());
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!orgId) return;
    setLoading(true);
    calendarApi.events({ organization_id: orgId, start: range.start, end: range.end })
      .then(r => setEvents(r.data?.events || r.data || []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [orgId, range]);

  const shiftMonth = (delta) => {
    const d = new Date(range.start);
    d.setMonth(d.getMonth() + delta);
    setRange(getMonthRange(d));
  };

  const grouped = events.reduce((acc, ev) => {
    const day = ev.date?.slice(0, 10) || 'unknown';
    if (!acc[day]) acc[day] = [];
    acc[day].push(ev);
    return acc;
  }, {});

  if (loading) return <div className="loader">Loading calendar...</div>;

  return (
    <div>
      <div className="page-header">
        <div><h1>Calendar</h1><p>Task deadlines and project milestones</p></div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button className="btn btn-secondary btn-sm" onClick={() => shiftMonth(-1)}>← Prev</button>
          <strong>{range.label}</strong>
          <button className="btn btn-secondary btn-sm" onClick={() => shiftMonth(1)}>Next →</button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {events.length === 0 ? (
        <div className="card empty-state">No events this month</div>
      ) : (
        <div className="card">
          {Object.keys(grouped).sort().map(day => (
            <div key={day} style={{ padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
              <strong style={{ display: 'block', marginBottom: 8 }}>{new Date(day + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}</strong>
              {grouped[day].map((ev, i) => (
                <div key={i} style={{ padding: '6px 12px', marginBottom: 4, background: 'var(--bg)', borderRadius: 'var(--radius)', display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span className={`badge badge-${ev.type === 'task_deadline' ? 'high' : 'medium'}`}>{ev.type?.replace('_', ' ')}</span>
                  <span>{ev.title}</span>
                  {ev.entity_type === 'task' && ev.entity_id && (
                    <Link to={`/tasks/${ev.entity_id}`}>View</Link>
                  )}
                  {ev.entity_type === 'project' && ev.entity_id && (
                    <Link to={`/projects/${ev.entity_id}`}>View</Link>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
