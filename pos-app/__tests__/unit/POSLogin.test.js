/**
 * POSLogin Component Tests
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import POSLogin from '../../src/pages/POS/POSLogin';

// Mock electron API
const mockElectronAPI = {
  auth: {
    login: jest.fn(),
    validateSession: jest.fn()
  }
};

window.electron = mockElectronAPI;

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate
}));

describe('POSLogin Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  const renderLogin = (props = {}) => {
    return render(
      <BrowserRouter>
        <POSLogin {...props} />
      </BrowserRouter>
    );
  };

  it('should render login form', () => {
    renderLogin();

    expect(screen.getByText('Happy Place POS')).toBeInTheDocument();
    expect(screen.getByText('Employee Login')).toBeInTheDocument();
    expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login to pos/i })).toBeInTheDocument();
  });

  it('should show online status indicator', () => {
    renderLogin();

    const statusBanner = screen.getByText(/online.*auto-sync enabled/i);
    expect(statusBanner).toBeInTheDocument();
  });

  it('should handle successful login', async () => {
    const mockOnLogin = jest.fn();
    mockElectronAPI.auth.login.mockResolvedValueOnce({
      success: true,
      employee: {
        id: 1,
        email: 'test@example.com',
        full_name: 'Test User',
        role: 'cashier'
      },
      session: {
        token: 'test-token',
        expires_at: '2025-12-11T10:00:00Z'
      }
    });

    renderLogin({ onLogin: mockOnLogin });

    // Fill in form
    fireEvent.change(screen.getByLabelText('Email Address'), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' }
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /login to pos/i }));

    await waitFor(() => {
      expect(mockElectronAPI.auth.login).toHaveBeenCalledWith('test@example.com', 'password123');
      expect(localStorage.getItem('session_token')).toBe('test-token');
      expect(mockOnLogin).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('should handle failed login', async () => {
    mockElectronAPI.auth.login.mockResolvedValueOnce({
      success: false,
      error: 'Invalid credentials'
    });

    renderLogin();

    // Fill in form
    fireEvent.change(screen.getByLabelText('Email Address'), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'wrongpassword' }
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /login to pos/i }));

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
      expect(localStorage.getItem('session_token')).toBeNull();
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  it('should clear error when user starts typing', async () => {
    mockElectronAPI.auth.login.mockResolvedValueOnce({
      success: false,
      error: 'Invalid credentials'
    });

    renderLogin();

    // Trigger error
    fireEvent.change(screen.getByLabelText('Email Address'), {
      target: { value: 'test@example.com' }
    });
    fireEvent.click(screen.getByRole('button', { name: /login to pos/i }));

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });

    // Start typing
    fireEvent.change(screen.getByLabelText('Email Address'), {
      target: { value: 'test2@example.com' }
    });

    expect(screen.queryByText('Invalid credentials')).not.toBeInTheDocument();
  });

  it('should check for existing valid session on mount', async () => {
    localStorage.setItem('session_token', 'existing-token');
    
    mockElectronAPI.auth.validateSession.mockResolvedValueOnce({
      valid: true,
      session: {
        id: 1,
        employee_id: 1,
        email: 'test@example.com',
        full_name: 'Test User',
        role: 'cashier'
      }
    });

    const mockOnLogin = jest.fn();
    renderLogin({ onLogin: mockOnLogin });

    await waitFor(() => {
      expect(mockElectronAPI.auth.validateSession).toHaveBeenCalledWith('existing-token');
      expect(mockOnLogin).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('should clear invalid session on mount', async () => {
    localStorage.setItem('session_token', 'invalid-token');
    localStorage.setItem('employee_info', JSON.stringify({ id: 1 }));
    
    mockElectronAPI.auth.validateSession.mockResolvedValueOnce({
      valid: false,
      reason: 'session_expired'
    });

    renderLogin();

    await waitFor(() => {
      expect(localStorage.getItem('session_token')).toBeNull();
      expect(localStorage.getItem('employee_info')).toBeNull();
    });
  });

  it('should show loading state during login', async () => {
    mockElectronAPI.auth.login.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
    );

    renderLogin();

    fireEvent.change(screen.getByLabelText('Email Address'), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' }
    });

    const loginButton = screen.getByRole('button', { name: /login to pos/i });
    fireEvent.click(loginButton);

    // Button should be disabled during loading
    expect(loginButton).toBeDisabled();

    await waitFor(() => {
      expect(loginButton).not.toBeDisabled();
    });
  });
});
