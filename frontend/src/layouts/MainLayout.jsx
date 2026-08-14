import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useEffect, useState } from 'react';
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

export default function MainLayout() {
  const { user, logout, organization } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const [searchQ, setSearchQ] = useState('');

  useEffect(() => {
    notificationApi.unreadCount().then(r => setUnread(r.data?.count || 0)).catch(() => {});
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQ.trim()) navigate(`/search?q=${encodeURIComponent(searchQ.trim())}`);
  };

  return (
    <div className="layout">
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-brand">
          <span className="brand-icon">P</span>
          <span>PMS</span>
        </div>
        {organization && (
          <div className="sidebar-org">{organization.name}</div>
        )}
        <nav className="sidebar-nav">
          {NAV.map(item => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => isActive ? 'active' : ''} onClick={() => setSidebarOpen(false)}>
              <span className="nav-icon" aria-hidden="true">{item.icon}</span> {item.label}
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
            <NavLink to="/notifications" className="header-notif" aria-label="Notifications">
              🔔 {unread > 0 && <span className="nav-badge">{unread}</span>}
            </NavLink>
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
