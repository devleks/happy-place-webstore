import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { adminAPI } from '../../services/adminAPI';
import '../../styles/AdminDashboard.css';

const AddProduct = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category_id: '',
    price: '',
    stock_quantity: '',
    low_stock_threshold: '',
    sku: '',
  });
  const [variants, setVariants] = useState([
    { size: '', color: '', quantity: 0, sku_suffix: '' }
  ]);
  const [imageFiles, setImageFiles] = useState([]);
  const [imagePreviews, setImagePreviews] = useState([]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleVariantChange = (index, field, value) => {
    const newVariants = [...variants];
    newVariants[index][field] = value;
    setVariants(newVariants);
  };

  const addVariant = () => {
    setVariants([...variants, { size: '', color: '', quantity: 0, sku_suffix: '' }]);
  };

  const removeVariant = (index) => {
    if (variants.length > 1) {
      setVariants(variants.filter((_, i) => i !== index));
    }
  };

  const handleImageChange = (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    // Validate file types
    const validFiles = files.filter(file => file.type.startsWith('image/'));
    if (validFiles.length !== files.length) {
      setError('Please select only image files');
      return;
    }

    setImageFiles(prev => [...prev, ...validFiles]);

    // Create previews
    validFiles.forEach(file => {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreviews(prev => [...prev, reader.result]);
      };
      reader.readAsDataURL(file);
    });
  };

  const removeImage = (index) => {
    setImageFiles(prev => prev.filter((_, i) => i !== index));
    setImagePreviews(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate images
    if (imageFiles.length === 0) {
      setError('Please upload at least one product image');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Create product with variants
      const productData = {
        ...formData,
        variants: variants.map(v => ({
          size: v.size,
          color: v.color,
          quantity: parseInt(v.quantity) || 0,
          sku: formData.sku + (v.sku_suffix ? `-${v.sku_suffix}` : '')
        }))
      };
      
      const productResponse = await adminAPI.createProduct(productData);
      const productId = productResponse.product_id || productResponse.id;

      // Upload images
      if (imageFiles.length > 0 && productId) {
        await adminAPI.uploadProductImages(productId, imageFiles);
      }

      navigate('/admin/inventory');
    } catch (err) {
      setError(err.message || 'Failed to create product');
      console.error('Create product error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!user || (user.role !== 'admin' && user.role !== 'manager')) {
    navigate('/admin/login');
    return null;
  }

  return (
    <div className="add-product">
      <div className="page-header">
        <h1>Add New Product</h1>
        <button onClick={() => navigate('/admin/inventory')} className="btn-secondary">
          Cancel
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)} className="close-btn">×</button>
        </div>
      )}

      <form onSubmit={handleSubmit} className="admin-form">
        <div className="form-section">
          <h2>Product Information</h2>

          <div className="form-group">
            <label htmlFor="name">Product Name *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="sku">SKU *</label>
            <input
              type="text"
              id="sku"
              name="sku"
              value={formData.sku}
              onChange={handleChange}
              required
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows="4"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="category_id">Category *</label>
            <select
              id="category_id"
              name="category_id"
              value={formData.category_id}
              onChange={handleChange}
              required
              className="form-input"
            >
              <option value="">Select a category</option>
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
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="price">Price *</label>
              <input
                type="number"
                id="price"
                name="price"
                value={formData.price}
                onChange={handleChange}
                required
                min="0"
                step="0.01"
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="stock_quantity">Stock Quantity *</label>
              <input
                type="number"
                id="stock_quantity"
                name="stock_quantity"
                value={formData.stock_quantity}
                onChange={handleChange}
                required
                min="0"
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="low_stock_threshold">Low Stock Threshold *</label>
              <input
                type="number"
                id="low_stock_threshold"
                name="low_stock_threshold"
                value={formData.low_stock_threshold}
                onChange={handleChange}
                required
                min="0"
                className="form-input"
              />
            </div>
          </div>
        </div>

        <div className="form-section">
          <h2>Product Variants (Size & Color)</h2>
          <p className="form-note">Add different sizes and colors for this product. Each variant will have its own stock quantity.</p>
          
          {variants.map((variant, index) => (
            <div key={index} className="variant-row" style={{ display: 'flex', gap: '10px', marginBottom: '15px', padding: '15px', border: '1px solid #ddd', borderRadius: '4px', position: 'relative' }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Size *</label>
                <select
                  value={variant.size}
                  onChange={(e) => handleVariantChange(index, 'size', e.target.value)}
                  required
                  className="form-input"
                >
                  <option value="">Select Size</option>
                  <option value="XS">XS</option>
                  <option value="S">S</option>
                  <option value="M">M</option>
                  <option value="L">L</option>
                  <option value="XL">XL</option>
                  <option value="XXL">XXL</option>
                  <option value="XXXL">XXXL</option>
                  <option value="One Size">One Size</option>
                </select>
              </div>

              <div className="form-group" style={{ flex: 1 }}>
                <label>Color *</label>
                <input
                  type="text"
                  value={variant.color}
                  onChange={(e) => handleVariantChange(index, 'color', e.target.value)}
                  placeholder="e.g., Red, Blue, Black"
                  required
                  className="form-input"
                />
              </div>

              <div className="form-group" style={{ flex: 1 }}>
                <label>Quantity *</label>
                <input
                  type="number"
                  value={variant.quantity}
                  onChange={(e) => handleVariantChange(index, 'quantity', e.target.value)}
                  min="0"
                  required
                  className="form-input"
                />
              </div>

              <div className="form-group" style={{ flex: 1 }}>
                <label>SKU Suffix</label>
                <input
                  type="text"
                  value={variant.sku_suffix}
                  onChange={(e) => handleVariantChange(index, 'sku_suffix', e.target.value)}
                  placeholder="e.g., RED-M"
                  className="form-input"
                />
              </div>

              {variants.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeVariant(index)}
                  className="btn-danger"
                  style={{ position: 'absolute', top: '5px', right: '5px', padding: '5px 10px', fontSize: '12px' }}
                >
                  Remove
                </button>
              )}
            </div>
          ))}

          <button
            type="button"
            onClick={addVariant}
            className="btn-secondary"
            style={{ marginTop: '10px' }}
          >
            + Add Another Variant
          </button>
        </div>

        <div className="form-section">
          <h2>Product Images *</h2>
          <p className="form-note">Upload at least one product image. The first image will be set as the primary image.</p>

          <div className="form-group">
            <label htmlFor="images">Upload Images</label>
            <input
              type="file"
              id="images"
              accept="image/*"
              multiple
              onChange={handleImageChange}
              className="form-input"
            />
          </div>

          {imagePreviews.length > 0 && (
            <div className="image-previews" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '15px' }}>
              {imagePreviews.map((preview, index) => (
                <div key={index} className="image-preview-item" style={{ position: 'relative' }}>
                  <img
                    src={preview}
                    alt={`Preview ${index + 1}`}
                    style={{ width: '100px', height: '100px', objectFit: 'cover', borderRadius: '4px', border: '1px solid #ddd' }}
                  />
                  <button
                    type="button"
                    onClick={() => removeImage(index)}
                    className="remove-image-btn"
                    style={{ position: 'absolute', top: '-5px', right: '-5px', background: 'red', color: 'white', border: 'none', borderRadius: '50%', width: '20px', height: '20px', cursor: 'pointer', fontSize: '12px' }}
                  >
                    ×
                  </button>
                  {index === 0 && (
                    <span style={{ position: 'absolute', bottom: '0', left: '0', right: '0', background: 'rgba(0,0,0,0.7)', color: 'white', fontSize: '10px', padding: '2px', textAlign: 'center' }}>
                      Primary
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="form-actions">
          <button
            type="button"
            onClick={() => navigate('/admin/inventory')}
            className="btn-secondary"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
          >
            {loading ? 'Creating...' : 'Create Product'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default AddProduct;
