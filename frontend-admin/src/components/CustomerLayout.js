import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';

/**
 * Layout wrapper for customer-facing pages
 * Includes the Header component with navigation, cart, wishlist
 */
const CustomerLayout = () => {
  return (
    <>
      <Header />
      <main className="main-content">
        <Outlet />
      </main>
      <footer className="footer">
        <div className="footer-content">
          <p>&copy; 2024 Happy Place Boutique. All rights reserved.</p>
          <div className="footer-links">
            <a href="/privacy-policy">Privacy Policy</a>
            <a href="/terms-of-service">Terms of Service</a>
            <a href="/return-policy">Return Policy</a>
          </div>
        </div>
      </footer>
    </>
  );
};

export default CustomerLayout;
