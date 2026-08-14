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
            <div key={a.id} style={{ padding: '12px 0', borderBottom: '1px solid var(--border)', display: 'flex', gap: 16 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--primary)', marginTop: 8, flexShrink: 0 }} />
              <div>
                <strong>{a.actor_name || 'System'}</strong>
                <span style={{ color: 'var(--text-muted)' }}> — {a.action?.replace(/_/g, ' ')}</span>
                {a.entity_type && (
                  <span style={{ color: 'var(--text-muted)' }}> ({a.entity_type}{a.entity_id ? ` #${a.entity_id.slice(0, 8)}` : ''})</span>
                )}
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: 4 }}>
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
