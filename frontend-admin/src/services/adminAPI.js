import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle errors
const handleError = (error) => {
  if (error.response) {
    // Backend can return error in 'error', 'message', or 'msg' field
    const errorMsg = error.response.data.error || 
                     error.response.data.message || 
                     error.response.data.msg ||
                     'An error occurred';
    throw new Error(errorMsg);
  } else if (error.request) {
    throw new Error('No response from server. Please check your connection.');
  } else {
    throw new Error(error.message || 'An unexpected error occurred');
  }
};

export const adminAPI = {
  // ========== Dashboard Methods ==========
  getMetrics: async (period = 'today') => {
    try {
      const response = await api.get(`/admin/dashboard/metrics?period=${period}`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  getRecentActivity: async () => {
    try {
      const response = await api.get('/admin/dashboard/activity');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  getAlerts: async () => {
    try {
      const response = await api.get('/admin/dashboard/alerts');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  // ========== Inventory Methods ==========
  getInventory: async () => {
    try {
      const response = await api.get('/admin/inventory');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  createProduct: async (productData) => {
    try {
      const response = await api.post('/admin/inventory', productData);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  updateStock: async (productId, data) => {
    try {
      const response = await api.post('/admin/inventory/adjust', {
        product_id: productId,
        quantity: data.quantity,
        reason: data.reason || 'Stock adjustment',
        notes: data.notes
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  bulkDeleteProducts: async (productIds) => {
    try {
      const response = await api.post('/admin/inventory/bulk-delete', { productIds });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  exportInventory: async (productIds) => {
    try {
      const response = await api.post(
        '/admin/inventory/export',
        { productIds },
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `inventory_${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  uploadProductImages: async (productId, imageFiles) => {
    try {
      const formData = new FormData();
      imageFiles.forEach((file, index) => {
        formData.append('images', file);
        // Mark first image as primary
        if (index === 0) {
          formData.append('primary_index', '0');
        }
      });

      const response = await api.post(`/admin/inventory/${productId}/images`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  // ========== Order Methods ==========
  getOrders: async () => {
    try {
      const response = await api.get('/admin/orders');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  updateOrderStatus: async (orderId, status) => {
    try {
      const response = await api.put(`/admin/orders/${orderId}/status`, { status });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  cancelOrder: async (orderId) => {
    try {
      const response = await api.post(`/admin/orders/${orderId}/cancel`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  refundOrder: async (orderId) => {
    try {
      const response = await api.post(`/admin/orders/${orderId}/refund`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  // Phase 1: Order Tracking Methods
  addOrderTracking: async (orderId, trackingData) => {
    try {
      const response = await api.post(`/admin/orders/${orderId}/tracking`, {
        tracking_number: trackingData.tracking_number,
        carrier: trackingData.carrier,
        estimated_delivery: trackingData.estimated_delivery,
        notes: trackingData.notes
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  getOrderTracking: async (orderId) => {
    try {
      const response = await api.get(`/admin/orders/${orderId}/tracking`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  getShippingCarriers: async () => {
    try {
      const response = await api.get('/admin/shipping/carriers');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  // Phase 1: Fulfillment Methods
  assignOrder: async (assignmentData) => {
    try {
      const response = await api.post('/fulfillment/assign', assignmentData);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  getOrderAssignments: async (orderId) => {
    try {
      const response = await api.get(`/fulfillment/assignments/${orderId}`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  // ========== Customer Methods ==========
  getCustomers: async () => {
    try {
      const response = await api.get('/admin/customers');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  getCustomerOrders: async (customerId) => {
    try {
      const response = await api.get(`/admin/customers/${customerId}/orders`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  exportCustomerData: async (customerId) => {
    try {
      const response = await api.get(`/admin/customers/${customerId}/export`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `customer_${customerId}_data.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  anonymizeCustomer: async (customerId) => {
    try {
      const response = await api.post(`/admin/customers/${customerId}/anonymize`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  deleteCustomer: async (customerId) => {
    try {
      const response = await api.delete(`/admin/customers/${customerId}`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  // ========== Employee Methods ==========
  getEmployees: async () => {
    try {
      const response = await api.get('/admin/employees');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  createEmployee: async (data) => {
    try {
      const response = await api.post('/admin/employees', data);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  updateEmployee: async (employeeId, data) => {
    try {
      const response = await api.put(`/admin/employees/${employeeId}`, data);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  deleteEmployee: async (employeeId) => {
    try {
      const response = await api.delete(`/admin/employees/${employeeId}`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  deactivateEmployee: async (employeeId) => {
    try {
      const response = await api.post(`/admin/employees/${employeeId}/deactivate`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  // ========== Promotion Methods ==========
  getPromotions: async () => {
    try {
      const response = await api.get('/admin/promotions');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  createPromotion: async (data) => {
    try {
      const response = await api.post('/admin/promotions', data);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  updatePromotion: async (promotionId, data) => {
    try {
      const response = await api.put(`/admin/promotions/${promotionId}`, data);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  togglePromotion: async (promotionId, isActive) => {
    try {
      const response = await api.put(`/admin/promotions/${promotionId}/toggle`, { isActive });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  deletePromotion: async (promotionId) => {
    try {
      const response = await api.delete(`/admin/promotions/${promotionId}`);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  // ========== Report Methods ==========
  getSalesReport: async (startDate, endDate) => {
    try {
      const response = await api.get('/admin/reports/sales', {
        params: { start_date: startDate, end_date: endDate },
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  getInventoryReport: async () => {
    try {
      const response = await api.get('/admin/reports/inventory');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  getCustomersReport: async (startDate, endDate) => {
    try {
      const response = await api.get('/admin/reports/customers', {
        params: { start_date: startDate, end_date: endDate },
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  getProductsReport: async (startDate, endDate) => {
    try {
      const response = await api.get('/admin/reports/products', {
        params: { start_date: startDate, end_date: endDate },
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  getEmployeesReport: async (startDate, endDate) => {
    try {
      const response = await api.get('/admin/reports/employees', {
        params: { start_date: startDate, end_date: endDate },
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  exportReport: async (reportType, startDate, endDate, format) => {
    try {
      const response = await api.get(`/admin/reports/${reportType}/export`, {
        params: { start_date: startDate, end_date: endDate, format },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${reportType}_report_${Date.now()}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  // ========== Settings Methods ==========
  getSettings: async () => {
    try {
      const response = await api.get('/admin/settings');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  updateSettings: async (section, data) => {
    try {
      const response = await api.put(`/admin/settings/${section}`, data);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  // ========== Currency Methods ==========
  getCurrencySettings: async () => {
    try {
      const response = await api.get('/admin/settings/currency');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  updateCurrencySettings: async (data) => {
    try {
      const response = await api.put('/admin/settings/currency', data);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },
};

export default adminAPI;
