import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Header.css';

const Header = () => {
  const { user, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [cartCount] = useState(0); // TODO: Connect to cart context
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/products?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="header">
      <div className="header-container">
        <div className="header-top">
          <Link to="/" className="logo">
            <h1>Happy Place Boutique</h1>
          </Link>

          <form className="search-form" onSubmit={handleSearch}>
            <input
              type="text"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            <button type="submit" className="search-button">Search</button>
          </form>

          <div className="user-actions">
            <Link to="/wishlist" className="icon-link" title="Wishlist">
              <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
              </svg>
            </Link>
            <Link to="/cart" className="icon-link cart-link" title="Shopping Cart">
              <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="9" cy="21" r="1"></circle>
                <circle cx="20" cy="21" r="1"></circle>
                <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
              </svg>
              {cartCount > 0 && <span className="cart-badge">{cartCount}</span>}
            </Link>
            {user ? (
              <>
                <span className="welcome-text">Welcome, {user.first_name}!</span>
                <button onClick={handleLogout} className="btn-link">Logout</button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn-link">Login</Link>
                <Link to="/register" className="btn-primary">Sign Up</Link>
              </>
            )}
          </div>
        </div>

        <nav className="nav">
          <Link to="/products" className="nav-link">Shop Online</Link>
          <Link to="/products?category=womens" className="nav-link">Women's Clothing</Link>
          <Link to="/products?category=maternity" className="nav-link">Maternity Clothing</Link>
          <Link to="/store-location" className="nav-link">Store Location</Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;
