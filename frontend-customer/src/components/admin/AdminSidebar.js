import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import '../../styles/AdminDashboard.css';

const AdminSidebar = () => {
  const { user } = useAuth();

  const menuItems = [
    {
      path: '/admin/dashboard',
      icon: '📊',
      label: 'Dashboard',
      roles: ['admin', 'manager'],
    },
    {
      path: '/admin/inventory',
      icon: '📦',
      label: 'Inventory',
      roles: ['admin', 'manager'],
    },
    {
      path: '/admin/orders',
      icon: '🛒',
      label: 'Orders',
      roles: ['admin', 'manager'],
    },
    {
      path: '/admin/customers',
      icon: '👥',
      label: 'Customers',
      roles: ['admin', 'manager'],
    },
    {
      path: '/admin/employees',
      icon: '👤',
      label: 'Employees',
      roles: ['admin'],
    },
    {
      path: '/admin/promotions',
      icon: '🎁',
      label: 'Promotions',
      roles: ['admin', 'manager'],
    },
    {
      path: '/admin/reports',
      icon: '📈',
      label: 'Reports',
      roles: ['admin', 'manager'],
    },
    {
      path: '/admin/settings',
      icon: '⚙️',
      label: 'Settings',
      roles: ['admin'],
    },
  ];

  const filteredMenuItems = menuItems.filter((item) =>
    item.roles.includes(user?.role)
  );

  return (
    <div className="admin-sidebar">
      <div className="sidebar-header">
        <h2>Happy Place</h2>
        <p className="sidebar-subtitle">Admin Panel</p>
      </div>

      <nav className="sidebar-nav">
        {filteredMenuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'active' : ''}`
            }
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <NavLink to="/" className="nav-item">
          <span className="nav-icon">🏠</span>
          <span className="nav-label">Back to Store</span>
        </NavLink>
      </div>
    </div>
  );
};

export default AdminSidebar;
