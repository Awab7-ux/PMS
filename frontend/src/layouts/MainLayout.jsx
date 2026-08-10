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
  { to: '/settings', label: 'Settings', icon: '⚙️' },
];

export default function MainLayout() {
  const { user, logout, organization } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    notificationApi.unreadCount().then(r => setUnread(r.data?.count || 0)).catch(() => {});
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
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
              <span>{item.icon}</span> {item.label}
              {item.to === '/notifications' && unread > 0 && (
                <span className="nav-badge">{unread}</span>
              )}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="layout-main">
        <header className="header">
          <button className="menu-toggle btn btn-secondary btn-sm" onClick={() => setSidebarOpen(!sidebarOpen)}>☰</button>
          <div className="header-right">
            <span className="user-name">{user?.full_name}</span>
            <button className="btn btn-secondary btn-sm" onClick={handleLogout}>Logout</button>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
      {sidebarOpen && <div className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} />}
    </div>
  );
}
