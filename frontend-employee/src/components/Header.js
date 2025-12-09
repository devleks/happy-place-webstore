import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { useWishlist } from '../context/WishlistContext';
import '../styles/Header.css';

const Header = () => {
  const { user, logout } = useAuth();
  const { getCartCount } = useCart();
  const { getWishlistCount } = useWishlist();
  const [searchQuery, setSearchQuery] = useState('');
  const [showWomensMenu, setShowWomensMenu] = useState(false);
  const [showMaternityMenu, setShowMaternityMenu] = useState(false);
  const navigate = useNavigate();

  const cartCount = getCartCount();
  const wishlistCount = getWishlistCount();

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
            <h1>Happy Place</h1>
          </Link>

          <div className="user-actions">
            <Link to="/wishlist" className="icon-link wishlist-link" title="Wishlist">
              <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
              </svg>
              {wishlistCount > 0 && <span className="wishlist-badge">{wishlistCount}</span>}
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
                <Link to="/orders" className="btn-link">My Orders</Link>
                <button onClick={handleLogout} className="btn-link">Logout</button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn-link">Login</Link>
                <Link to="/register" className="btn-primary">Sign Up</Link>
              </>
            )}
          </div>

          <form className="search-form" onSubmit={handleSearch}>
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            <button type="submit" className="search-button" title="Search">
              <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
              </svg>
            </button>
          </form>
        </div>

        <nav className="nav">
          <Link to="/products" className="nav-link">All Products</Link>

          {/* Women's Clothing Dropdown */}
          <div
            className="nav-dropdown"
            onMouseEnter={() => setShowWomensMenu(true)}
            onMouseLeave={() => setShowWomensMenu(false)}
          >
            <Link to="/products?parent_category=women-clothing" className="nav-link womens-link">
              Women's Clothing ▾
            </Link>
            {showWomensMenu && (
              <div className="dropdown-menu womens-menu">
                <Link to="/products?parent_category=women-clothing" className="dropdown-item">All Women's</Link>
                <Link to="/products?category=women-tops" className="dropdown-item">Tops</Link>
                <Link to="/products?category=women-bottoms" className="dropdown-item">Bottoms</Link>
                <Link to="/products?category=women-dresses" className="dropdown-item">Dresses</Link>
                <Link to="/products?category=women-accessories" className="dropdown-item">Accessories</Link>
              </div>
            )}
          </div>

          {/* Maternity Clothing Dropdown */}
          <div
            className="nav-dropdown"
            onMouseEnter={() => setShowMaternityMenu(true)}
            onMouseLeave={() => setShowMaternityMenu(false)}
          >
            <Link to="/products?parent_category=maternity-clothing" className="nav-link maternity-link">
              Maternity Clothing ▾
            </Link>
            {showMaternityMenu && (
              <div className="dropdown-menu maternity-menu">
                <Link to="/products?parent_category=maternity-clothing" className="dropdown-item">All Maternity</Link>
                <Link to="/products?category=maternity-tops" className="dropdown-item">Maternity Tops</Link>
                <Link to="/products?category=maternity-bottoms" className="dropdown-item">Maternity Bottoms</Link>
                <Link to="/products?category=maternity-dresses" className="dropdown-item">Maternity Dresses</Link>
              </div>
            )}
          </div>

          <Link to="/store-location" className="nav-link">Store Location</Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;
