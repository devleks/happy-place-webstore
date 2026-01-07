import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
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
import TrackOrder from './pages/TrackOrder';
import CustomerLogin from './pages/CustomerLogin';
import CustomerDashboard from './pages/CustomerDashboard';
import Login from './pages/Login';
import Register from './pages/Register';
import StoreLocation from './pages/StoreLocation';
import PrivacyPolicy from './pages/PrivacyPolicy';
import TermsOfService from './pages/TermsOfService';
import ReturnPolicy from './pages/ReturnPolicy';
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
                      <Route path="/track-order/:orderId" element={<TrackOrder />} />
                      <Route path="/customer/login" element={<CustomerLogin />} />
                      <Route path="/dashboard" element={<CustomerDashboard />} />
                      <Route path="/login" element={<Login />} />
                      <Route path="/register" element={<Register />} />
                      <Route path="/store-location" element={<StoreLocation />} />
                      <Route path="/privacy-policy" element={<PrivacyPolicy />} />
                      <Route path="/terms-of-service" element={<TermsOfService />} />
                      <Route path="/return-policy" element={<ReturnPolicy />} />
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
