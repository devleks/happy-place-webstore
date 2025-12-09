import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import '../../styles/AdminDashboard.css';

const AdminHeader = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showDropdown, setShowDropdown] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="admin-header">
      <div className="header-left">
        <h1 className="page-title">Admin Dashboard</h1>
      </div>

      <div className="header-right">
        <div className="user-menu">
          <button
            className="user-menu-button"
            onClick={() => setShowDropdown(!showDropdown)}
          >
            <div className="user-avatar">
              {user?.name?.charAt(0).toUpperCase() || 'A'}
            </div>
            <div className="user-info">
              <span className="user-name">{user?.name || 'Admin'}</span>
              <span className="user-role">{user?.role || 'admin'}</span>
            </div>
            <span className="dropdown-arrow">▼</span>
          </button>

          {showDropdown && (
            <div className="user-dropdown">
              <button onClick={() => navigate('/admin/profile')} className="dropdown-item">
                Profile
              </button>
              <button onClick={() => navigate('/admin/settings')} className="dropdown-item">
                Settings
              </button>
              <div className="dropdown-divider"></div>
              <button onClick={handleLogout} className="dropdown-item logout">
                Logout
              </button>
            </div>
          )}
        </div>
      </div>

      {showDropdown && (
        <div
          className="dropdown-backdrop"
          onClick={() => setShowDropdown(false)}
        ></div>
      )}
    </header>
  );
};

export default AdminHeader;
