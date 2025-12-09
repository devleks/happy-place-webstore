import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import api from '../services/api';

const WishlistContext = createContext();

export const useWishlist = () => {
  const context = useContext(WishlistContext);
  if (!context) {
    throw new Error('useWishlist must be used within a WishlistProvider');
  }
  return context;
};

export const WishlistProvider = ({ children }) => {
  const [wishlist, setWishlist] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { user } = useAuth();

  // Fetch wishlist when user logs in
  useEffect(() => {
    if (user) {
      fetchWishlist();
    } else {
      setWishlist(null);
    }
  }, [user]);

  const fetchWishlist = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/wishlist');
      setWishlist(response.data);
    } catch (err) {
      console.error('Error fetching wishlist:', err);
      setError(err.response?.data?.error || 'Failed to fetch wishlist');
    } finally {
      setLoading(false);
    }
  };

  const addToWishlist = async (productId) => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.post('/wishlist/items', {
        product_id: productId
      });

      // Refresh wishlist
      await fetchWishlist();

      return { success: true, data: response.data };
    } catch (err) {
      console.error('Error adding to wishlist:', err);
      const errorMsg = err.response?.data?.error || 'Failed to add item to wishlist';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const removeFromWishlist = async (itemId) => {
    try {
      setLoading(true);
      setError(null);
      await api.delete(`/wishlist/items/${itemId}`);

      // Refresh wishlist
      await fetchWishlist();

      return { success: true };
    } catch (err) {
      console.error('Error removing from wishlist:', err);
      const errorMsg = err.response?.data?.error || 'Failed to remove item from wishlist';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const moveToCart = async (itemId, variantId = null, quantity = 1) => {
    try {
      setLoading(true);
      setError(null);
      const body = { quantity };
      if (variantId) {
        body.variant_id = variantId;
      }

      await api.post(`/wishlist/move-to-cart/${itemId}`, body);

      // Refresh wishlist
      await fetchWishlist();

      return { success: true };
    } catch (err) {
      console.error('Error moving to cart:', err);
      const errorMsg = err.response?.data?.error || 'Failed to move item to cart';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const isInWishlist = (productId) => {
    if (!wishlist || !wishlist.items) return false;
    return wishlist.items.some(item => item.product_id === productId);
  };

  const getWishlistCount = () => {
    if (!wishlist || !wishlist.items) return 0;
    return wishlist.items.length;
  };

  const value = {
    wishlist,
    loading,
    error,
    fetchWishlist,
    addToWishlist,
    removeFromWishlist,
    moveToCart,
    isInWishlist,
    getWishlistCount
  };

  return <WishlistContext.Provider value={value}>{children}</WishlistContext.Provider>;
};
