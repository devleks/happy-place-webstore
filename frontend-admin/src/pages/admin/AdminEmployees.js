import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { adminAPI } from '../../services/adminAPI';
import DataTable from '../../components/admin/DataTable';
import StatusBadge from '../../components/admin/StatusBadge';
import '../../styles/AdminDashboard.css';

const AdminEmployees = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState('');
  const [currentEmployee, setCurrentEmployee] = useState(null);
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'cashier',
    hourly_rate: '',
    phone: '',
  });

  useEffect(() => {
    // Only admins can manage employees
    if (!user || user.role !== 'admin') {
      navigate('/admin/login');
      return;
    }

    fetchEmployees();
  }, [user, navigate]);

  const fetchEmployees = async () => {
    try {
      setLoading(true);
      const data = await adminAPI.getEmployees();
      setEmployees(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load employees');
      console.error('Employees error:', err);
    } finally {
      setLoading(false);
    }
  };

  const openAddModal = () => {
    setFormData({
      full_name: '',
      email: '',
      password: '',
      role: 'cashier',
      hourly_rate: '',
      phone: '',
    });
    setCurrentEmployee(null);
    setModalType('add');
    setShowModal(true);
  };

  const openEditModal = (employee) => {
    setFormData({
      full_name: employee.full_name,
      email: employee.email,
      password: '',
      role: employee.role,
      hourly_rate: employee.hourly_rate || '',
      phone: employee.phone || '',
    });
    setCurrentEmployee(employee);
    setModalType('edit');
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      if (modalType === 'add') {
        await adminAPI.createEmployee(formData);
        alert('Employee created successfully');
      } else if (modalType === 'edit') {
        await adminAPI.updateEmployee(currentEmployee.id, formData);
        alert('Employee updated successfully');
      }
      setShowModal(false);
      fetchEmployees();
    } catch (err) {
      alert(err.message || 'Failed to save employee');
    }
  };

  const handleDelete = async (employeeId) => {
    if (!window.confirm('Are you sure you want to delete this employee?')) return;

    try {
      await adminAPI.deleteEmployee(employeeId);
      fetchEmployees();
      alert('Employee deleted successfully');
    } catch (err) {
      alert(err.message || 'Failed to delete employee');
    }
  };

  const handleDeactivate = async (employeeId) => {
    try {
      await adminAPI.deactivateEmployee(employeeId);
      fetchEmployees();
      alert('Employee deactivated successfully');
    } catch (err) {
      alert(err.message || 'Failed to deactivate employee');
    }
  };

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'name', label: 'Name' },
    { key: 'email', label: 'Email' },
    {
      key: 'role',
      label: 'Role',
      render: (employee) => (
        <span className="role-badge role-{employee.role}">{employee.role}</span>
      ),
    },
    {
      key: 'hourly_rate',
      label: 'Hourly Rate',
      render: (employee) => employee.hourly_rate ? `$${employee.hourly_rate.toFixed(2)}` : 'N/A',
    },
    {
      key: 'created_at',
      label: 'Hired',
      render: (employee) => new Date(employee.created_at).toLocaleDateString(),
    },
    {
      key: 'is_active',
      label: 'Status',
      render: (employee) => (
        <StatusBadge status={employee.is_active ? 'active' : 'inactive'} />
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (employee) => (
        <div className="action-buttons">
          <button
            className="btn-icon"
            onClick={() => openEditModal(employee)}
            title="Edit Employee"
          >
            ✏️
          </button>
          {employee.is_active && (
            <button
              className="btn-icon"
              onClick={() => handleDeactivate(employee.id)}
              title="Deactivate"
            >
              🔒
            </button>
          )}
          <button
            className="btn-icon"
            onClick={() => handleDelete(employee.id)}
            title="Delete Employee"
          >
            🗑️
          </button>
        </div>
      ),
    },
  ];

  if (loading) {
    return <div className="loading-spinner">Loading employees...</div>;
  }

  return (
    <div className="admin-employees">
      <div className="page-header">
        <h1>Employee Management</h1>
        <button className="btn-primary" onClick={openAddModal}>
          Add Employee
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)} className="close-btn">×</button>
        </div>
      )}

      {/* Summary Stats */}
      <div className="stats-row">
        <div className="stat-card">
          <span className="stat-label">Total Employees</span>
          <span className="stat-value">{employees.length}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Active</span>
          <span className="stat-value">
            {employees.filter((e) => e.is_active).length}
          </span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Managers</span>
          <span className="stat-value">
            {employees.filter((e) => e.role === 'manager').length}
          </span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Cashiers</span>
          <span className="stat-value">
            {employees.filter((e) => e.role === 'cashier').length}
          </span>
        </div>
      </div>

      {/* Data Table */}
      <DataTable
        columns={columns}
        data={employees}
        keyField="id"
        emptyMessage="No employees found"
      />

      {/* Add/Edit Employee Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{modalType === 'add' ? 'Add Employee' : 'Edit Employee'}</h2>
              <button onClick={() => setShowModal(false)} className="close-btn">
                ×
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Name *</label>
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Email *</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>
                    Password {modalType === 'add' ? '*' : '(leave blank to keep current)'}
                  </label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="form-input"
                    required={modalType === 'add'}
                  />
                </div>

                <div className="form-group">
                  <label>Role *</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="form-input"
                    required
                  >
                    <option value="cashier">Cashier</option>
                    <option value="manager">Manager</option>
                    <option value="admin">Admin</option>
                    <option value="packer">Packer</option>
                    <option value="shipper">Shipper</option>
                    <option value="staff">Staff</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Hourly Rate</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.hourly_rate}
                    onChange={(e) =>
                      setFormData({ ...formData, hourly_rate: e.target.value })
                    }
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label>Phone</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="form-input"
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {modalType === 'add' ? 'Add Employee' : 'Update Employee'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminEmployees;
