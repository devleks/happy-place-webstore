import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { productsAPI, helpers } from '../services/api';
import { useCart } from '../context/CartContext';
import { useWishlist } from '../context/WishlistContext';
import { useAuth } from '../context/AuthContext';
import toast from '../utils/toast';
import SizeGuide from '../components/SizeGuide';
import { formatSizeWithConversions } from '../utils/sizeConversion';
import '../styles/ProductDetail.css';

const ProductDetail = () => {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { addToCart } = useCart();
  const { addToWishlist, isInWishlist } = useWishlist();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSize, setSelectedSize] = useState('');
  const [selectedColor, setSelectedColor] = useState('');
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [addingToCart, setAddingToCart] = useState(false);
  const [addingToWishlist, setAddingToWishlist] = useState(false);
  const [showSizeGuide, setShowSizeGuide] = useState(false);

  useEffect(() => {
    fetchProduct();
  }, [slug]);

  useEffect(() => {
    if (product && selectedSize && selectedColor) {
      findVariant();
    }
  }, [selectedSize, selectedColor, product]);

  // Reset quantity to 1 when variant changes
  useEffect(() => {
    setQuantity(1);
  }, [selectedVariant]);

  const fetchProduct = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await productsAPI.getBySlug(slug);
      const productData = response.data;
      setProduct(productData);

      // Set default selections from available sizes/colors
      if (productData.available_sizes && productData.available_sizes.length > 0) {
        setSelectedSize(productData.available_sizes[0]);
      }
      if (productData.available_colors && productData.available_colors.length > 0) {
        setSelectedColor(productData.available_colors[0]);
      }
    } catch (err) {
      setError('Failed to load product. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const findVariant = () => {
    if (!product || !product.variants) return;

    const variant = product.variants.find(
      (v) => v.size === selectedSize && v.color === selectedColor && v.is_active
    );

    setSelectedVariant(variant || null);
  };

  const getAvailabilityStatus = () => {
    if (!selectedVariant || !selectedVariant.inventory) {
      return {
        available: false,
        quantity: 0,
        status: 'Out of Stock',
        statusClass: 'out-of-stock',
      };
    }

    const availableQty = selectedVariant.inventory.available_quantity;
    const isLowStock = selectedVariant.inventory.is_low_stock;
    const isOutOfStock = selectedVariant.inventory.is_out_of_stock;

    if (isOutOfStock || availableQty === 0) {
      return {
        available: false,
        quantity: 0,
        status: 'Out of Stock',
        statusClass: 'out-of-stock',
      };
    }

    if (isLowStock) {
      return {
        available: true,
        quantity: availableQty,
        status: `Low Stock (${availableQty} left)`,
        statusClass: 'low-stock',
      };
    }

    return {
      available: true,
      quantity: availableQty,
      status: `In Stock (${availableQty} available)`,
      statusClass: 'in-stock',
    };
  };

  const handleQuantityChange = (newQuantity) => {
    const maxQuantity = availability.quantity || 1;

    // Ensure quantity is within valid range
    if (newQuantity < 1) {
      setQuantity(1);
    } else if (newQuantity > maxQuantity) {
      setQuantity(maxQuantity);
      toast.warning(`Maximum available quantity is ${maxQuantity}`);
    } else {
      setQuantity(newQuantity);
    }
  };

  const handleQuantityDecrease = () => {
    if (quantity > 1) {
      setQuantity(quantity - 1);
    }
  };

  const handleQuantityIncrease = () => {
    const maxQuantity = availability.quantity || 1;
    if (quantity < maxQuantity) {
      setQuantity(quantity + 1);
    } else {
      toast.warning(`Maximum available quantity is ${maxQuantity}`);
    }
  };

  const handleAddToCart = async () => {
    if (!user) {
      toast.warning('Please log in to add items to cart');
      navigate('/login');
      return;
    }

    if (!selectedVariant) {
      toast.warning('Please select size and color');
      return;
    }

    if (!availability.available) {
      toast.error('This variant is out of stock');
      return;
    }

    if (quantity < 1) {
      toast.error('Please select a valid quantity');
      return;
    }

    if (quantity > availability.quantity) {
      toast.error(`Only ${availability.quantity} items available`);
      return;
    }

    setAddingToCart(true);
    const result = await addToCart(selectedVariant.id, quantity);
    setAddingToCart(false);

    if (result.success) {
      toast.success(`Added ${quantity} item(s) to cart!`);
    } else {
      toast.error(result.error || 'Failed to add to cart');
    }
  };

  const handleAddToWishlist = async () => {
    if (!user) {
      toast.warning('Please log in to add items to wishlist');
      navigate('/login');
      return;
    }

    if (isInWishlist(product.id)) {
      toast.info('This item is already in your wishlist');
      return;
    }

    setAddingToWishlist(true);
    const result = await addToWishlist(product.id);
    setAddingToWishlist(false);

    if (result.success) {
      toast.success('Added to wishlist!');
    } else {
      toast.error(result.error || 'Failed to add to wishlist');
    }
  };

  if (loading) return <div className="loading">Loading product...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!product) return <div className="error">Product not found</div>;

  const availability = getAvailabilityStatus();
  const isOnSale = helpers.isOnSale(product);
  const discountPercent = helpers.getDiscountPercent(product);
  const canReturn = helpers.canBeReturned(product);
  const returnMessage = helpers.getReturnPolicyMessage(product);

  return (
    <div className="product-detail">
      <div className="product-container">
        {/* Product Images */}
        <div className="product-image-section">
          {product.images && product.images.length > 0 ? (
            <img
              src={product.images.find((img) => img.is_primary)?.image_url || product.images[0].image_url}
              alt={product.name}
              className="product-image-large"
            />
          ) : (
            <div className="product-image-placeholder">No Image</div>
          )}

          {/* Additional images thumbnails - future enhancement */}
          {product.images && product.images.length > 1 && (
            <div className="product-thumbnails">
              {product.images.map((img) => (
                <img
                  key={img.id}
                  src={img.image_url}
                  alt={img.alt_text}
                  className="product-thumbnail"
                />
              ))}
            </div>
          )}
        </div>

        {/* Product Info */}
        <div className="product-info-section">
          {/* Badges */}
          <div className="product-badges">
            {product.is_clearance && (
              <span className="badge final-sale-badge">FINAL SALE</span>
            )}
            {isOnSale && !product.is_clearance && (
              <span className="badge sale-badge">{discountPercent}% OFF</span>
            )}
          </div>

          <h1 className="product-title">{product.name}</h1>
          <p className="product-category">{product.category_name}</p>

          {/* Price */}
          <div className="product-price-section">
            {isOnSale ? (
              <>
                <span className="product-price-sale">{helpers.formatPrice(product.sale_price)}</span>
                <span className="product-price-original">{helpers.formatPrice(product.price)}</span>
              </>
            ) : (
              <span className="product-price">{helpers.formatPrice(product.price)}</span>
            )}
          </div>

          {/* Description */}
          {product.description && (
            <div className="product-description">
              <p>{product.description}</p>
            </div>
          )}

          {/* Variant Selection */}
          <div className="product-options">
            {/* Size Selection */}
            {product.available_sizes && product.available_sizes.length > 0 && (
              <div className="option-group">
                <div className="option-header">
                  <label className="option-label">
                    Size: <span className="selected-value">{selectedSize}</span>
                  </label>
                  <button
                    className="size-guide-link"
                    onClick={() => setShowSizeGuide(true)}
                  >
                    📏 Size Guide
                  </button>
                </div>
                <div className="size-options">
                  {product.available_sizes.map((size) => (
                    <button
                      key={size}
                      className={`size-button ${selectedSize === size ? 'active' : ''}`}
                      onClick={() => setSelectedSize(size)}
                      title={formatSizeWithConversions(size)}
                    >
                      {size}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Color Selection */}
            {product.available_colors && product.available_colors.length > 0 && (
              <div className="option-group">
                <label className="option-label">
                  Color: <span className="selected-value">{selectedColor}</span>
                </label>
                <div className="color-options">
                  {product.available_colors.map((color) => (
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

          {/* Availability */}
          {selectedVariant && (
            <div className="availability-section">
              <div className={`availability-status ${availability.statusClass}`}>
                <span className="status-icon">
                  {availability.available ? '✓' : '✕'}
                </span>
                <span className="status-text">{availability.status}</span>
              </div>
              {selectedVariant.sku && (
                <p className="variant-sku">SKU: {selectedVariant.sku}</p>
              )}
            </div>
          )}

          {/* Quantity Selector */}
          {selectedVariant && availability.available && (
            <div className="quantity-section">
              <label className="quantity-label">Quantity:</label>
              <div className="quantity-selector">
                <button
                  className="quantity-btn"
                  onClick={handleQuantityDecrease}
                  disabled={quantity <= 1}
                  aria-label="Decrease quantity"
                >
                  −
                </button>
                <input
                  type="number"
                  className="quantity-input"
                  value={quantity}
                  onChange={(e) => handleQuantityChange(parseInt(e.target.value) || 1)}
                  min="1"
                  max={availability.quantity}
                />
                <button
                  className="quantity-btn"
                  onClick={handleQuantityIncrease}
                  disabled={quantity >= availability.quantity}
                  aria-label="Increase quantity"
                >
                  +
                </button>
              </div>
            </div>
          )}

          {/* Add to Cart Button */}
          <div className="action-buttons">
            <button
              className="btn-primary-large"
              disabled={!availability.available || addingToCart}
              onClick={handleAddToCart}
            >
              {addingToCart ? 'Adding...' : availability.available ? 'Add to Cart' : 'Out of Stock'}
            </button>
            <button
              className="btn-wishlist"
              onClick={handleAddToWishlist}
              disabled={addingToWishlist || isInWishlist(product.id)}
              title={isInWishlist(product.id) ? 'Already in wishlist' : 'Add to wishlist'}
            >
              <svg className="heart-icon" viewBox="0 0 24 24" fill={isInWishlist(product.id) ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
              </svg>
            </button>
          </div>

          {/* Return Policy */}
          <div className="return-policy-section">
            <div className={`return-policy-badge ${canReturn ? 'returnable' : 'final-sale'}`}>
              <span className="policy-icon">{canReturn ? 'ℹ' : '⚠'}</span>
              <span className="policy-text">{returnMessage}</span>
            </div>
            {canReturn && (
              <p className="policy-details" style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
                2-day return window from delivery. 10% restocking fee applies.
              </p>
            )}
          </div>

          {/* Product Meta */}
          <div className="product-meta">
            <div className="meta-item">
              <strong>Category:</strong> {product.category_name}
            </div>
            {product.weight && (
              <div className="meta-item">
                <strong>Weight:</strong> {product.weight} kg
              </div>
            )}
            <div className="meta-item">
              <strong>Product ID:</strong> {product.id}
            </div>
          </div>
        </div>
      </div>

      {/* Size Guide Modal */}
      {showSizeGuide && (
        <SizeGuide
          selectedSize={selectedSize}
          onClose={() => setShowSizeGuide(false)}
        />
      )}
    </div>
  );
};

export default ProductDetail;
