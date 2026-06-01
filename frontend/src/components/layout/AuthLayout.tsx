import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Home, MessageSquare, FileText, Settings, LogOut, Menu, X, Bot } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import styles from './AuthLayout.module.css';

export const AuthLayout: React.FC = () => {
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const toggleSidebar = () => setIsMobileOpen(!isMobileOpen);

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: <Home size={20} /> },
    { name: 'Chats', path: '/chat', icon: <MessageSquare size={20} /> },
    { name: 'Documents', path: '/documents', icon: <FileText size={20} /> },
    { name: 'Settings', path: '/settings', icon: <Settings size={20} /> },
  ];

  return (
    <div className={styles.layoutContainer}>
      {/* Mobile Header */}
      <div className={styles.mobileHeader}>
        <div className={styles.logo}>
          <Bot size={24} />
          <span>Self-Healing RAG</span>
        </div>
        <button className={styles.menuBtn} onClick={toggleSidebar}>
          {isMobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Sidebar */}
      <aside className={`${styles.sidebar} ${isMobileOpen ? styles.mobileOpen : ''}`}>
        <div className={styles.sidebarLogo}>
          <Bot size={28} />
          <span>Self-Healing RAG</span>
        </div>
        
        <nav className={styles.nav}>
          {navItems.map((item) => (
            <NavLink 
              key={item.name} 
              to={item.path} 
              className={({ isActive }) => `${styles.navItem} ${isActive ? styles.active : ''}`}
              onClick={() => setIsMobileOpen(false)}
            >
              {item.icon}
              <span>{item.name}</span>
            </NavLink>
          ))}
        </nav>

        <div className={styles.sidebarFooter}>
          <div className={styles.userInfo}>
            <div className={styles.avatar}>
              {user?.avatarId ? (
                <img src={`https://rag-based-pdf-llm-1.onrender.com/users/avatar/${user.avatarId}`} alt="Avatar" />
              ) : user?.profilePicture ? (
                <img src={user.profilePicture} alt="Avatar" />
              ) : (
                <UserAvatarFallback name={user?.name || 'U'} />
              )}
            </div>
            <div className={styles.userDetails}>
              <span className={styles.userName}>{user?.name}</span>
            </div>
          </div>
          <button className={styles.logoutBtn} onClick={logout}>
            <LogOut size={20} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className={styles.mainContent}>
        <Outlet />
      </main>

      {/* Overlay for mobile */}
      {isMobileOpen && <div className={styles.overlay} onClick={toggleSidebar}></div>}
    </div>
  );
};

const UserAvatarFallback = ({ name }: { name: string }) => (
  <div style={{
    width: '100%', height: '100%', backgroundColor: 'var(--primary-color)',
    color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontWeight: 'bold', fontSize: '1.2rem'
  }}>
    {name.charAt(0).toUpperCase()}
  </div>
);
