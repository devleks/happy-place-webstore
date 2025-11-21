import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/Home.css';

const Home = () => {
  return (
    <div className="home">
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title">Welcome to Happy Place Boutique</h1>
          <p className="hero-subtitle">
            Your destination for stylish women's and maternity clothing
          </p>
          <div className="hero-buttons">
            <Link to="/products" className="btn-primary-large">
              Shop Now
            </Link>
            <Link to="/store-location" className="btn-secondary-large">
              Visit Our Store
            </Link>
          </div>
        </div>
      </section>

      <section className="featured-categories">
        <h2 className="section-title">Shop by Category</h2>

        {/* Women's Clothing Section */}
        <div className="category-section">
          <h3 className="category-section-title">Women's Clothing</h3>
          <div className="category-products-grid">
            <Link to="/products/classic-cotton-tshirt" className="featured-product-card">
              <div className="featured-product-image">
                <img src="https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=600&fit=crop&q=80" alt="Classic Cotton T-Shirt" />
              </div>
              <div className="featured-product-info">
                <h4 className="featured-product-name">Classic Cotton T-Shirt</h4>
                <p className="featured-product-price">$29.99</p>
              </div>
            </Link>
            <Link to="/products/elegant-blouse" className="featured-product-card">
              <div className="featured-product-image">
                <img src="https://images.unsplash.com/photo-1485968579580-b6d095142e6e?w=400&h=600&fit=crop&q=80" alt="Elegant Blouse" />
              </div>
              <div className="featured-product-info">
                <h4 className="featured-product-name">Elegant Blouse</h4>
                <p className="featured-product-price">$49.99</p>
              </div>
            </Link>
          </div>
          <div className="category-link-wrapper">
            <Link to="/products?category=womens" className="btn-secondary-large">View All Women's</Link>
          </div>
        </div>

        {/* Maternity Clothing Section */}
        <div className="category-section">
          <h3 className="category-section-title">Maternity Clothing</h3>
          <div className="category-products-grid">
            <Link to="/products/maternity-basic-tee" className="featured-product-card">
              <div className="featured-product-image">
                <img src="https://images.unsplash.com/photo-1578587018452-892bacefd3f2?w=400&h=600&fit=crop&q=80" alt="Maternity Basic Tee" />
              </div>
              <div className="featured-product-info">
                <h4 className="featured-product-name">Maternity Basic Tee</h4>
                <p className="featured-product-price">$34.99</p>
              </div>
            </Link>
            <Link to="/products/maternity-wrap-top" className="featured-product-card">
              <div className="featured-product-image">
                <img src="https://images.unsplash.com/photo-1584363091550-0317fa71d41d?w=400&h=600&fit=crop&q=80" alt="Maternity Wrap Top" />
              </div>
              <div className="featured-product-info">
                <h4 className="featured-product-name">Maternity Wrap Top</h4>
                <p className="featured-product-price">$54.99</p>
              </div>
            </Link>
          </div>
          <div className="category-link-wrapper">
            <Link to="/products?category=maternity" className="btn-secondary-large">View All Maternity</Link>
          </div>
        </div>
      </section>

      <section className="about-section">
        <div className="about-content">
          <h2 className="section-title">About Happy Place Boutique</h2>
          <p>
            We're a local boutique specializing in women's and maternity clothing.
            Our mission is to help every woman feel confident and comfortable in what she wears,
            whether she's expecting or embracing her everyday style.
          </p>
          <p>
            Visit us in store or shop online - we offer the same great selection and personalized
            service both ways!
          </p>
        </div>
      </section>
    </div>
  );
};

export default Home;
