import { useEffect, useState } from 'react';
import { notificationApi } from '../services/api';

export default function NotificationsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => {
    notificationApi.list({ per_page: 50 })
      .then(r => setItems(r.data || []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const markRead = async (id) => {
    await notificationApi.markRead(id);
    load();
  };

  const markAllRead = async () => {
    await notificationApi.markAllRead();
    load();
  };

  if (loading) return <div className="loader">Loading notifications...</div>;

  return (
    <div>
      <div className="page-header">
        <div><h1>Notifications</h1><p>Stay updated on project activity</p></div>
        {items.some(n => !n.is_read) && (
          <button className="btn btn-secondary" onClick={markAllRead}>Mark all read</button>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {items.length === 0 ? (
        <div className="card empty-state">No notifications</div>
      ) : (
        <div className="card">
          {items.map(n => (
            <div key={n.id} style={{
              padding: '16px 0',
              borderBottom: '1px solid var(--border)',
              opacity: n.is_read ? 0.7 : 1,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
                <div>
                  <strong>{n.title}</strong>
                  {!n.is_read && <span className="badge badge-high" style={{ marginLeft: 8 }}>New</span>}
                  <p style={{ marginTop: 4, color: 'var(--text-muted)' }}>{n.message}</p>
                  <small style={{ color: 'var(--text-muted)' }}>{n.created_at ? new Date(n.created_at).toLocaleString() : ''}</small>
                </div>
                {!n.is_read && (
                  <button className="btn btn-secondary btn-sm" onClick={() => markRead(n.id)}>Mark read</button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
