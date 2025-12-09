import React from 'react';
import '../../styles/AdminDashboard.css';

const MetricCard = ({ title, value, icon, trend, subtitle, alert, onClick }) => {
  return (
    <div
      className={`metric-card ${alert ? 'alert' : ''} ${onClick ? 'clickable' : ''}`}
      onClick={onClick}
    >
      <div className="metric-header">
        <span className="metric-title">{title}</span>
        {icon && <span className="metric-icon">{icon}</span>}
      </div>

      <div className="metric-value">{value}</div>

      {subtitle && <div className="metric-subtitle">{subtitle}</div>}

      {trend && (
        <div className={`metric-trend ${trend > 0 ? 'positive' : 'negative'}`}>
          <span className="trend-arrow">{trend > 0 ? '↑' : '↓'}</span>
          <span className="trend-value">{Math.abs(trend)}%</span>
          <span className="trend-label">vs last period</span>
        </div>
      )}
    </div>
  );
};

export default MetricCard;
