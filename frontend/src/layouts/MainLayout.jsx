import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCallback, useEffect, useState } from 'react';
import { notificationApi } from '../services/api';
import './MainLayout.css';

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/projects', label: 'Projects', icon: '📁' },
  { to: '/tasks', label: 'Tasks', icon: '✅' },
  { to: '/teams', label: 'Teams', icon: '👥' },
  { to: '/calendar', label: 'Calendar', icon: '📅' },
  { to: '/reports', label: 'Reports', icon: '📈' },
  { to: '/notifications', label: 'Notifications', icon: '🔔' },
  { to: '/activity', label: 'Activity', icon: '📋' },
  { to: '/users', label: 'Users', icon: '👤' },
  { to: '/settings', label: 'Settings', icon: '⚙️' },
];

const notificationDestination = (notification) => {
  if (notification.entity_type === 'task' && notification.entity_id) return `/tasks/${notification.entity_id}`;
  if (notification.entity_type === 'project' && notification.entity_id) return `/projects/${notification.entity_id}`;
  if (notification.entity_type === 'team') return '/teams';
  return null;
};

const relativeTime = (value) => {
  if (!value) return '';
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
};

export default function MainLayout() {
  const { user, logout, organization } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => localStorage.getItem('sidebar_collapsed') === 'true');
  const [unread, setUnread] = useState(0);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [notificationLoading, setNotificationLoading] = useState(false);
  const [notificationError, setNotificationError] = useState('');
  const [searchQ, setSearchQ] = useState('');

  const loadNotifications = useCallback(async () => {
    setNotificationLoading(true); setNotificationError('');
    try { const [countResponse, listResponse] = await Promise.all([notificationApi.unreadCount(), notificationApi.list({ per_page: 6 })]); setUnread(countResponse.data?.count || 0); setNotifications(listResponse.data || []); }
    catch (err) { setNotificationError(err.message || 'Unable to load notifications.'); }
    finally { setNotificationLoading(false); }
  }, []);

  useEffect(() => { loadNotifications(); const timer = setInterval(loadNotifications, 60000); return () => clearInterval(timer); }, [loadNotifications]);
  const openNotification = () => { setNotificationOpen(open => !open); if (!notificationOpen) loadNotifications(); };
  const handleNotificationClick = async (notification) => {
    try { if (!notification.is_read) await notificationApi.markRead(notification.id); const destination = notificationDestination(notification); setNotificationOpen(false); if (destination) navigate(destination); await loadNotifications(); }
    catch (err) { setNotificationError(err.message || 'Unable to update notification.'); }
  };
  const markAllRead = async () => { try { await notificationApi.markAllRead(); await loadNotifications(); } catch (err) { setNotificationError(err.message || 'Unable to mark notifications as read.'); } };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQ.trim()) navigate(`/search?q=${encodeURIComponent(searchQ.trim())}`);
  };

  const toggleCollapsed = () => {
    const next = !sidebarCollapsed;
    setSidebarCollapsed(next);
    localStorage.setItem('sidebar_collapsed', String(next));
  };

  return (
    <div className="layout">
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''} ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-brand">
          <span className="brand-icon">P</span>
          <span className="sidebar-label">PMS</span>
          <button type="button" className="sidebar-collapse" onClick={toggleCollapsed} aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}>{sidebarCollapsed ? '›' : '‹'}</button>
        </div>
        {organization && (
          <div className="sidebar-org">{organization.name}</div>
        )}
        <nav className="sidebar-nav">
          {NAV.map(item => (
            <NavLink key={item.to} to={item.to} title={sidebarCollapsed ? item.label : undefined} className={({ isActive }) => isActive ? 'active' : ''} onClick={() => setSidebarOpen(false)}>
              <span className="nav-icon" aria-hidden="true">{item.icon}</span> <span className="sidebar-label">{item.label}</span>
              {item.to === '/notifications' && unread > 0 && (
                <span className="nav-badge">{unread}</span>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="profile-card">
            <span className="avatar" aria-hidden="true">{(user?.full_name || user?.username || 'U').slice(0, 1).toUpperCase()}</span>
            <div style={{ minWidth: 0 }}>
              <div className="profile-name">{user?.full_name || user?.username}</div>
              <div className="profile-email">{user?.email}</div>
            </div>
            <button type="button" className="logout-button" onClick={handleLogout} aria-label="Log out">↪</button>
          </div>
        </div>
      </aside>

      <div className="layout-main">
        <header className="header">
          <button type="button" className="menu-toggle btn btn-secondary btn-sm" onClick={() => setSidebarOpen(!sidebarOpen)} aria-label="Toggle menu">☰</button>
          <form onSubmit={handleSearch} className="header-search">
            <input className="input" placeholder="Search..." value={searchQ} onChange={e => setSearchQ(e.target.value)} aria-label="Global search" />
          </form>
          <div className="header-right">
            <div className="notification-menu"><button type="button" className="header-notif" onClick={openNotification} aria-label="Notifications" aria-expanded={notificationOpen}>🔔 {unread > 0 && <span className="nav-badge">{unread > 99 ? '99+' : unread}</span>}</button>{notificationOpen && <div className="notification-panel" role="dialog" aria-label="Recent notifications"><div className="notification-panel-header"><strong>Notifications</strong>{unread > 0 && <button type="button" className="btn btn-secondary btn-sm" onClick={markAllRead}>Mark all read</button>}</div>{notificationLoading ? <div className="notification-panel-state">Loading notifications…</div> : notificationError ? <div className="notification-panel-state"><span>{notificationError}</span><button type="button" className="btn btn-secondary btn-sm" onClick={loadNotifications}>Retry</button></div> : notifications.length === 0 ? <div className="notification-panel-state">You’re all caught up.</div> : <div className="notification-list">{notifications.map(notification => <button type="button" key={notification.id} className={`notification-item ${notification.is_read ? '' : 'unread'}`} onClick={() => handleNotificationClick(notification)}><span className="notification-icon">{notification.event_type.includes('TASK') ? '✓' : notification.event_type.includes('TEAM') ? '👥' : '📁'}</span><span><strong>{notification.title}</strong><small>{notification.message}</small><em>{relativeTime(notification.created_at)}</em></span></button>)}</div>}<NavLink to="/notifications" className="notification-panel-footer" onClick={() => setNotificationOpen(false)}>View all notifications</NavLink></div>}</div>
            <span className="user-name">{user?.full_name}</span>
            <button type="button" className="btn btn-secondary btn-sm" onClick={handleLogout}>Logout</button>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
      {sidebarOpen && <div className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} role="presentation" />}
    </div>
  );
}
