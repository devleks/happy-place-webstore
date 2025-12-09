import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { helpers } from '../services/api';
import { useWishlist } from '../context/WishlistContext';
import { useAuth } from '../context/AuthContext';
import toast from '../utils/toast';
import { formatSizeWithConversions } from '../utils/sizeConversion';
import '../styles/ProductCard.css';

const ProductCard = ({ product }) => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { addToWishlist, removeFromWishlist, isInWishlist, wishlist } = useWishlist();
  const [isLoading, setIsLoading] = useState(false);

  const isWishlisted = isInWishlist(product.id);

  // Generate rating (mock data for now - TODO: get from backend)
  const rating = product.rating || 4.5;
  const reviewCount = product.review_count || Math.floor(Math.random() * 50) + 5;

  // Calculate sale status and pricing using helpers
  const isOnSale = helpers.isOnSale(product);
  const discountPercent = helpers.getDiscountPercent(product);
  const isClearance = product.is_clearance || false;
  const displayPrice = isOnSale ? product.sale_price : product.price;

  // Color options from product data
  const colors = product.available_colors || [];

  // Size options from product data
  const sizes = product.available_sizes || [];

  // Determine category type (Women's or Maternity)
  const isMaternity = product.category_name?.toLowerCase().includes('maternity');
  const categoryType = isMaternity ? 'maternity' : 'womens';

  const handleWishlistClick = async (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (!user) {
      toast.warning('Please log in to add items to wishlist');
      navigate('/login');
      return;
    }

    if (isLoading) return;

    setIsLoading(true);

    if (isWishlisted) {
      // Find the wishlist item for this product
      const wishlistItem = wishlist?.items?.find(item => item.product_id === product.id);
      if (wishlistItem) {
        const result = await removeFromWishlist(wishlistItem.id);
        if (!result.success) {
          toast.error(result.error || 'Failed to remove from wishlist');
        }
      }
    } else {
      const result = await addToWishlist(product.id);
      if (!result.success) {
        toast.error(result.error || 'Failed to add to wishlist');
      } else {
        toast.success('Added to wishlist!');
      }
    }

    setIsLoading(false);
  };

  const renderStars = (rating) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;

    for (let i = 0; i < 5; i++) {
      if (i < fullStars) {
        stars.push(<span key={i} className="star filled">★</span>);
      } else if (i === fullStars && hasHalfStar) {
        stars.push(<span key={i} className="star half">★</span>);
      } else {
        stars.push(<span key={i} className="star empty">★</span>);
      }
    }
    return stars;
  };

  return (
    <div className="product-card">
      {/* Badges */}
      <div className="product-badges">
        {isClearance && <span className="badge badge-final-sale">FINAL SALE</span>}
        {isOnSale && !isClearance && (
          <span className="badge badge-sale">{discountPercent}% OFF</span>
        )}
      </div>

      {/* Category Badge */}
      <div className="category-badge-container">
        <span className={`category-badge badge-${categoryType}`}>
          {isMaternity ? 'MATERNITY' : "WOMEN'S"}
        </span>
      </div>

      {/* Wishlist Button */}
      <button
        className={`wishlist-btn ${isWishlisted ? 'active' : ''}`}
        onClick={handleWishlistClick}
        disabled={isLoading}
        title={isWishlisted ? 'Remove from wishlist' : 'Add to wishlist'}
      >
        <svg viewBox="0 0 24 24" fill={isWishlisted ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
        </svg>
      </button>

      <Link to={`/products/${product.slug}`} className="product-link">
        <div className="product-image-container">
          <img
            src={product.image_url}
            alt={product.name}
            className="product-image"
          />
          {/* Quick View overlay on hover */}
          <div className="quick-view-overlay">
            <span className="quick-view-text">Quick View</span>
          </div>
        </div>
        <div className="product-info">
          <h3 className="product-name">{product.name}</h3>

          {/* Rating */}
          <div className="product-rating">
            <div className="stars">{renderStars(rating)}</div>
            <span className="review-count">({reviewCount})</span>
          </div>

          {/* Price */}
          <div className="product-pricing">
            {isOnSale ? (
              <>
                <span className="product-price-sale">{helpers.formatPrice(displayPrice)}</span>
                <span className="product-price-original">{helpers.formatPrice(product.price)}</span>
              </>
            ) : (
              <span className="product-price">{helpers.formatPrice(displayPrice)}</span>
            )}
          </div>

          {/* Available Colors */}
          {colors && colors.length > 0 && (
            <div className="color-options-text">
              <span className="color-label">Colors: </span>
              <span className="color-list">
                {colors.slice(0, 3).join(', ')}
                {colors.length > 3 && ` +${colors.length - 3} more`}
              </span>
            </div>
          )}

          {/* Available Sizes */}
          {sizes && sizes.length > 0 && (
            <div className="size-options-text">
              <span className="size-label">Sizes: </span>
              <span className="size-list">
                {sizes.slice(0, 4).map((size, index) => (
                  <span
                    key={size}
                    className="size-item"
                    title={formatSizeWithConversions(size)}
                  >
                    {size}{index < Math.min(sizes.length, 4) - 1 ? ', ' : ''}
                  </span>
                ))}
                {sizes.length > 4 && ` +${sizes.length - 4} more`}
              </span>
            </div>
          )}
        </div>
      </Link>
    </div>
  );
};

export default ProductCard;
