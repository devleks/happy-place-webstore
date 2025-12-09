import React from 'react';
import '../../styles/AdminDashboard.css';

const StatusBadge = ({ status }) => {
  const getStatusClass = (status) => {
    switch (status?.toLowerCase()) {
      // Order statuses
      case 'pending':
        return 'status-pending';
      case 'processing':
        return 'status-processing';
      case 'shipped':
        return 'status-shipped';
      case 'delivered':
        return 'status-delivered';
      case 'cancelled':
        return 'status-cancelled';

      // Payment statuses
      case 'paid':
        return 'status-paid';
      case 'failed':
        return 'status-failed';
      case 'refunded':
        return 'status-refunded';

      // Stock statuses
      case 'in-stock':
        return 'status-in-stock';
      case 'low-stock':
        return 'status-low-stock';
      case 'out-of-stock':
        return 'status-out-of-stock';

      // General statuses
      case 'active':
        return 'status-active';
      case 'inactive':
        return 'status-inactive';
      case 'expired':
        return 'status-expired';

      default:
        return 'status-default';
    }
  };

  const getStatusLabel = (status) => {
    if (!status) return 'Unknown';

    // Format status: replace hyphens/underscores with spaces and capitalize
    return status
      .replace(/[-_]/g, ' ')
      .split(' ')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  return (
    <span className={`status-badge ${getStatusClass(status)}`}>
      {getStatusLabel(status)}
    </span>
  );
};

export default StatusBadge;
