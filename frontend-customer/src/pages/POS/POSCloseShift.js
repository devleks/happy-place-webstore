import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../../styles/POSCloseShift.css';

const POSCloseShift = () => {
  const [employee, setEmployee] = useState(null);
  const [currentShift, setCurrentShift] = useState(null);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState(1); // 1: Review, 2: Count Cash, 3: Confirm
  const [cashCount, setCashCount] = useState({
    notes_1000: 0,
    notes_500: 0,
    notes_200: 0,
    notes_100: 0,
    notes_50: 0,
    coins_20: 0,
    coins_10: 0,
    coins_5: 0,
    coins_1: 0
  });
  const [notes, setNotes] = useState('');
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('employee_token');
    const employeeInfo = localStorage.getItem('employee_info');

    if (!token || !employeeInfo) {
      navigate('/pos/login');
      return;
    }

    setEmployee(JSON.parse(employeeInfo));
    loadShiftData(token);
  }, [navigate]);

  const loadShiftData = async (token) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/api/pos/shifts/current', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await response.json();

      if (response.ok && data.shift) {
        setCurrentShift(data.shift);
      } else {
        alert('No active shift found');
        navigate('/pos/dashboard');
      }
    } catch (err) {
      console.error('Error loading shift:', err);
      setError('Failed to load shift data');
    } finally {
      setLoading(false);
    }
  };

  const handleCashCountChange = (denomination, value) => {
    setCashCount(prev => ({
      ...prev,
      [denomination]: parseInt(value) || 0
    }));
  };

  const calculateCashTotal = () => {
    const total =
      (cashCount.notes_1000 * 1000) +
      (cashCount.notes_500 * 500) +
      (cashCount.notes_200 * 200) +
      (cashCount.notes_100 * 100) +
      (cashCount.notes_50 * 50) +
      (cashCount.coins_20 * 20) +
      (cashCount.coins_10 * 10) +
      (cashCount.coins_5 * 5) +
      (cashCount.coins_1 * 1);
    return total;
  };

  const calculateExpectedCash = () => {
    const openingFloat = parseFloat(currentShift?.opening_float || 0);
    const cashSales = parseFloat(currentShift?.cash_sales || 0);
    return openingFloat + cashSales;
  };

  const calculateVariance = () => {
    return calculateCashTotal() - calculateExpectedCash();
  };

  const handleCloseShift = async () => {
    setProcessing(true);
    setError('');

    const token = localStorage.getItem('employee_token');

    try {
      const response = await fetch('http://127.0.0.1:5001/api/pos/shifts/close', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          closing_cash_count: calculateCashTotal(),
          cash_variance: calculateVariance(),
          notes: notes
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        alert('Shift closed successfully!');
        navigate('/pos/dashboard');
      } else {
        setError(data.error || 'Failed to close shift');
      }
    } catch (err) {
      setError('Connection error. Please try again.');
      console.error('Close shift error:', err);
    } finally {
      setProcessing(false);
    }
  };

  const formatCurrency = (amount) => {
    return `KSh ${parseFloat(amount).toLocaleString('en-KE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-KE', { hour: '2-digit', minute: '2-digit' });
  };

  const formatDuration = (start) => {
    const startTime = new Date(start);
    const now = new Date();
    const diff = now - startTime;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${minutes}m`;
  };

  if (loading) {
    return (
      <div className="pos-loading-screen">
        <div className="pos-loading-spinner"></div>
        <p>Loading Shift Data...</p>
      </div>
    );
  }

  const cashTotal = calculateCashTotal();
  const expectedCash = calculateExpectedCash();
  const variance = calculateVariance();

  return (
    <div className="pos-close-shift">
      {/* Header */}
      <header className="close-shift-header">
        <button className="back-btn" onClick={() => navigate('/pos/dashboard')}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M19 12H5M5 12l7 7m-7-7l7-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Back
        </button>
        <h1>Close Shift</h1>
        <div className="header-info">
          <span className="shift-badge">Shift #{currentShift?.shift_number}</span>
          <span className="employee-badge">{employee?.full_name}</span>
        </div>
      </header>

      {/* Main Content */}
      <div className="close-shift-content">
        {/* Progress Indicator */}
        <div className="progress-steps">
          <div className={`progress-step ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
            <div className="step-number">1</div>
            <div className="step-label">Review Shift</div>
          </div>
          <div className="progress-line"></div>
          <div className={`progress-step ${step >= 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>
            <div className="step-number">2</div>
            <div className="step-label">Count Cash</div>
          </div>
          <div className="progress-line"></div>
          <div className={`progress-step ${step >= 3 ? 'active' : ''}`}>
            <div className="step-number">3</div>
            <div className="step-label">Confirm</div>
          </div>
        </div>

        {error && <div className="error-banner">{error}</div>}

        {/* Step 1: Review Shift */}
        {step === 1 && (
          <div className="step-content">
            <div className="shift-summary-card">
              <h2>Shift Summary</h2>

              <div className="summary-section">
                <h3>Shift Details</h3>
                <div className="summary-grid">
                  <div className="summary-item">
                    <span className="label">Shift Number:</span>
                    <span className="value">#{currentShift.shift_number}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Started:</span>
                    <span className="value">{formatTime(currentShift.start_time)}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Duration:</span>
                    <span className="value">{formatDuration(currentShift.start_time)}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Opening Float:</span>
                    <span className="value">{formatCurrency(currentShift.opening_float)}</span>
                  </div>
                </div>
              </div>

              <div className="summary-section">
                <h3>Sales Summary</h3>
                <div className="stats-grid">
                  <div className="stat-box">
                    <div className="stat-label">Total Sales</div>
                    <div className="stat-value large">{formatCurrency(currentShift.total_sales || 0)}</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-label">Transactions</div>
                    <div className="stat-value">{currentShift.transaction_count || 0}</div>
                  </div>
                </div>
              </div>

              <div className="summary-section">
                <h3>Payment Breakdown</h3>
                <div className="payment-breakdown">
                  <div className="payment-row">
                    <span className="payment-label">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" strokeWidth="2"/>
                      </svg>
                      Cash
                    </span>
                    <span className="payment-value">{formatCurrency(currentShift.cash_sales || 0)}</span>
                  </div>
                  <div className="payment-row">
                    <span className="payment-label">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <path d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                      M-Pesa
                    </span>
                    <span className="payment-value">{formatCurrency(currentShift.mpesa_sales || 0)}</span>
                  </div>
                  <div className="payment-row">
                    <span className="payment-label">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <rect x="1" y="4" width="22" height="16" rx="2" stroke="currentColor" strokeWidth="2"/>
                        <path d="M1 10h22" stroke="currentColor" strokeWidth="2"/>
                      </svg>
                      Card
                    </span>
                    <span className="payment-value">{formatCurrency(currentShift.card_sales || 0)}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="step-actions">
              <button className="btn-cancel" onClick={() => navigate('/pos/dashboard')}>
                Cancel
              </button>
              <button className="btn-next" onClick={() => setStep(2)}>
                Proceed to Cash Count
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Count Cash */}
        {step === 2 && (
          <div className="step-content">
            <div className="cash-count-card">
              <h2>Count Cash Drawer</h2>
              <p className="instruction">Count all cash in the drawer and enter quantities below</p>

              <div className="cash-count-section">
                <h3>Notes</h3>
                <div className="denomination-grid">
                  <div className="denomination-item">
                    <label>KSh 1,000</label>
                    <input
                      type="number"
                      min="0"
                      value={cashCount.notes_1000}
                      onChange={(e) => handleCashCountChange('notes_1000', e.target.value)}
                    />
                    <span className="subtotal">{formatCurrency(cashCount.notes_1000 * 1000)}</span>
                  </div>
                  <div className="denomination-item">
                    <label>KSh 500</label>
                    <input
                      type="number"
                      min="0"
                      value={cashCount.notes_500}
                      onChange={(e) => handleCashCountChange('notes_500', e.target.value)}
                    />
                    <span className="subtotal">{formatCurrency(cashCount.notes_500 * 500)}</span>
                  </div>
                  <div className="denomination-item">
                    <label>KSh 200</label>
                    <input
                      type="number"
                      min="0"
                      value={cashCount.notes_200}
                      onChange={(e) => handleCashCountChange('notes_200', e.target.value)}
                    />
                    <span className="subtotal">{formatCurrency(cashCount.notes_200 * 200)}</span>
                  </div>
                  <div className="denomination-item">
                    <label>KSh 100</label>
                    <input
                      type="number"
                      min="0"
                      value={cashCount.notes_100}
                      onChange={(e) => handleCashCountChange('notes_100', e.target.value)}
                    />
                    <span className="subtotal">{formatCurrency(cashCount.notes_100 * 100)}</span>
                  </div>
                  <div className="denomination-item">
                    <label>KSh 50</label>
                    <input
                      type="number"
                      min="0"
                      value={cashCount.notes_50}
                      onChange={(e) => handleCashCountChange('notes_50', e.target.value)}
                    />
                    <span className="subtotal">{formatCurrency(cashCount.notes_50 * 50)}</span>
                  </div>
                </div>
              </div>

              <div className="cash-count-section">
                <h3>Coins</h3>
                <div className="denomination-grid">
                  <div className="denomination-item">
                    <label>KSh 20</label>
                    <input
                      type="number"
                      min="0"
                      value={cashCount.coins_20}
                      onChange={(e) => handleCashCountChange('coins_20', e.target.value)}
                    />
                    <span className="subtotal">{formatCurrency(cashCount.coins_20 * 20)}</span>
                  </div>
                  <div className="denomination-item">
                    <label>KSh 10</label>
                    <input
                      type="number"
                      min="0"
                      value={cashCount.coins_10}
                      onChange={(e) => handleCashCountChange('coins_10', e.target.value)}
                    />
                    <span className="subtotal">{formatCurrency(cashCount.coins_10 * 10)}</span>
                  </div>
                  <div className="denomination-item">
                    <label>KSh 5</label>
                    <input
                      type="number"
                      min="0"
                      value={cashCount.coins_5}
                      onChange={(e) => handleCashCountChange('coins_5', e.target.value)}
                    />
                    <span className="subtotal">{formatCurrency(cashCount.coins_5 * 5)}</span>
                  </div>
                  <div className="denomination-item">
                    <label>KSh 1</label>
                    <input
                      type="number"
                      min="0"
                      value={cashCount.coins_1}
                      onChange={(e) => handleCashCountChange('coins_1', e.target.value)}
                    />
                    <span className="subtotal">{formatCurrency(cashCount.coins_1 * 1)}</span>
                  </div>
                </div>
              </div>

              <div className="cash-total-display">
                <span>Total Cash Counted:</span>
                <span className="total-amount">{formatCurrency(cashTotal)}</span>
              </div>
            </div>

            <div className="step-actions">
              <button className="btn-back" onClick={() => setStep(1)}>
                Back
              </button>
              <button className="btn-next" onClick={() => setStep(3)}>
                Continue to Confirmation
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Confirm */}
        {step === 3 && (
          <div className="step-content">
            <div className="confirmation-card">
              <h2>Confirm Shift Closure</h2>

              <div className="variance-display">
                <div className="variance-row">
                  <span>Expected Cash:</span>
                  <span>{formatCurrency(expectedCash)}</span>
                </div>
                <div className="variance-row">
                  <span>Actual Cash Counted:</span>
                  <span>{formatCurrency(cashTotal)}</span>
                </div>
                <div className={`variance-row variance ${variance === 0 ? 'balanced' : variance > 0 ? 'over' : 'short'}`}>
                  <span>Variance:</span>
                  <span className="variance-amount">
                    {variance > 0 ? '+' : ''}{formatCurrency(Math.abs(variance))}
                    {variance > 0 ? ' OVER' : variance < 0 ? ' SHORT' : ' BALANCED'}
                  </span>
                </div>
              </div>

              {Math.abs(variance) > 0 && (
                <div className="variance-warning">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <div>
                    <strong>Cash variance detected</strong>
                    <p>Please double-check your cash count or add notes explaining the variance.</p>
                  </div>
                </div>
              )}

              <div className="notes-section">
                <label>Shift Notes (Optional)</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add any notes about the shift, issues encountered, or variance explanation..."
                  rows="4"
                ></textarea>
              </div>

              <div className="final-summary">
                <h3>Final Shift Summary</h3>
                <div className="summary-grid">
                  <div className="summary-item">
                    <span className="label">Total Sales:</span>
                    <span className="value">{formatCurrency(currentShift.total_sales || 0)}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Transactions:</span>
                    <span className="value">{currentShift.transaction_count || 0}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Duration:</span>
                    <span className="value">{formatDuration(currentShift.start_time)}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="step-actions">
              <button className="btn-back" onClick={() => setStep(2)}>
                Back
              </button>
              <button
                className="btn-close-shift"
                onClick={handleCloseShift}
                disabled={processing}
              >
                {processing ? 'Closing Shift...' : 'Close Shift'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default POSCloseShift;
