import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/ProductCard.css';

const ProductCard = ({ product }) => {
  const [isWishlisted, setIsWishlisted] = useState(false);

  // Generate rating (mock data for now - TODO: get from backend)
  const rating = product.rating || 4.5;
  const reviewCount = product.review_count || Math.floor(Math.random() * 50) + 5;

  // Mock data for badges
  const isNew = product.is_new || false;
  const isOnSale = product.sale_price && product.sale_price < product.price;
  const displayPrice = isOnSale ? product.sale_price : product.price;

  // Mock color options
  const colors = product.colors || ['#722F37', '#B76E79', '#F4E4E6'];

  const handleWishlistClick = (e) => {
    e.preventDefault();
    setIsWishlisted(!isWishlisted);
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
        {isNew && <span className="badge badge-new">NEW</span>}
        {isOnSale && <span className="badge badge-sale">SALE</span>}
      </div>

      {/* Wishlist Button */}
      <button
        className={`wishlist-btn ${isWishlisted ? 'active' : ''}`}
        onClick={handleWishlistClick}
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
            <span className="product-price">${displayPrice.toFixed(2)}</span>
            {isOnSale && (
              <span className="product-price-original">${product.price.toFixed(2)}</span>
            )}
          </div>

          {/* Color Swatches */}
          {colors && colors.length > 0 && (
            <div className="color-swatches">
              {colors.slice(0, 4).map((color, index) => (
                <span
                  key={index}
                  className="color-swatch"
                  style={{ backgroundColor: color }}
                  title={`Color option ${index + 1}`}
                ></span>
              ))}
              {colors.length > 4 && (
                <span className="color-more">+{colors.length - 4}</span>
              )}
            </div>
          )}
        </div>
      </Link>
    </div>
  );
};

export default ProductCard;
