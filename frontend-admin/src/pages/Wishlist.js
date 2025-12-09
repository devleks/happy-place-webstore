import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useWishlist } from '../context/WishlistContext';
import { useAuth } from '../context/AuthContext';
import { helpers } from '../services/api';
import toast from '../utils/toast';
import '../styles/Wishlist.css';

function Wishlist() {
  const { wishlist, loading, removeFromWishlist, moveToCart } = useWishlist();
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate('/login');
    }
  }, [user, navigate]);

  const handleRemoveItem = async (itemId) => {
    if (window.confirm('Remove this item from wishlist?')) {
      const result = await removeFromWishlist(itemId);
      if (!result.success) {
        toast.error(result.error || 'Failed to remove item');
      } else {
        toast.success('Item removed from wishlist');
      }
    }
  };

  const handleMoveToCart = async (itemId) => {
    const result = await moveToCart(itemId);
    if (result.success) {
      toast.success('Item moved to cart!');
    } else {
      toast.error(result.error || 'Failed to move item to cart');
    }
  };

  if (loading && !wishlist) {
    return (
      <div className="wishlist-container">
        <div className="loading">Loading wishlist...</div>
      </div>
    );
  }

  if (!wishlist || !wishlist.items || wishlist.items.length === 0) {
    return (
      <div className="wishlist-container">
        <div className="empty-wishlist">
          <h2>Your Wishlist is Empty</h2>
          <p>Save your favorite items for later!</p>
          <Link to="/products" className="btn-primary">Browse Products</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="wishlist-container">
      <div className="wishlist-header">
        <h1>My Wishlist</h1>
        <span className="wishlist-count">{wishlist.total_items} items</span>
      </div>

      <div className="wishlist-grid">
        {wishlist.items.map((item) => {
          const product = item.product;

          if (!product) return null;

          const onSale = helpers.isOnSale(product);
          const discount = helpers.getDiscountPercent(product);

          // Get product image URL
          const imageUrl = product.primary_image?.image_url ||
                         product.images?.[0]?.image_url ||
                         'https://via.placeholder.com/300';

          return (
            <div key={item.id} className="wishlist-item">
              <Link to={`/products/${product.slug}`} className="wishlist-item-image">
                <img
                  src={imageUrl}
                  alt={product.name}
                />

                {product.is_clearance && (
                  <span className="badge final-sale-badge">FINAL SALE</span>
                )}
                {onSale && !product.is_clearance && (
                  <span className="badge sale-badge">{discount}% OFF</span>
                )}
              </Link>

              <div className="wishlist-item-content">
                <Link to={`/products/${product.slug}`} className="wishlist-item-name">
                  {product.name}
                </Link>

                <p className="wishlist-item-description">
                  {product.description && product.description.length > 80
                    ? product.description.substring(0, 80) + '...'
                    : product.description}
                </p>

                <div className="wishlist-item-price">
                  {onSale ? (
                    <>
                      <span className="original-price">{helpers.formatPrice(product.price)}</span>
                      <span className="sale-price">{helpers.formatPrice(product.sale_price)}</span>
                    </>
                  ) : (
                    <span className="regular-price">{helpers.formatPrice(product.price)}</span>
                  )}
                </div>

                <div className="wishlist-item-actions">
                  <button
                    onClick={() => handleMoveToCart(item.id)}
                    className="btn-move-to-cart"
                  >
                    Add to Cart
                  </button>
                  <button
                    onClick={() => handleRemoveItem(item.id)}
                    className="btn-remove-wishlist"
                  >
                    Remove
                  </button>
                </div>

                <div className="wishlist-item-date">
                  Added {new Date(item.added_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default Wishlist;
