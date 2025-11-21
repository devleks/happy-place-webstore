import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { productsAPI } from '../services/api';
import '../styles/ProductDetail.css';

const ProductDetail = () => {
  const { slug } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSize, setSelectedSize] = useState('');
  const [selectedColor, setSelectedColor] = useState('');

  useEffect(() => {
    fetchProduct();
  }, [slug]);

  const fetchProduct = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await productsAPI.getBySlug(slug);
      setProduct(response.data);

      // Set default selections
      if (response.data.sizes) {
        const sizes = JSON.parse(response.data.sizes);
        setSelectedSize(sizes[0] || '');
      }
      if (response.data.colors) {
        const colors = JSON.parse(response.data.colors);
        setSelectedColor(colors[0] || '');
      }
    } catch (err) {
      setError('Failed to load product. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getAvailability = () => {
    if (!product || !product.inventory) return { online: false, store: false };

    const variant = product.inventory.find(
      (inv) => inv.size === selectedSize && inv.color === selectedColor
    );

    return {
      online: variant?.available_online || false,
      store: variant?.available_in_store || false,
      onlineQty: variant?.online_quantity || 0,
      storeQty: variant?.store_quantity || 0,
    };
  };

  if (loading) return <div className="loading">Loading product...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!product) return <div className="error">Product not found</div>;

  const sizes = product.sizes ? JSON.parse(product.sizes) : [];
  const colors = product.colors ? JSON.parse(product.colors) : [];
  const availability = getAvailability();

  return (
    <div className="product-detail">
      <div className="product-container">
        <div className="product-image-section">
          <img src={product.image_url} alt={product.name} className="product-image-large" />
        </div>

        <div className="product-info-section">
          <h1 className="product-title">{product.name}</h1>
          <p className="product-category">{product.category_name}</p>
          <p className="product-price">${product.price.toFixed(2)}</p>

          <div className="product-description">
            <p>{product.description}</p>
          </div>

          <div className="product-options">
            {sizes.length > 0 && (
              <div className="option-group">
                <label className="option-label">Size:</label>
                <div className="size-options">
                  {sizes.map((size) => (
                    <button
                      key={size}
                      className={`size-button ${selectedSize === size ? 'active' : ''}`}
                      onClick={() => setSelectedSize(size)}
                    >
                      {size}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {colors.length > 0 && (
              <div className="option-group">
                <label className="option-label">Color:</label>
                <div className="color-options">
                  {colors.map((color) => (
                    <button
                      key={color}
                      className={`color-button ${selectedColor === color ? 'active' : ''}`}
                      onClick={() => setSelectedColor(color)}
                    >
                      {color}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="availability-section">
            <h3>Availability</h3>
            <div className="availability-info">
              <div className={`availability-item ${availability.online ? 'in-stock' : 'out-of-stock'}`}>
                <span className="availability-label">Online:</span>
                <span className="availability-status">
                  {availability.online
                    ? `In Stock (${availability.onlineQty} available)`
                    : 'Out of Stock'}
                </span>
              </div>
              <div className={`availability-item ${availability.store ? 'in-stock' : 'out-of-stock'}`}>
                <span className="availability-label">In Store:</span>
                <span className="availability-status">
                  {availability.store
                    ? `Available (${availability.storeQty} in stock)`
                    : 'Out of Stock'}
                </span>
              </div>
            </div>
          </div>

          <div className="action-buttons">
            <button
              className="btn-primary-large"
              disabled={!availability.online && !availability.store}
            >
              {availability.online || availability.store ? 'Add to Cart' : 'Out of Stock'}
            </button>
          </div>

          <div className="product-meta">
            <p>SKU: {product.slug.toUpperCase()}</p>
            <p>Category: {product.category_name}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetail;
