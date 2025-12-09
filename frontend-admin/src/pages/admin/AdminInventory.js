import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { adminAPI } from '../../services/adminAPI';
import DataTable from '../../components/admin/DataTable';
import StatusBadge from '../../components/admin/StatusBadge';
import '../../styles/AdminDashboard.css';

const AdminInventory = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [stockFilter, setStockFilter] = useState('all');
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState('');
  const [currentProduct, setCurrentProduct] = useState(null);
  const [stockAdjustment, setStockAdjustment] = useState({
    quantity: 0,
    reason: '',
  });

  useEffect(() => {
    if (!user || (user.role !== 'admin' && user.role !== 'manager')) {
      navigate('/login');
      return;
    }

    fetchInventory();
  }, [user, navigate]);

  useEffect(() => {
    filterProducts();
  }, [searchTerm, categoryFilter, stockFilter, products]);

  const fetchInventory = async () => {
    try {
      setLoading(true);
      const data = await adminAPI.getInventory();
      // API returns {items: [...], total, page, per_page, total_pages}
      setProducts(data.items || data || []);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load inventory');
      console.error('Inventory error:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterProducts = () => {
    let filtered = [...products];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          p.sku?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Category filter
    if (categoryFilter !== 'all') {
      filtered = filtered.filter((p) => p.category === categoryFilter);
    }

    // Stock filter
    if (stockFilter === 'low') {
      filtered = filtered.filter((p) => p.stock_quantity <= p.low_stock_threshold);
    } else if (stockFilter === 'out') {
      filtered = filtered.filter((p) => p.stock_quantity === 0);
    }

    setFilteredProducts(filtered);
  };

  const handleStockAdjustment = async () => {
    if (!currentProduct) return;

    try {
      await adminAPI.updateStock(currentProduct.variant_id, {
        quantity: stockAdjustment.quantity,
        reason: stockAdjustment.reason,
      });
      setShowModal(false);
      setStockAdjustment({ quantity: 0, reason: '' });
      fetchInventory();
      alert('Stock updated successfully');
    } catch (err) {
      alert(err.message || 'Failed to update stock');
    }
  };

  const handleBulkAction = async (action) => {
    if (selectedProducts.length === 0) {
      alert('Please select products first');
      return;
    }

    try {
      if (action === 'delete') {
        if (!window.confirm(`Delete ${selectedProducts.length} products?`)) return;
        await adminAPI.bulkDeleteProducts(selectedProducts);
      } else if (action === 'export') {
        await adminAPI.exportInventory(selectedProducts);
      }
      setSelectedProducts([]);
      fetchInventory();
    } catch (err) {
      alert(err.message || 'Bulk action failed');
    }
  };

  const openStockModal = (product) => {
    setCurrentProduct(product);
    setModalType('stock');
    setShowModal(true);
  };

  const openDetailsModal = (product) => {
    setCurrentProduct(product);
    setModalType('details');
    setShowModal(true);
  };

  const getStockStatus = (product) => {
    if (product.stock_quantity === 0) return 'out-of-stock';
    if (product.stock_quantity <= product.low_stock_threshold) return 'low-stock';
    return 'in-stock';
  };

  const columns = [
    {
      key: 'select',
      label: '',
      render: (product) => (
        <input
          type="checkbox"
          checked={selectedProducts.includes(product.variant_id)}
          onChange={(e) => {
            if (e.target.checked) {
              setSelectedProducts([...selectedProducts, product.variant_id]);
            } else {
              setSelectedProducts(selectedProducts.filter((id) => id !== product.variant_id));
            }
          }}
        />
      ),
    },
    {
      key: 'image',
      label: 'Image',
      render: (product) => (
        <div className="product-image-cell">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.product_name}
              className="product-thumbnail"
              style={{ width: '50px', height: '50px', objectFit: 'cover', borderRadius: '4px' }}
            />
          ) : (
            <div className="no-image-placeholder" style={{ width: '50px', height: '50px', backgroundColor: '#f0f0f0', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', color: '#999' }}>
              No Image
            </div>
          )}
        </div>
      ),
    },
    { key: 'sku', label: 'SKU' },
    { key: 'product_name', label: 'Product Name' },
    {
      key: 'variant_info',
      label: 'Size / Color',
      render: (product) => (
        <span>
          {product.size && <span style={{ padding: '2px 6px', background: '#e3f2fd', borderRadius: '3px', fontSize: '11px', marginRight: '5px' }}>{product.size}</span>}
          {product.color && <span style={{ padding: '2px 6px', background: '#f3e5f5', borderRadius: '3px', fontSize: '11px' }}>{product.color}</span>}
        </span>
      ),
    },
    { key: 'category', label: 'Category' },
    {
      key: 'price',
      label: 'Price',
      render: (product) => `$${product.price.toFixed(2)}`,
    },
    {
      key: 'stock_quantity',
      label: 'Stock',
      render: (product) => (
        <div className="stock-cell">
          <span>{product.stock_quantity}</span>
          <StatusBadge status={getStockStatus(product)} />
        </div>
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (product) => (
        <div className="action-buttons">
          <button
            className="btn-icon"
            onClick={() => openStockModal(product)}
            title="Adjust Stock"
          >
            📦
          </button>
          <button
            className="btn-icon"
            onClick={() => openDetailsModal(product)}
            title="View Details"
          >
            👁️
          </button>
        </div>
      ),
    },
  ];

  if (loading) {
    return <div className="loading-spinner">Loading inventory...</div>;
  }

  return (
    <div className="admin-inventory">
      <div className="page-header">
        <h1>Inventory Management</h1>
        <button className="btn-primary" onClick={() => navigate('/inventory/add')}>
          Add Product
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)} className="close-btn">×</button>
        </div>
      )}

      {/* Filters */}
      <div className="filters-section">
        <input
          type="text"
          placeholder="Search by name or SKU..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />

        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="filter-select"
        >
          <option value="all">All Categories</option>
          <optgroup label="Women's Clothing">
            <option value="2">Tops</option>
            <option value="3">Bottoms</option>
            <option value="4">Dresses</option>
            <option value="5">Accessories</option>
          </optgroup>
          <optgroup label="Maternity Clothing">
            <option value="7">Maternity Tops</option>
            <option value="8">Maternity Bottoms</option>
            <option value="9">Maternity Dresses</option>
          </optgroup>
        </select>

        <select
          value={stockFilter}
          onChange={(e) => setStockFilter(e.target.value)}
          className="filter-select"
        >
          <option value="all">All Stock Levels</option>
          <option value="low">Low Stock</option>
          <option value="out">Out of Stock</option>
        </select>
      </div>

      {/* Bulk Actions */}
      {selectedProducts.length > 0 && (
        <div className="bulk-actions">
          <span>{selectedProducts.length} items selected</span>
          <button onClick={() => handleBulkAction('export')} className="btn-secondary">
            Export Selected
          </button>
          <button onClick={() => handleBulkAction('delete')} className="btn-danger">
            Delete Selected
          </button>
        </div>
      )}

      {/* Data Table */}
      <DataTable
        columns={columns}
        data={filteredProducts}
        keyField="variant_id"
        emptyMessage="No products found"
      />

      {/* Stock Adjustment Modal */}
      {showModal && modalType === 'stock' && currentProduct && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Adjust Stock - {currentProduct.product_name || currentProduct.name}</h2>
              <button onClick={() => setShowModal(false)} className="close-btn">
                ×
              </button>
            </div>
            <div className="modal-body">
              {currentProduct.image_url && (
                <div style={{ marginBottom: '15px', textAlign: 'center' }}>
                  <img
                    src={currentProduct.image_url}
                    alt={currentProduct.product_name || currentProduct.name}
                    style={{ width: '100px', height: '100px', objectFit: 'cover', borderRadius: '8px', border: '1px solid #ddd' }}
                  />
                </div>
              )}
              <p><strong>SKU:</strong> {currentProduct.sku}</p>
              <p><strong>Current Stock:</strong> {currentProduct.stock || currentProduct.stock_quantity}</p>
              {currentProduct.available !== undefined && <p><strong>Available:</strong> {currentProduct.available}</p>}
              <div className="form-group">
                <label>Adjustment Quantity:</label>
                <input
                  type="number"
                  value={stockAdjustment.quantity}
                  onChange={(e) =>
                    setStockAdjustment({
                      ...stockAdjustment,
                      quantity: parseInt(e.target.value) || 0,
                    })
                  }
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>Reason:</label>
                <textarea
                  value={stockAdjustment.reason}
                  onChange={(e) =>
                    setStockAdjustment({ ...stockAdjustment, reason: e.target.value })
                  }
                  className="form-input"
                  rows="3"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowModal(false)} className="btn-secondary">
                Cancel
              </button>
              <button onClick={handleStockAdjustment} className="btn-primary">
                Update Stock
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Product Details Modal */}
      {showModal && modalType === 'details' && currentProduct && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Product Details</h2>
              <button onClick={() => setShowModal(false)} className="close-btn">
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="product-details">
                {currentProduct.image_url && (
                  <div style={{ marginBottom: '20px', textAlign: 'center' }}>
                    <img
                      src={currentProduct.image_url}
                      alt={currentProduct.product_name || currentProduct.name}
                      style={{ maxWidth: '200px', maxHeight: '200px', objectFit: 'contain', borderRadius: '8px', border: '1px solid #ddd' }}
                    />
                  </div>
                )}
                <p><strong>SKU:</strong> {currentProduct.sku}</p>
                <p><strong>Name:</strong> {currentProduct.product_name || currentProduct.name}</p>
                <p><strong>Category:</strong> {currentProduct.category}</p>
                <p><strong>Price:</strong> ${currentProduct.price.toFixed(2)}</p>
                <p><strong>Stock:</strong> {currentProduct.stock || currentProduct.stock_quantity}</p>
                <p><strong>Available:</strong> {currentProduct.available || (currentProduct.stock_quantity - (currentProduct.reserved || 0))}</p>
                {currentProduct.reserved !== undefined && <p><strong>Reserved:</strong> {currentProduct.reserved}</p>}
                <p><strong>Description:</strong> {currentProduct.description || 'N/A'}</p>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowModal(false)} className="btn-primary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminInventory;
