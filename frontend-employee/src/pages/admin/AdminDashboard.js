import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { adminAPI } from '../../services/adminAPI';
import MetricCard from '../../components/admin/MetricCard';
import AlertBanner from '../../components/admin/AlertBanner';
import '../../styles/AdminDashboard.css';

const AdminDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [metrics, setMetrics] = useState({
    totalSales: 0,
    totalOrders: 0,
    totalCustomers: 0,
    lowStockItems: 0,
  });
  const [recentActivity, setRecentActivity] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [salesTrend, setSalesTrend] = useState([]);

  useEffect(() => {
    // Check if user has admin/manager role
    if (!user || (user.role !== 'admin' && user.role !== 'manager')) {
      navigate('/login');
      return;
    }

    fetchDashboardData();

    // Refresh data every 5 minutes
    const interval = setInterval(() => {
      fetchDashboardData();
    }, 300000);

    return () => clearInterval(interval);
  }, [user, navigate]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [metricsData, activityData, alertsData] = await Promise.all([
        adminAPI.getMetrics(),
        adminAPI.getRecentActivity(),
        adminAPI.getAlerts(),
      ]);

      setMetrics(metricsData);
      setRecentActivity(activityData);
      setAlerts(alertsData);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAction = (action) => {
    switch (action) {
      case 'addProduct':
        navigate('/admin/inventory');
        break;
      case 'viewOrders':
        navigate('/admin/orders');
        break;
      case 'manageCustomers':
        navigate('/admin/customers');
        break;
      case 'viewReports':
        navigate('/admin/reports');
        break;
      default:
        break;
    }
  };

  if (loading) {
    return (
      <div className="admin-dashboard">
        <div className="loading-spinner">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <button onClick={() => fetchDashboardData()} className="refresh-btn">
          Refresh
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)} className="close-btn">×</button>
        </div>
      )}

      {/* Alerts Section */}
      {alerts.length > 0 && (
        <div className="alerts-section">
          <h2>Critical Alerts</h2>
          <div className="alerts-list">
            {alerts.map((alert) => (
              <AlertBanner key={alert.id} alert={alert} />
            ))}
          </div>
        </div>
      )}

      {/* Metrics Cards */}
      <div className="metrics-grid">
        <MetricCard
          title="Total Sales"
          value={`$${metrics.totalSales?.toFixed(2) || '0.00'}`}
          icon="💰"
          trend={metrics.salesTrend}
          onClick={() => navigate('/admin/reports')}
        />
        <MetricCard
          title="Total Orders"
          value={metrics.totalOrders || 0}
          icon="📦"
          subtitle="This month"
          onClick={() => navigate('/admin/orders')}
        />
        <MetricCard
          title="Total Customers"
          value={metrics.totalCustomers || 0}
          icon="👥"
          subtitle="Active users"
          onClick={() => navigate('/admin/customers')}
        />
        <MetricCard
          title="Low Stock Items"
          value={metrics.lowStockItems || 0}
          icon="⚠️"
          alert={metrics.lowStockItems > 0}
          onClick={() => navigate('/admin/inventory')}
        />
      </div>

      {/* Quick Actions */}
      <div className="quick-actions-section">
        <h2>Quick Actions</h2>
        <div className="quick-actions-grid">
          <button
            className="quick-action-btn"
            onClick={() => handleQuickAction('addProduct')}
          >
            <span className="action-icon">➕</span>
            <span>Add Product</span>
          </button>
          <button
            className="quick-action-btn"
            onClick={() => handleQuickAction('viewOrders')}
          >
            <span className="action-icon">📋</span>
            <span>View Orders</span>
          </button>
          <button
            className="quick-action-btn"
            onClick={() => handleQuickAction('manageCustomers')}
          >
            <span className="action-icon">👤</span>
            <span>Manage Customers</span>
          </button>
          <button
            className="quick-action-btn"
            onClick={() => handleQuickAction('viewReports')}
          >
            <span className="action-icon">📊</span>
            <span>View Reports</span>
          </button>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="recent-activity-section">
        <h2>Recent Activity</h2>
        <div className="activity-list">
          {recentActivity.length > 0 ? (
            recentActivity.map((activity) => (
              <div key={activity.id} className="activity-item">
                <div className="activity-icon">{activity.icon || '•'}</div>
                <div className="activity-content">
                  <div className="activity-description">{activity.description}</div>
                  <div className="activity-time">
                    {new Date(activity.timestamp).toLocaleString()}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <p className="no-data">No recent activity</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
