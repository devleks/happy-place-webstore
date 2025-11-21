import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Header.css';

const Header = () => {
  const { user, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
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
