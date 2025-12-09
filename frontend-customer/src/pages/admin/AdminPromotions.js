import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { adminAPI } from '../../services/adminAPI';
import DataTable from '../../components/admin/DataTable';
import StatusBadge from '../../components/admin/StatusBadge';
import '../../styles/AdminDashboard.css';

const AdminPromotions = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [promotions, setPromotions] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState('');
  const [currentPromotion, setCurrentPromotion] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    discount_type: 'percentage',
    discount_value: '',
    start_date: '',
    end_date: '',
    min_purchase_amount: '',
    max_uses: '',
    is_active: true,
  });

  useEffect(() => {
    if (!user || (user.role !== 'admin' && user.role !== 'manager')) {
      navigate('/login');
      return;
    }

    fetchPromotions();
  }, [user, navigate]);

  const fetchPromotions = async () => {
    try {
      setLoading(true);
      const data = await adminAPI.getPromotions();
      setPromotions(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load promotions');
      console.error('Promotions error:', err);
    } finally {
      setLoading(false);
    }
  };

  const openAddModal = () => {
    setFormData({
      name: '',
      code: '',
      discount_type: 'percentage',
      discount_value: '',
      start_date: '',
      end_date: '',
      min_purchase_amount: '',
      max_uses: '',
      is_active: true,
    });
    setCurrentPromotion(null);
    setModalType('add');
    setShowModal(true);
  };

  const openEditModal = (promotion) => {
    setFormData({
      name: promotion.name,
      code: promotion.code,
      discount_type: promotion.discount_type,
      discount_value: promotion.discount_value,
      start_date: promotion.start_date?.split('T')[0] || '',
      end_date: promotion.end_date?.split('T')[0] || '',
      min_purchase_amount: promotion.min_purchase_amount || '',
      max_uses: promotion.max_uses || '',
      is_active: promotion.is_active,
    });
    setCurrentPromotion(promotion);
    setModalType('edit');
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      if (modalType === 'add') {
        await adminAPI.createPromotion(formData);
        alert('Promotion created successfully');
      } else if (modalType === 'edit') {
        await adminAPI.updatePromotion(currentPromotion.id, formData);
        alert('Promotion updated successfully');
      }
      setShowModal(false);
      fetchPromotions();
    } catch (err) {
      alert(err.message || 'Failed to save promotion');
    }
  };

  const handleToggleActive = async (promotionId, isActive) => {
    try {
      await adminAPI.togglePromotion(promotionId, !isActive);
      fetchPromotions();
    } catch (err) {
      alert(err.message || 'Failed to toggle promotion');
    }
  };

  const handleDelete = async (promotionId) => {
    if (!window.confirm('Are you sure you want to delete this promotion?')) return;

    try {
      await adminAPI.deletePromotion(promotionId);
      fetchPromotions();
      alert('Promotion deleted successfully');
    } catch (err) {
      alert(err.message || 'Failed to delete promotion');
    }
  };

  const isExpired = (endDate) => {
    return new Date(endDate) < new Date();
  };

  const columns = [
    { key: 'code', label: 'Code' },
    { key: 'name', label: 'Name' },
    {
      key: 'discount',
      label: 'Discount',
      render: (promo) =>
        promo.discount_type === 'percentage'
          ? `${promo.discount_value}%`
          : `$${promo.discount_value}`,
    },
    {
      key: 'start_date',
      label: 'Start Date',
      render: (promo) =>
        promo.start_date ? new Date(promo.start_date).toLocaleDateString() : 'N/A',
    },
    {
      key: 'end_date',
      label: 'End Date',
      render: (promo) =>
        promo.end_date ? new Date(promo.end_date).toLocaleDateString() : 'N/A',
    },
    {
      key: 'uses',
      label: 'Uses',
      render: (promo) =>
        `${promo.current_uses || 0}${promo.max_uses ? ` / ${promo.max_uses}` : ''}`,
    },
    {
      key: 'status',
      label: 'Status',
      render: (promo) => {
        if (!promo.is_active) return <StatusBadge status="inactive" />;
        if (isExpired(promo.end_date)) return <StatusBadge status="expired" />;
        return <StatusBadge status="active" />;
      },
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (promo) => (
        <div className="action-buttons">
          <button
            className="btn-icon"
            onClick={() => openEditModal(promo)}
            title="Edit Promotion"
          >
            ✏️
          </button>
          <button
            className="btn-icon"
            onClick={() => handleToggleActive(promo.id, promo.is_active)}
            title={promo.is_active ? 'Deactivate' : 'Activate'}
          >
            {promo.is_active ? '🔒' : '🔓'}
          </button>
          <button
            className="btn-icon"
            onClick={() => handleDelete(promo.id)}
            title="Delete Promotion"
          >
            🗑️
          </button>
        </div>
      ),
    },
  ];

  if (loading) {
    return <div className="loading-spinner">Loading promotions...</div>;
  }

  return (
    <div className="admin-promotions">
      <div className="page-header">
        <h1>Promotion Management</h1>
        <button className="btn-primary" onClick={openAddModal}>
          Create Promotion
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
          <span className="stat-label">Total Promotions</span>
          <span className="stat-value">{promotions.length}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Active</span>
          <span className="stat-value">
            {promotions.filter((p) => p.is_active && !isExpired(p.end_date)).length}
          </span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Expired</span>
          <span className="stat-value">
            {promotions.filter((p) => isExpired(p.end_date)).length}
          </span>
        </div>
      </div>

      {/* Data Table */}
      <DataTable
        columns={columns}
        data={promotions}
        keyField="id"
        emptyMessage="No promotions found"
      />

      {/* Add/Edit Promotion Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{modalType === 'add' ? 'Create Promotion' : 'Edit Promotion'}</h2>
              <button onClick={() => setShowModal(false)} className="close-btn">
                ×
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Promotion Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Promotion Code *</label>
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) =>
                      setFormData({ ...formData, code: e.target.value.toUpperCase() })
                    }
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Discount Type *</label>
                    <select
                      value={formData.discount_type}
                      onChange={(e) =>
                        setFormData({ ...formData, discount_type: e.target.value })
                      }
                      className="form-input"
                      required
                    >
                      <option value="percentage">Percentage</option>
                      <option value="fixed">Fixed Amount</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Discount Value *</label>
                    <input
                      type="number"
                      step="0.01"
                      value={formData.discount_value}
                      onChange={(e) =>
                        setFormData({ ...formData, discount_value: e.target.value })
                      }
                      className="form-input"
                      required
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Start Date</label>
                    <input
                      type="date"
                      value={formData.start_date}
                      onChange={(e) =>
                        setFormData({ ...formData, start_date: e.target.value })
                      }
                      className="form-input"
                    />
                  </div>

                  <div className="form-group">
                    <label>End Date</label>
                    <input
                      type="date"
                      value={formData.end_date}
                      onChange={(e) =>
                        setFormData({ ...formData, end_date: e.target.value })
                      }
                      className="form-input"
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Minimum Purchase Amount</label>
                    <input
                      type="number"
                      step="0.01"
                      value={formData.min_purchase_amount}
                      onChange={(e) =>
                        setFormData({ ...formData, min_purchase_amount: e.target.value })
                      }
                      className="form-input"
                    />
                  </div>

                  <div className="form-group">
                    <label>Max Uses</label>
                    <input
                      type="number"
                      value={formData.max_uses}
                      onChange={(e) =>
                        setFormData({ ...formData, max_uses: e.target.value })
                      }
                      className="form-input"
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) =>
                        setFormData({ ...formData, is_active: e.target.checked })
                      }
                    />
                    <span>Active</span>
                  </label>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {modalType === 'add' ? 'Create Promotion' : 'Update Promotion'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPromotions;
