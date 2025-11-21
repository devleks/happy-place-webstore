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
        <div className="categories-grid">
          <Link to="/products?category=womens" className="category-card">
            <div className="category-image" style={{ background: 'linear-gradient(135deg, #F7DFD4 0%, #F4E4E6 100%)' }}>
              <h3>Women's Clothing</h3>
            </div>
          </Link>
          <Link to="/products?category=maternity" className="category-card">
            <div className="category-image" style={{ background: 'linear-gradient(135deg, #FFF5F0 0%, #F7DFD4 100%)' }}>
              <h3>Maternity Clothing</h3>
            </div>
          </Link>
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
