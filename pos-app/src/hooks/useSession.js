/**
 * useSession Hook
 * Automatic session validation and management
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/electronAPI';

export function useSession() {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    validateSession();

    // Validate session every minute
    const interval = setInterval(validateSession, 60000);

    return () => clearInterval(interval);
  }, []);

  const validateSession = async () => {
    const sessionToken = localStorage.getItem('session_token');
    
    if (!sessionToken) {
      setLoading(false);
      navigate('/login');
      return;
    }

    try {
      const result = await api.auth.validateSession(sessionToken);
      
      if (result.valid) {
        setSession(result.session);
      } else {
        // Session invalid - logout
        handleSessionExpired(result.reason, result.message);
      }
    } catch (error) {
      console.error('Session validation error:', error);
      handleSessionExpired('validation_error');
    } finally {
      setLoading(false);
    }
  };

  const handleSessionExpired = (reason, customMessage) => {
    localStorage.removeItem('session_token');
    localStorage.removeItem('employee_info');
    localStorage.removeItem('current_shift');
    setSession(null);
    
    const messages = {
      session_expired: 'Your session has expired. Please login again.',
      inactivity_timeout: 'You were logged out due to inactivity (30 minutes).',
      employee_deactivated: 'Your account has been deactivated. Please contact your manager.',
      password_changed: customMessage || 'Your password was changed. Please login again with your new password.',
      validation_error: 'Session validation failed. Please login again.'
    };
    
    alert(messages[reason] || 'Please login again.');
    navigate('/login');
  };

  const logout = async () => {
    const sessionToken = localStorage.getItem('session_token');
    if (sessionToken) {
      await api.auth.logout(sessionToken);
    }
    
    localStorage.removeItem('session_token');
    localStorage.removeItem('employee_info');
    localStorage.removeItem('current_shift');
    setSession(null);
    navigate('/login');
  };

  return { session, loading, logout, validateSession };
}
