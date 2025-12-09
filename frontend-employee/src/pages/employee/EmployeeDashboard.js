import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const EmployeeDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    // Redirect based on role
    switch (user.role) {
      case 'packer':
        navigate('/packing');
        break;
      case 'shipper':
        navigate('/shipping');
        break;
      case 'manager':
      case 'admin':
        // Managers/admins can choose
        navigate('/packing');
        break;
      default:
        navigate('/login');
    }
  }, [user, navigate]);

  return (
    <div className="loading-container">
      <div className="loading-spinner">Redirecting to your dashboard...</div>
    </div>
  );
};

export default EmployeeDashboard;
