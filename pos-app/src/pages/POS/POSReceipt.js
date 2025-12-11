import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../../services/electronAPI';
import '../../styles/POSReceipt.css';

const POSReceipt = () => {
  const [transaction, setTransaction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { transactionId } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    loadTransactionReceipt();
  }, [transactionId, navigate]);

  const loadTransactionReceipt = async () => {
    try {
      // Load transaction using Electron API
      const data = await api.transaction.getById(transactionId);

      if (data) {
        setTransaction(data);
      } else {
        setError('Failed to load receipt');
      }
    } catch (err) {
      console.error('Error loading receipt:', err);
      setError('Transaction not found');
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = async () => {
    try {
      // Use Electron hardware API to print receipt
      await api.hardware.printReceipt(transaction);
    } catch (err) {
      console.error('Print error:', err);
      // Fallback to browser print
      window.print();
    }
  };

  const handleNewSale = () => {
    navigate('/pos/sale');
  };

  const handleBackToDashboard = () => {
    navigate('/dashboard');
  };

  const formatCurrency = (amount) => {
    return `KSh ${parseFloat(amount).toLocaleString('en-KE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString('en-KE', { year: 'numeric', month: 'long', day: 'numeric' }),
      time: date.toLocaleTimeString('en-KE', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };
  };

  if (loading) {
    return (
      <div className="pos-loading-screen">
        <div className="pos-loading-spinner"></div>
        <p>Loading Receipt...</p>
      </div>
    );
  }

  if (error || !transaction) {
    return (
      <div className="pos-receipt-error">
        <div className="error-content">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="#e74c3c" strokeWidth="2"/>
            <path d="M12 8v4m0 4h.01" stroke="#e74c3c" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          <h2>Receipt Not Found</h2>
          <p>{error || 'Unable to load transaction receipt'}</p>
          <button className="back-to-dashboard-btn" onClick={handleBackToDashboard}>
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const { date, time } = formatDateTime(transaction.transaction_time);

  return (
    <div className="pos-receipt-page">
      {/* Action Bar - Hidden in Print */}
      <div className="receipt-actions no-print">
        <button className="action-btn secondary" onClick={handleBackToDashboard}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M19 12H5M5 12l7 7m-7-7l7-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Dashboard
        </button>
        <div className="action-group">
          <button className="action-btn" onClick={handlePrint}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Print
          </button>
          <button className="action-btn primary" onClick={handleNewSale}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M12 4v16m8-8H4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            New Sale
          </button>
        </div>
      </div>

      {/* Receipt Content */}
      <div className="receipt-container">
        <div className="receipt-paper">
          {/* Header */}
          <div className="receipt-header">
            <div className="store-logo">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="#9b59b6" strokeWidth="2"/>
                <path d="M8 12h8M12 8v8" stroke="#9b59b6" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </div>
            <h1>Happy Place Boutique</h1>
            <p className="store-tagline">Your Happy Place for Fashion</p>
            <div className="store-details">
              <p>Kimathi Street, Nairobi</p>
              <p>Tel: +254 700 123 456</p>
              <p>Email: hello@happyplace.co.ke</p>
            </div>
          </div>

          <div className="receipt-divider"></div>

          {/* Transaction Info */}
          <div className="receipt-section">
            <h2>SALES RECEIPT</h2>
            <div className="receipt-info-grid">
              <div className="info-item">
                <span className="info-label">Transaction #:</span>
                <span className="info-value">{transaction.transaction_number}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Date:</span>
                <span className="info-value">{date}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Time:</span>
                <span className="info-value">{time}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Shift #:</span>
                <span className="info-value">{transaction.shift_number}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Cashier:</span>
                <span className="info-value">{transaction.employee_name}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Payment:</span>
                <span className="info-value payment-method">{transaction.payment_method.toUpperCase()}</span>
              </div>
            </div>
          </div>

          <div className="receipt-divider"></div>

          {/* Items */}
          <div className="receipt-section">
            <h3>Items Purchased</h3>
            <table className="receipt-items-table">
              <thead>
                <tr>
                  <th className="text-left">Item</th>
                  <th className="text-center">Qty</th>
                  <th className="text-right">Price</th>
                  <th className="text-right">Total</th>
                </tr>
              </thead>
              <tbody>
                {transaction.items && transaction.items.map((item, index) => (
                  <tr key={index}>
                    <td className="item-details">
                      <div className="item-name">{item.product_name}</div>
                      <div className="item-variant">{item.size}, {item.color}</div>
                      <div className="item-sku">SKU: {item.sku}</div>
                    </td>
                    <td className="text-center item-quantity">{item.quantity}</td>
                    <td className="text-right item-price">{formatCurrency(item.unit_price)}</td>
                    <td className="text-right item-total">{formatCurrency(item.subtotal)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="receipt-divider"></div>

          {/* Totals */}
          <div className="receipt-section">
            <div className="receipt-totals">
              <div className="total-row">
                <span>Subtotal:</span>
                <span>{formatCurrency(transaction.subtotal)}</span>
              </div>
              <div className="total-row">
                <span>VAT (16%):</span>
                <span>{formatCurrency(transaction.tax_amount)}</span>
              </div>
              <div className="total-row grand-total">
                <span>TOTAL:</span>
                <span>{formatCurrency(transaction.total_amount)}</span>
              </div>

              {transaction.payment_method === 'cash' && (
                <>
                  <div className="total-row payment-detail">
                    <span>Cash Tendered:</span>
                    <span>{formatCurrency(transaction.cash_tendered)}</span>
                  </div>
                  <div className="total-row payment-detail change">
                    <span>Change:</span>
                    <span>{formatCurrency(transaction.change_given)}</span>
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="receipt-divider"></div>

          {/* Footer */}
          <div className="receipt-footer">
            <p className="thank-you">Thank you for shopping with us!</p>
            <p className="return-policy">Returns accepted within 14 days with receipt</p>
            <p className="vat-info">VAT Reg: KE-12345678Z</p>

            <div className="receipt-barcode">
              <svg width="200" height="60" viewBox="0 0 200 60">
                {/* Simple barcode representation */}
                <rect x="10" y="10" width="3" height="40" fill="#000"/>
                <rect x="15" y="10" width="1" height="40" fill="#000"/>
                <rect x="18" y="10" width="2" height="40" fill="#000"/>
                <rect x="22" y="10" width="4" height="40" fill="#000"/>
                <rect x="28" y="10" width="1" height="40" fill="#000"/>
                <rect x="31" y="10" width="3" height="40" fill="#000"/>
                <rect x="36" y="10" width="2" height="40" fill="#000"/>
                <rect x="40" y="10" width="1" height="40" fill="#000"/>
                <rect x="43" y="10" width="4" height="40" fill="#000"/>
                <rect x="49" y="10" width="2" height="40" fill="#000"/>
                <rect x="53" y="10" width="1" height="40" fill="#000"/>
                <rect x="56" y="10" width="3" height="40" fill="#000"/>
                <rect x="61" y="10" width="2" height="40" fill="#000"/>
                <rect x="65" y="10" width="4" height="40" fill="#000"/>
                <rect x="71" y="10" width="1" height="40" fill="#000"/>
                <rect x="74" y="10" width="2" height="40" fill="#000"/>
                <rect x="78" y="10" width="3" height="40" fill="#000"/>
                <rect x="83" y="10" width="1" height="40" fill="#000"/>
                <rect x="86" y="10" width="4" height="40" fill="#000"/>
                <rect x="92" y="10" width="2" height="40" fill="#000"/>
              </svg>
            </div>

            <p className="receipt-number">{transaction.transaction_number}</p>
            <p className="website">www.happyplace.co.ke</p>
          </div>
        </div>
      </div>

      {/* Success Message - Hidden in Print */}
      <div className="receipt-success-banner no-print">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="#16a34a" strokeWidth="2"/>
          <path d="M9 12l2 2 4-4" stroke="#16a34a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span>Transaction completed successfully!</span>
      </div>
    </div>
  );
};

export default POSReceipt;
