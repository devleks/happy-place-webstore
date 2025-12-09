import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { helpers } from '../services/api';
import toast from '../utils/toast';
import '../styles/Cart.css';

function Cart() {
  const { cart, loading, updateCartItem, removeFromCart, clearCart } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [updatingItem, setUpdatingItem] = useState(null);

  useEffect(() => {
    if (!user) {
      navigate('/login');
    }
  }, [user, navigate]);

  const handleQuantityChange = async (itemId, newQuantity) => {
    if (newQuantity < 1) return;

    setUpdatingItem(itemId);
    const result = await updateCartItem(itemId, newQuantity);
    setUpdatingItem(null);

    if (!result.success) {
      toast.error(result.error || 'Failed to update quantity');
    }
  };

  const handleRemoveItem = async (itemId) => {
    if (window.confirm('Remove this item from cart?')) {
      const result = await removeFromCart(itemId);
      if (!result.success) {
        toast.error(result.error || 'Failed to remove item');
      } else {
        toast.success('Item removed from cart');
      }
    }
  };

  const handleClearCart = async () => {
    if (window.confirm('Clear all items from cart?')) {
      const result = await clearCart();
      if (!result.success) {
        toast.error(result.error || 'Failed to clear cart');
      } else {
        toast.success('Cart cleared successfully');
      }
    }
  };

  if (loading && !cart) {
    return (
      <div className="cart-container">
        <div className="loading">Loading cart...</div>
      </div>
    );
  }

  if (!cart || !cart.items || cart.items.length === 0) {
    return (
      <div className="cart-container">
        <div className="empty-cart">
          <h2>Your Cart is Empty</h2>
          <p>Add some items to get started!</p>
          <Link to="/products" className="btn-primary">Shop Now</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="cart-container">
      <div className="cart-header">
        <h1>Shopping Cart</h1>
        <button onClick={handleClearCart} className="btn-clear-cart">
          Clear Cart
        </button>
      </div>

      <div className="cart-content">
        <div className="cart-items">
          {cart.items.map((item) => {
            const variant = item.variant;
            const product = variant?.product;

            if (!product) return null;

            const price = product.sale_price || product.price;
            const itemTotal = price * item.quantity;

            // Get product image URL
            const imageUrl = product.primary_image?.image_url ||
                           product.images?.[0]?.image_url ||
                           'https://via.placeholder.com/150';

            return (
              <div key={item.id} className="cart-item">
                <Link to={`/products/${product.slug}`} className="cart-item-image">
                  <img
                    src={imageUrl}
                    alt={product.name}
                  />
                </Link>

                <div className="cart-item-details">
                  <Link to={`/products/${product.slug}`} className="cart-item-name">
                    {product.name}
                  </Link>

                  <div className="cart-item-variant">
                    {variant.size && <span>Size: {variant.size}</span>}
                    {variant.color && (
                      <span>
                        Color: <span className="color-preview" style={{ backgroundColor: variant.color }}></span>
                        {variant.color}
                      </span>
                    )}
                  </div>

                  <div className="cart-item-sku">SKU: {variant.sku}</div>

                  {product.is_clearance && (
                    <div className="final-sale-badge">FINAL SALE</div>
                  )}
                </div>

                <div className="cart-item-quantity">
                  <button
                    onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                    disabled={updatingItem === item.id || item.quantity <= 1}
                    className="quantity-btn"
                  >
                    -
                  </button>
                  <input
                    type="number"
                    value={item.quantity}
                    onChange={(e) => handleQuantityChange(item.id, parseInt(e.target.value) || 1)}
                    disabled={updatingItem === item.id}
                    className="quantity-input"
                    min="1"
                  />
                  <button
                    onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                    disabled={updatingItem === item.id}
                    className="quantity-btn"
                  >
                    +
                  </button>
                </div>

                <div className="cart-item-price">
                  <div className="item-unit-price">{helpers.formatPrice(price)}</div>
                  <div className="item-total-price">{helpers.formatPrice(itemTotal)}</div>
                </div>

                <button
                  onClick={() => handleRemoveItem(item.id)}
                  className="btn-remove"
                  disabled={updatingItem === item.id}
                >
                  Remove
                </button>
              </div>
            );
          })}
        </div>

        <div className="cart-summary">
          <h2>Order Summary</h2>

          <div className="summary-row">
            <span>Subtotal ({cart.total_items} items)</span>
            <span>{helpers.formatPrice(cart.subtotal)}</span>
          </div>

          <div className="summary-row">
            <span>Shipping</span>
            <span>Calculated at checkout</span>
          </div>

          <div className="summary-divider"></div>

          <div className="summary-row summary-total">
            <span>Total</span>
            <span>{helpers.formatPrice(cart.subtotal)}</span>
          </div>

          <button className="btn-checkout" onClick={() => navigate('/checkout')}>
            Proceed to Checkout
          </button>

          <Link to="/products" className="btn-continue-shopping">
            Continue Shopping
          </Link>

          <div className="cart-notice">
            <p>Nairobi: Free shipping</p>
            <p>Upcountry: KSh 300 + KSh 50/kg</p>
            <p className="final-sale-notice">FINAL SALE items cannot be returned or exchanged</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Cart;
