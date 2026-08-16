import { useEffect, useState } from 'react';
import { notificationApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { onRealtime } from '../services/realtime';
import { PageHeader, Card, LoadingState, EmptyState, Alert, Badge } from '../components';

export default function NotificationsPage() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => {
    notificationApi.list({ per_page: 50 })
      .then(r => setItems(r.data || []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(
    () =>
      onRealtime('notification.new', notification => {
        if (String(notification.user_id) !== String(user?.id)) return;
        setItems(current => [
          notification,
          ...current.filter(item => item.id !== notification.id)
        ]);
      }),
    [user?.id]
  );

  const markRead = async (id) => {
    await notificationApi.markRead(id);
    load();
  };

  const markAllRead = async () => {
    await notificationApi.markAllRead();
    load();
  };

  if (loading) return <LoadingState message="Loading notifications..." />;

  const unreadCount = items.filter(n => !n.is_read).length;

  return (
    <div>
      <PageHeader
        title="Notifications"
        description="Stay updated on project activity"
        icon="🔔"
        action={
          unreadCount > 0 && (
            <button className="btn btn-secondary" onClick={markAllRead}>
              Mark all read
            </button>
          )
        }
      />

      {error && <Alert type="error" title="Error" message={error} onClose={() => setError('')} />}

      {items.length === 0 ? (
        <EmptyState
          icon="🔔"
          title="No notifications"
          message="You're all caught up! No new notifications."
        />
      ) : (
        <Card>
          {items.map(n => (
            <div
              key={n.id}
              style={{
                padding: '16px 0',
                borderBottom: '1px solid var(--border)',
                opacity: n.is_read ? 0.7 : 1,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                gap: 16
              }}
            >
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <strong>{n.title}</strong>
                  {!n.is_read && <Badge variant="danger">New</Badge>}
                </div>
                <p style={{ margin: '4px 0', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                  {n.message}
                </p>
                <small style={{ color: 'var(--text-muted)' }}>
                  {n.created_at ? new Date(n.created_at).toLocaleString() : ''}
                </small>
              </div>
              {!n.is_read && (
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => markRead(n.id)}
                  style={{ whiteSpace: 'nowrap' }}
                >
                  Mark read
                </button>
              )}
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}
