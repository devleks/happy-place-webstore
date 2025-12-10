import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/electronAPI';
import '../../styles/POSNewSale.css';

const POSNewSale = ({ employee: propEmployee }) => {
  const [employee, setEmployee] = useState(propEmployee);
  const [currentShift, setCurrentShift] = useState(null);
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checkoutMode, setCheckoutMode] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [cashTendered, setCashTendered] = useState('');
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const [barcodeBuffer, setBarcodeBuffer] = useState('');
  const [scanMessage, setScanMessage] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const employeeInfo = localStorage.getItem('employee_info');

    if (!employeeInfo && !propEmployee) {
      navigate('/login');
      return;
    }

    if (!employee) {
      setEmployee(JSON.parse(employeeInfo));
    }
    
    checkShiftAndLoadProducts();
  }, [navigate, propEmployee, employee]);

  // Barcode scanner listener
  useEffect(() => {
    let buffer = '';
    let timeout = null;

    const handleKeyPress = async (e) => {
      // Ignore if in checkout mode or typing in input fields
      if (checkoutMode || e.target.tagName === 'INPUT') {
        return;
      }

      // Most barcode scanners send characters quickly followed by Enter
      if (e.key === 'Enter') {
        if (buffer.length > 0) {
          // Process barcode
          await scanBarcode(buffer);
          buffer = '';
        }
      } else if (e.key.length === 1) {
        // Add character to buffer
        buffer += e.key;

        // Clear buffer after 100ms of no input (barcode scanners are fast)
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          buffer = '';
        }, 100);
      }
    };

    window.addEventListener('keypress', handleKeyPress);

    return () => {
      window.removeEventListener('keypress', handleKeyPress);
      clearTimeout(timeout);
    };
  }, [checkoutMode, cart]);

  const scanBarcode = async (barcode) => {
    try {
      setScanMessage(`Scanning: ${barcode}...`);

      // Search for product by SKU using Electron API
      const product = await api.product.getBySku(barcode);

      if (product) {
        // Create cart item from scanned product
        const cartItem = {
          product_id: product.id,
          product_sku: product.sku,
          product_name: product.name,
          sku: product.sku,
          price: product.effective_price,
          quantity: 1,
          available_stock: product.available_quantity
        };

        // Add to cart
        const existingIndex = cart.findIndex(item => item.variant_id === product.variant_id);

        if (existingIndex >= 0) {
          const newCart = [...cart];
          if (newCart[existingIndex].quantity < newCart[existingIndex].available_stock) {
            newCart[existingIndex].quantity += 1;
            setCart(newCart);
            setScanMessage(`✓ Added ${product.product_name} (${product.size}, ${product.color})`);
            playBeep();
          } else {
            setScanMessage(`✗ Not enough stock for ${product.product_name}`);
            playErrorBeep();
          }
        } else {
          if (cartItem.available_stock > 0) {
            setCart([...cart, cartItem]);
            setScanMessage(`✓ Added ${product.product_name} (${product.size}, ${product.color})`);
            playBeep();
          } else {
            setScanMessage(`✗ ${product.product_name} out of stock`);
            playErrorBeep();
          }
        }

        // Clear message after 3 seconds
        setTimeout(() => setScanMessage(''), 3000);
      } else {
        setScanMessage(`✗ Product not found: ${barcode}`);
        playErrorBeep();
        setTimeout(() => setScanMessage(''), 3000);
      }
    } catch (err) {
      console.error('Barcode scan error:', err);
      setScanMessage(`✗ Scan error`);
      playErrorBeep();
      setTimeout(() => setScanMessage(''), 3000);
    }
  };

  const playBeep = () => {
    // Simple beep sound using Web Audio API
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.value = 800;
      oscillator.type = 'sine';

      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.1);
    } catch (e) {
      // Audio not supported, silently fail
    }
  };

  const playErrorBeep = () => {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.value = 200;
      oscillator.type = 'sawtooth';

      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.2);
    } catch (e) {
      // Audio not supported, silently fail
    }
  };

  const checkShiftAndLoadProducts = async () => {
    try {
      // Check current shift from localStorage
      const shift = localStorage.getItem('current_shift');
      
      if (!shift) {
        alert('No active shift. Please start a shift first.');
        navigate('/dashboard');
        return;
      }

      setCurrentShift(JSON.parse(shift));

      // Load products using Electron API
      const productsData = await api.product.getAll();
      
      if (productsData) {
        setProducts(productsData);
        setFilteredProducts(productsData);
      }
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (term) => {
    setSearchTerm(term);
    if (!term.trim()) {
      setFilteredProducts(products);
      return;
    }

    const lowercaseTerm = term.toLowerCase();
    const filtered = products.filter(product =>
      product.name.toLowerCase().includes(lowercaseTerm) ||
      product.category?.toLowerCase().includes(lowercaseTerm) ||
      product.variants?.some(v => v.sku?.toLowerCase().includes(lowercaseTerm))
    );
    setFilteredProducts(filtered);
  };

  const addToCart = (product, variant) => {
    const cartItem = {
      product_id: product.id,
      variant_id: variant.id,
      product_name: product.name,
      size: variant.size,
      color: variant.color,
      sku: variant.sku,
      price: parseFloat(variant.price),
      quantity: 1,
      available_stock: variant.pos_stock || 0
    };

    const existingIndex = cart.findIndex(item => item.variant_id === variant.id);

    if (existingIndex >= 0) {
      const newCart = [...cart];
      if (newCart[existingIndex].quantity < newCart[existingIndex].available_stock) {
        newCart[existingIndex].quantity += 1;
        setCart(newCart);
      } else {
        alert('Not enough stock available');
      }
    } else {
      if (cartItem.available_stock > 0) {
        setCart([...cart, cartItem]);
      } else {
        alert('Product out of stock');
      }
    }
  };

  const updateQuantity = (index, newQuantity) => {
    if (newQuantity < 1) {
      removeFromCart(index);
      return;
    }

    const newCart = [...cart];
    if (newQuantity <= newCart[index].available_stock) {
      newCart[index].quantity = newQuantity;
      setCart(newCart);
    } else {
      alert('Not enough stock available');
    }
  };

  const removeFromCart = (index) => {
    setCart(cart.filter((_, i) => i !== index));
  };

  const calculateTotals = () => {
    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const tax = subtotal * 0.16; // 16% VAT
    const total = subtotal + tax;
    return { subtotal, tax, total };
  };

  const processTransaction = async () => {
    if (cart.length === 0) {
      alert('Cart is empty');
      return;
    }

    if (paymentMethod === 'cash' && (!cashTendered || parseFloat(cashTendered) < calculateTotals().total)) {
      alert('Insufficient cash tendered');
      return;
    }

    setProcessing(true);
    setError('');

    try {
      const { subtotal, tax, total } = calculateTotals();
      
      // Prepare transaction data
      const transactionData = {
        employee_id: employee.id,
        employee_name: employee.full_name,
        shift_id: currentShift.id,
        payment_method: paymentMethod,
        subtotal: subtotal,
        tax: tax,
        total: total,
        items: cart.map(item => ({
          product_id: item.product_id,
          product_name: item.product_name,
          sku: item.sku,
          quantity: item.quantity,
          unit_price: item.price,
          subtotal: item.price * item.quantity
        }))
      };

      if (paymentMethod === 'cash') {
        transactionData.cash_tendered = parseFloat(cashTendered);
        transactionData.change_given = change;
      }

      // Create transaction using Electron API
      const result = await api.transaction.create(transactionData);

      if (result && result.id) {
        // Update stock for each item
        for (const item of cart) {
          await api.product.updateStock(item.product_id, -item.quantity);
        }

        // Show success and navigate to receipt
        navigate(`/receipt/${result.id}`);
      } else {
        setError('Transaction failed');
      }
    } catch (err) {
      setError('Transaction error. Please try again.');
      console.error('Transaction error:', err);
    } finally {
      setProcessing(false);
    }
  };

  const formatCurrency = (amount) => {
    return `KSh ${parseFloat(amount).toLocaleString('en-KE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const { subtotal, tax, total } = calculateTotals();
  const change = paymentMethod === 'cash' && cashTendered ? Math.max(0, parseFloat(cashTendered) - total) : 0;

  if (loading) {
    return (
      <div className="pos-loading-screen">
        <div className="pos-loading-spinner"></div>
        <p>Loading POS...</p>
      </div>
    );
  }

  return (
    <div className="pos-new-sale">
      {/* Header */}
      <header className="pos-sale-header">
        <button className="back-btn" onClick={() => navigate('/dashboard')}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M19 12H5M5 12l7 7m-7-7l7-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Back
        </button>
        <h1>New Sale</h1>
        <div className="header-info">
          {scanMessage && (
            <span className={`scan-message ${scanMessage.includes('✓') ? 'success' : 'error'}`}>
              {scanMessage}
            </span>
          )}
          <span className="shift-badge">Shift #{currentShift?.shift_number}</span>
          <span className="employee-badge">{employee?.full_name}</span>
        </div>
      </header>

      {/* Main Content */}
      <div className="pos-sale-content">
        {/* Left: Product Search & Selection */}
        <div className="products-panel">
          <div className="search-box">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2"/>
              <path d="M21 21l-4.35-4.35" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <input
              type="text"
              placeholder="Search products, SKU, or scan barcode..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
            />
            <div className="barcode-indicator">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="6" width="2" height="12" fill="currentColor"/>
                <rect x="7" y="6" width="1" height="12" fill="currentColor"/>
                <rect x="10" y="6" width="2" height="12" fill="currentColor"/>
                <rect x="14" y="6" width="1" height="12" fill="currentColor"/>
                <rect x="17" y="6" width="3" height="12" fill="currentColor"/>
              </svg>
              <span>Scanner Ready</span>
            </div>
          </div>

          <div className="products-grid">
            {filteredProducts.length === 0 ? (
              <div className="no-products">
                <p>No products found</p>
              </div>
            ) : (
              filteredProducts.map(product => (
                <div key={product.id} className="product-card">
                  <div className="product-info">
                    <h3>{product.name}</h3>
                    <p className="product-category">{product.category}</p>
                  </div>

                  {product.variants && product.variants.length > 0 && (
                    <div className="variants-list">
                      {product.variants.map(variant => (
                        <div
                          key={variant.id}
                          className={`variant-item ${variant.pos_stock <= 0 ? 'out-of-stock' : ''}`}
                          onClick={() => variant.pos_stock > 0 && addToCart(product, variant)}
                          title={formatSizeWithConversions(variant.size)}
                        >
                          <div className="variant-details">
                            <span className="variant-size">{variant.size}</span>
                            <span className="variant-color">{variant.color}</span>
                            <span className="variant-stock">Stock: {variant.pos_stock || 0}</span>
                          </div>
                          <div className="variant-price">{formatCurrency(variant.price)}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right: Cart & Checkout */}
        <div className="cart-panel">
          <div className="cart-header">
            <h2>Cart ({cart.length})</h2>
            {cart.length > 0 && (
              <button className="clear-cart-btn" onClick={() => setCart([])}>
                Clear All
              </button>
            )}
          </div>

          <div className="cart-items">
            {cart.length === 0 ? (
              <div className="empty-cart">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                  <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" stroke="currentColor" strokeWidth="1.5"/>
                </svg>
                <p>Cart is empty</p>
                <small>Search and add products to start</small>
              </div>
            ) : (
              cart.map((item, index) => (
                <div key={index} className="cart-item">
                  <div className="item-details">
                    <h4>{item.product_name}</h4>
                    <p>{item.size}, {item.color}</p>
                    <span className="item-price">{formatCurrency(item.price)}</span>
                  </div>

                  <div className="item-controls">
                    <div className="quantity-controls">
                      <button onClick={() => updateQuantity(index, item.quantity - 1)}>-</button>
                      <span>{item.quantity}</span>
                      <button onClick={() => updateQuantity(index, item.quantity + 1)}>+</button>
                    </div>
                    <div className="item-total">{formatCurrency(item.price * item.quantity)}</div>
                    <button className="remove-btn" onClick={() => removeFromCart(index)}>×</button>
                  </div>
                </div>
              ))
            )}
          </div>

          {cart.length > 0 && (
            <>
              <div className="cart-summary">
                <div className="summary-row">
                  <span>Subtotal:</span>
                  <span>{formatCurrency(subtotal)}</span>
                </div>
                <div className="summary-row">
                  <span>VAT (16%):</span>
                  <span>{formatCurrency(tax)}</span>
                </div>
                <div className="summary-row total">
                  <span>Total:</span>
                  <span>{formatCurrency(total)}</span>
                </div>
              </div>

              {!checkoutMode ? (
                <button className="checkout-btn" onClick={() => setCheckoutMode(true)}>
                  Proceed to Payment
                </button>
              ) : (
                <div className="payment-section">
                  {error && <div className="payment-error">{error}</div>}

                  <div className="payment-methods">
                    <button
                      className={`payment-method-btn ${paymentMethod === 'cash' ? 'active' : ''}`}
                      onClick={() => setPaymentMethod('cash')}
                    >
                      Cash
                    </button>
                    <button
                      className={`payment-method-btn ${paymentMethod === 'mpesa' ? 'active' : ''}`}
                      onClick={() => setPaymentMethod('mpesa')}
                    >
                      M-Pesa
                    </button>
                    <button
                      className={`payment-method-btn ${paymentMethod === 'card' ? 'active' : ''}`}
                      onClick={() => setPaymentMethod('card')}
                    >
                      Card
                    </button>
                  </div>

                  {paymentMethod === 'cash' && (
                    <div className="cash-input-section">
                      <label>Cash Tendered</label>
                      <input
                        type="number"
                        value={cashTendered}
                        onChange={(e) => setCashTendered(e.target.value)}
                        placeholder="0.00"
                        step="0.01"
                      />
                      {cashTendered && parseFloat(cashTendered) >= total && (
                        <div className="change-display">
                          <span>Change:</span>
                          <strong>{formatCurrency(change)}</strong>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="payment-actions">
                    <button className="cancel-btn" onClick={() => setCheckoutMode(false)}>
                      Back
                    </button>
                    <button
                      className="complete-btn"
                      onClick={processTransaction}
                      disabled={processing}
                    >
                      {processing ? 'Processing...' : 'Complete Sale'}
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default POSNewSale;
