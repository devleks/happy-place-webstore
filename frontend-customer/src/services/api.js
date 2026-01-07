import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token && token !== 'undefined' && token !== 'null') {
    config.headers.Authorization = `Bearer ${token}`;
  } else if (config.headers.Authorization) {
    delete config.headers.Authorization;
  }
  return config;
});

// Auto-refresh token on 401 errors
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If error is 401 and we haven't tried to refresh yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh_token');

      if (!refreshToken || refreshToken === 'undefined' || refreshToken === 'null') {
        // No refresh token, redirect to appropriate login
        const userType = localStorage.getItem('user_type');
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_type');

        // Redirect based on user type or current path
        if (userType === 'employee' || window.location.pathname.startsWith('/admin')) {
          window.location.href = '/admin/login';
        } else if (window.location.pathname.startsWith('/pos')) {
          window.location.href = '/pos/login';
        } else {
          window.location.href = '/customer/login';
        }
        return Promise.reject(error);
      }

      try {
        // Call refresh endpoint
        const response = await axios.post(
          `${API_BASE_URL}/auth/refresh`,
          {},
          {
            headers: {
              Authorization: `Bearer ${refreshToken}`,
            },
          }
        );

        const newAccessToken = response.data.access_token;

        // Store new access token
        localStorage.setItem('token', newAccessToken);

        // Update authorization header
        api.defaults.headers.common.Authorization = `Bearer ${newAccessToken}`;
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

        // Process queued requests
        processQueue(null, newAccessToken);

        isRefreshing = false;

        // Retry original request
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        processQueue(refreshError, null);
        isRefreshing = false;

        const userType = localStorage.getItem('user_type');

        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_type');

        // Redirect to appropriate login page
        if (userType === 'employee' || window.location.pathname.startsWith('/admin')) {
          window.location.href = '/admin/login';
        } else if (window.location.pathname.startsWith('/pos')) {
          window.location.href = '/pos/login';
        } else {
          window.location.href = '/customer/login';
        }

        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Helper to get user type from token
const getUserType = () => {
  const token = localStorage.getItem('token');
  if (!token) return null;

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.user_type; // 'customer' or 'employee'
  } catch (e) {
    return null;
  }
};

// =====================================
// AUTHENTICATION API
// =====================================
export const authAPI = {
  // Customer Authentication
  customerRegister: (userData) => api.post('/auth/customer/register', userData),
  customerLogin: (credentials) => api.post('/auth/customer/login', credentials),
  customerGoogleOAuth: (data) => api.post('/auth/customer/google-oauth', data),
  getCustomerProfile: () => api.get('/auth/customer/me'),

  // Employee Authentication
  employeeLogin: (credentials) => api.post('/auth/employee/login', credentials),
  getEmployeeProfile: () => api.get('/auth/employee/me'),

  // Admin Authentication
  adminLogin: (credentials) => api.post('/auth/admin/login', credentials),

  // Token Management
  refreshToken: (refreshToken) => api.post('/auth/refresh', {}, {
    headers: { Authorization: `Bearer ${refreshToken}` }
  }),

  logoutUser: (accessToken, refreshToken) => api.post('/auth/logout',
    { refresh_token: refreshToken },
    { headers: { Authorization: `Bearer ${accessToken}` }}
  ),

  // Helper methods
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_type');
  },

  isAuthenticated: () => !!localStorage.getItem('token'),
  getUserType: getUserType,
  isCustomer: () => getUserType() === 'customer',
  isEmployee: () => getUserType() === 'employee',
};

// =====================================
// PRODUCTS API
// =====================================
export const productsAPI = {
  // Public endpoints
  getAll: (params) => api.get('/products', { params }),
  getBySlug: (slug) => api.get(`/products/${slug}`),
  getById: (id) => api.get(`/products/${id}`),

  // Admin endpoints
  create: (productData) => api.post('/admin/products', productData),
};

// =====================================
// PRODUCT VARIANTS API
// =====================================
export const variantsAPI = {
  // Get all variants for a product
  getByProductId: (productId) => api.get(`/products/${productId}/variants`),

  // Create variant (Admin only)
  create: (productId, variantData) => api.post(`/products/${productId}/variants`, variantData),

  // Update variant inventory (Admin only)
  updateInventory: (variantId, data) => api.patch(`/variants/${variantId}/inventory`, data),

  // Check variant availability
  checkAvailability: (variantId) => api.get(`/variants/${variantId}/availability`),
};

// =====================================
// CATEGORIES API
// =====================================
export const categoriesAPI = {
  // Get all categories (flat list)
  getAll: () => api.get('/categories'),

  // Get category tree (hierarchical)
  getTree: () => api.get('/categories/tree'),

  // Get category descendants
  getDescendants: (categoryId) => api.get(`/categories/${categoryId}/descendants`),

  // Get products in category (with subcategories)
  getProducts: (categoryId, params = {}) => api.get(`/categories/${categoryId}/products`, { params }),
};

// =====================================
// PROMOTIONS API
// =====================================
export const promotionsAPI = {
  // Validate promotion code
  validate: (data) => api.post('/promotions/validate', data),

  // Apply promotion to order
  applyToOrder: (orderId, promotionCode) =>
    api.post(`/orders/${orderId}/promotions`, { promotion_code: promotionCode }),

  // Get active promotions
  getActive: () => api.get('/promotions/active'),
};

// =====================================
// RETURNS API
// =====================================
export const returnsAPI = {
  // Check return eligibility for an order
  checkEligibility: (orderId) => api.get(`/orders/${orderId}/return-eligibility`),

  // Create return request
  create: (returnData) => api.post('/returns', returnData),

  // Get return status
  getById: (returnId) => api.get(`/returns/${returnId}`),

  // Update return status (Admin only)
  updateStatus: (returnId, statusData) => api.patch(`/returns/${returnId}/status`, statusData),
};

// =====================================
// SHIPPING API
// =====================================
export const shippingAPI = {
  // Get available shipping methods
  getMethods: (isNairobi = true) => api.get('/shipping/methods', { params: { is_nairobi: isNairobi } }),

  // Calculate shipping cost
  calculate: (data) => api.post('/shipping/calculate', data),

  // Get shipping method details
  getMethod: (methodId) => api.get(`/shipping/methods/${methodId}`),
};

// =====================================
// ADMIN API
// =====================================
export const adminAPI = {
  // Dashboard
  getDashboard: () => api.get('/admin/dashboard'),

  // Inventory alerts
  getInventoryAlerts: () => api.get('/admin/inventory/alerts'),
};

// =====================================
// STORE LOCATION API (Legacy - Keep for compatibility)
// =====================================
export const storeLocationAPI = {
  getAll: () => api.get('/store-locations'),
  getById: (id) => api.get(`/store-locations/${id}`),
};

// =====================================
// HELPER FUNCTIONS
// =====================================
export const helpers = {
  // Format price in KSh
  formatPrice: (amount) => {
    return `KSh ${parseFloat(amount).toLocaleString('en-KE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  },

  // Check if item is on sale
  isOnSale: (product) => {
    return product.sale_price && product.sale_price < product.price;
  },

  // Get discount percentage
  getDiscountPercent: (product) => {
    if (!product.sale_price || product.sale_price >= product.price) return 0;
    return Math.round(((product.price - product.sale_price) / product.price) * 100);
  },

  // Check if item can be returned
  canBeReturned: (product) => {
    // FINAL SALE: Clearance items cannot be returned
    if (product.is_clearance) return false;

    // FINAL SALE: Sale items cannot be returned
    if (product.is_on_sale || (product.sale_price && product.sale_price < product.price)) {
      return false;
    }

    // Regular-priced items can be returned
    return true;
  },

  // Get return policy message
  getReturnPolicyMessage: (product) => {
    if (product.is_clearance) {
      return 'FINAL SALE - No returns or exchanges';
    }

    if (product.is_on_sale || (product.sale_price && product.sale_price < product.price)) {
      return 'FINAL SALE - No returns or exchanges';
    }

    return 'Returns accepted within 2 days of delivery (10% restocking fee applies)';
  },
};

export default api;
