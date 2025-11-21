import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { productsAPI } from '../services/api';
import ProductCard from '../components/ProductCard';
import '../styles/Products.css';

const Products = () => {
  const [searchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({});

  const category = searchParams.get('category');
  const search = searchParams.get('search');
  const page = searchParams.get('page') || 1;

  useEffect(() => {
    fetchProducts();
  }, [category, search, page]);

  const fetchProducts = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = {
        page,
        per_page: 12,
      };

      if (category) params.category = category;
      if (search) params.search = search;

      const response = await productsAPI.getAll(params);
      setProducts(response.data.products);
      setPagination({
        total: response.data.total,
        pages: response.data.pages,
        current_page: response.data.current_page,
      });
    } catch (err) {
      setError('Failed to load products. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="products-page">
      <div className="products-header">
        <h1>
          {search
            ? `Search Results for "${search}"`
            : category
            ? category.replace('-', ' ').replace(/\b\w/g, (l) => l.toUpperCase())
            : 'All Products'}
        </h1>
        <p className="results-count">
          {pagination.total ? `${pagination.total} products found` : ''}
        </p>
      </div>

      {loading ? (
        <div className="loading">Loading products...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : products.length === 0 ? (
        <div className="no-results">
          <p>No products found.</p>
        </div>
      ) : (
        <>
          <div className="products-grid">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>

          {pagination.pages > 1 && (
            <div className="pagination">
              {Array.from({ length: pagination.pages }, (_, i) => i + 1).map((pageNum) => (
                <a
                  key={pageNum}
                  href={`?${new URLSearchParams({ ...Object.fromEntries(searchParams), page: pageNum })}`}
                  className={`page-link ${pageNum === pagination.current_page ? 'active' : ''}`}
                >
                  {pageNum}
                </a>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Products;
