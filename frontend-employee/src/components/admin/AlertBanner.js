import React from 'react';
import '../../styles/AdminDashboard.css';

const AlertBanner = ({ alert }) => {
  const getAlertClass = (severity) => {
    switch (severity) {
      case 'critical':
        return 'alert-critical';
      case 'warning':
        return 'alert-warning';
      case 'info':
        return 'alert-info';
      default:
        return 'alert-info';
    }
  };

  const getAlertIcon = (severity) => {
    switch (severity) {
      case 'critical':
        return '🚨';
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return 'ℹ️';
    }
  };

  return (
    <div className={`alert-banner ${getAlertClass(alert.severity)}`}>
      <span className="alert-icon">{getAlertIcon(alert.severity)}</span>
      <div className="alert-content">
        <div className="alert-title">{alert.title}</div>
        <div className="alert-message">{alert.message}</div>
      </div>
      {alert.action && (
        <button className="alert-action" onClick={alert.action.onClick}>
          {alert.action.label}
        </button>
      )}
    </div>
  );
};

export default AlertBanner;
