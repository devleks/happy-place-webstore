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
  const parentCategory = searchParams.get('parent_category');
  const search = searchParams.get('search');
  const page = searchParams.get('page') || 1;

  useEffect(() => {
    fetchProducts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category, parentCategory, search, page]);

  const fetchProducts = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = {
        page,
        per_page: 12,
      };

      if (category) params.category = category;
      if (parentCategory) params.parent_category = parentCategory;
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

  const getPageTitle = () => {
    if (search) {
      return `Search Results for "${search}"`;
    }
    if (parentCategory === 'women-clothing') {
      return "Women's Clothing";
    }
    if (parentCategory === 'maternity-clothing') {
      return "Maternity Clothing";
    }
    if (category) {
      return category
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    }
    return 'All Products';
  };

  const getCategoryColor = () => {
    if (parentCategory === 'maternity-clothing' || category?.includes('maternity')) {
      return 'maternity';
    }
    return 'womens';
  };

  return (
    <div className="products-page">
      <div className={`products-header header-${getCategoryColor()}`}>
        <h1>{getPageTitle()}</h1>
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
