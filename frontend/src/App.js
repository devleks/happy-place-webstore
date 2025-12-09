import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthProvider } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import { WishlistProvider } from './context/WishlistContext';
import CustomerLayout from './components/CustomerLayout';
import Home from './pages/Home';
import Products from './pages/Products';
import ProductDetail from './pages/ProductDetail';
import Cart from './pages/Cart';
import Wishlist from './pages/Wishlist';
import Checkout from './pages/Checkout';
import OrderConfirmation from './pages/OrderConfirmation';
import OrderHistory from './pages/OrderHistory';
import CustomerLogin from './pages/CustomerLogin';
import CustomerDashboard from './pages/CustomerDashboard';
import EmployeeLogin from './pages/EmployeeLogin';
import Login from './pages/Login';
import Register from './pages/Register';
import StoreLocation from './pages/StoreLocation';
import PrivacyPolicy from './pages/PrivacyPolicy';
import TermsOfService from './pages/TermsOfService';
import ReturnPolicy from './pages/ReturnPolicy';
import POSLogin from './pages/POS/POSLogin';
import POSDashboard from './pages/POS/POSDashboard';
import POSNewSale from './pages/POS/POSNewSale';
import POSReceipt from './pages/POS/POSReceipt';
import POSCloseShift from './pages/POS/POSCloseShift';
import AdminLogin from './pages/admin/AdminLogin';
import AdminLayout from './components/admin/AdminLayout';
import ProtectedAdminRoute from './components/ProtectedAdminRoute';
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminInventory from './pages/admin/AdminInventory';
import AddProduct from './pages/admin/AddProduct';
import AdminOrders from './pages/admin/AdminOrders';
import AdminCustomers from './pages/admin/AdminCustomers';
import AdminEmployees from './pages/admin/AdminEmployees';
import AdminPromotions from './pages/admin/AdminPromotions';
import AdminReports from './pages/admin/AdminReports';
import AdminSettings from './pages/admin/AdminSettings';
import './styles/App.css';
import 'react-toastify/dist/ReactToastify.css';

const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || '';

// Only enable Google OAuth if client ID is properly configured
const isGoogleOAuthEnabled = GOOGLE_CLIENT_ID && GOOGLE_CLIENT_ID !== '';

function App() {
  const AppContent = (
    <AuthProvider>
      <CartProvider>
        <WishlistProvider>
          <Router>
              <div className="App">
                  <Routes>
                    {/* Customer-facing routes with Header/Footer */}
                    <Route element={<CustomerLayout />}>
                      <Route path="/" element={<Home />} />
                      <Route path="/products" element={<Products />} />
                      <Route path="/products/:slug" element={<ProductDetail />} />
                      <Route path="/cart" element={<Cart />} />
                      <Route path="/wishlist" element={<Wishlist />} />
                      <Route path="/checkout" element={<Checkout />} />
                      <Route path="/order-confirmation/:orderId" element={<OrderConfirmation />} />
                      <Route path="/orders" element={<OrderHistory />} />
                      <Route path="/customer/login" element={<CustomerLogin />} />
                      <Route path="/dashboard" element={<CustomerDashboard />} />
                      <Route path="/login" element={<Login />} />
                      <Route path="/register" element={<Register />} />
                      <Route path="/store-location" element={<StoreLocation />} />
                      <Route path="/privacy-policy" element={<PrivacyPolicy />} />
                      <Route path="/terms-of-service" element={<TermsOfService />} />
                      <Route path="/return-policy" element={<ReturnPolicy />} />
                    </Route>

                    {/* Employee Login - No Header/Footer */}
                    <Route path="/employee/login" element={<EmployeeLogin />} />

                    {/* POS Routes - No Header/Footer */}
                    <Route path="/pos/login" element={<POSLogin />} />
                    <Route path="/pos/dashboard" element={<POSDashboard />} />
                    <Route path="/pos/sale" element={<POSNewSale />} />
                    <Route path="/pos/receipt/:transactionId" element={<POSReceipt />} />
                    <Route path="/pos/close-shift" element={<POSCloseShift />} />

                    {/* Admin Routes - Separate AdminLayout with own header/sidebar */}
                    <Route path="/admin/login" element={<AdminLogin />} />
                    <Route path="/admin" element={
                      <ProtectedAdminRoute>
                        <AdminLayout />
                      </ProtectedAdminRoute>
                    }>
                      <Route index element={<Navigate to="/admin/dashboard" replace />} />
                      <Route path="dashboard" element={<AdminDashboard />} />
                      <Route path="inventory" element={<AdminInventory />} />
                      <Route path="inventory/add" element={<AddProduct />} />
                      <Route path="orders" element={<AdminOrders />} />
                      <Route path="customers" element={<AdminCustomers />} />
                      <Route path="employees" element={<AdminEmployees />} />
                      <Route path="promotions" element={<AdminPromotions />} />
                      <Route path="reports" element={<AdminReports />} />
                      <Route path="settings" element={<AdminSettings />} />
                    </Route>
                  </Routes>
              </div>
              <ToastContainer
                position="top-right"
                autoClose={3000}
                hideProgressBar={false}
                newestOnTop={false}
                closeOnClick
                rtl={false}
                pauseOnFocusLoss
                draggable
                pauseOnHover
                theme="light"
              />
            </Router>
          </WishlistProvider>
        </CartProvider>
      </AuthProvider>
  );

  // Conditionally wrap with GoogleOAuthProvider only if properly configured
  return isGoogleOAuthEnabled ? (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      {AppContent}
    </GoogleOAuthProvider>
  ) : (
    AppContent
  );
}

export default App;
