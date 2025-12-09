import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import api from '../services/api';

const CartContext = createContext();

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};

export const CartProvider = ({ children }) => {
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { user } = useAuth();

  // Fetch cart when user logs in
  useEffect(() => {
    if (user) {
      fetchCart();
    } else {
      setCart(null);
    }
  }, [user]);

  const fetchCart = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/cart');
      setCart(response.data);
    } catch (err) {
      console.error('Error fetching cart:', err);
      setError(err.response?.data?.error || 'Failed to fetch cart');
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (variantId, quantity = 1) => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.post('/cart/items', {
        variant_id: variantId,
        quantity
      });

      // Refresh cart
      await fetchCart();

      return { success: true, data: response.data };
    } catch (err) {
      console.error('Error adding to cart:', err);
      const errorMsg = err.response?.data?.error || 'Failed to add item to cart';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const updateCartItem = async (itemId, quantity) => {
    try {
      setLoading(true);
      setError(null);
      await api.put(`/cart/items/${itemId}`, { quantity });

      // Refresh cart
      await fetchCart();

      return { success: true };
    } catch (err) {
      console.error('Error updating cart item:', err);
      const errorMsg = err.response?.data?.error || 'Failed to update cart item';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const removeFromCart = async (itemId) => {
    try {
      setLoading(true);
      setError(null);
      await api.delete(`/cart/items/${itemId}`);

      // Refresh cart
      await fetchCart();

      return { success: true };
    } catch (err) {
      console.error('Error removing from cart:', err);
      const errorMsg = err.response?.data?.error || 'Failed to remove item from cart';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const clearCart = async () => {
    try {
      setLoading(true);
      setError(null);
      await api.delete('/cart');

      // Refresh cart
      await fetchCart();

      return { success: true };
    } catch (err) {
      console.error('Error clearing cart:', err);
      const errorMsg = err.response?.data?.error || 'Failed to clear cart';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const getCartCount = () => {
    if (!cart || !cart.items) return 0;
    return cart.items.reduce((total, item) => total + item.quantity, 0);
  };

  const value = {
    cart,
    loading,
    error,
    fetchCart,
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    getCartCount
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};
