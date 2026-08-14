import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { reportApi } from '../services/api';

export default function ActivityPage() {
  const { orgId } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!orgId) { setLoading(false); return; }
    setLoading(true);
    setError('');
    reportApi.activity({ organization_id: orgId, per_page: 50 })
      .then(r => setItems(r.data || []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [orgId]);

  if (loading) return <div className="loader">Loading activity...</div>;

  return (
    <div>
      <div className="page-header">
        <div><h1>Activity</h1><p>A live record of work across your organization.</p></div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {items.length === 0 ? (
        <div className="card empty-state">No activity yet</div>
      ) : (
        <div className="card" style={{ paddingTop: 8, paddingBottom: 8 }}>
          {items.map(a => (
            <div key={a.id} className="timeline-item">
              <div className="timeline-avatar" aria-hidden="true">{(a.actor_name || 'S').slice(0, 1).toUpperCase()}</div>
              <div className="timeline-copy">
                <strong>{a.actor_name || 'System'}</strong>
                <span style={{ color: 'var(--text-muted)' }}> — {a.action?.replace(/_/g, ' ')}</span>
                {a.entity_type && (
                  <span style={{ color: 'var(--text-muted)' }}> ({a.entity_type}{a.entity_id ? ` #${a.entity_id.slice(0, 8)}` : ''})</span>
                )}
                <div className="timeline-meta">
                  {a.created_at ? new Date(a.created_at).toLocaleString() : ''}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
