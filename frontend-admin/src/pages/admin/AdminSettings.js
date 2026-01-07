import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { adminAPI } from '../../services/adminAPI';
import '../../styles/AdminDashboard.css';

const AdminSettings = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState('store');
  const [currencySettings, setCurrencySettings] = useState({
    currency: 'KSh',
    currency_code: 'KES',
  });
  const [settings, setSettings] = useState({
    store: {
      name: '',
      email: '',
      phone: '',
      address: '',
      city: '',
      state: '',
      zip_code: '',
      country: '',
      tax_rate: '',
    },
    business: {
      monday_open: '09:00',
      monday_close: '17:00',
      tuesday_open: '09:00',
      tuesday_close: '17:00',
      wednesday_open: '09:00',
      wednesday_close: '17:00',
      thursday_open: '09:00',
      thursday_close: '17:00',
      friday_open: '09:00',
      friday_close: '17:00',
      saturday_open: '10:00',
      saturday_close: '16:00',
      sunday_open: '',
      sunday_close: '',
    },
    payment: {
      stripe_enabled: false,
      stripe_publishable_key: '',
      stripe_secret_key: '',
      paypal_enabled: false,
      paypal_client_id: '',
      cash_enabled: true,
    },
    notification: {
      email_notifications: true,
      low_stock_alert: true,
      order_notifications: true,
      customer_notifications: true,
    },
  });

  useEffect(() => {
    // Only admins can access settings
    if (!user || user.role !== 'admin') {
      navigate('/admin/login');
      return;
    }

    fetchSettings();
  }, [user, navigate]);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const data = await adminAPI.getSettings();
      setSettings({
        store: data.store || settings.store,
        business: data.business || settings.business,
        payment: data.payment || settings.payment,
        notification: data.notification || settings.notification,
      });

      // Fetch currency settings
      const currencyData = await adminAPI.getCurrencySettings();
      if (currencyData.success) {
        setCurrencySettings({
          currency: currencyData.currency,
          currency_code: currencyData.currency_code,
        });
      }

      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load settings');
      console.error('Settings error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (section) => {
    try {
      await adminAPI.updateSettings(section, settings[section]);
      setSuccess(`${section.charAt(0).toUpperCase() + section.slice(1)} settings saved successfully`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message || 'Failed to save settings');
    }
  };

  const handleCurrencyUpdate = async () => {
    try {
      await adminAPI.updateCurrencySettings(currencySettings);
      setSuccess('Currency settings updated successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message || 'Failed to update currency');
    }
  };

  const renderStoreSettings = () => (
    <div className="settings-section">
      <h2>Store Information</h2>
      <div className="form-group">
        <label>Store Name *</label>
        <input
          type="text"
          value={settings.store.name}
          onChange={(e) =>
            setSettings({
              ...settings,
              store: { ...settings.store, name: e.target.value },
            })
          }
          className="form-input"
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Email *</label>
          <input
            type="email"
            value={settings.store.email}
            onChange={(e) =>
              setSettings({
                ...settings,
                store: { ...settings.store, email: e.target.value },
              })
            }
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label>Phone *</label>
          <input
            type="tel"
            value={settings.store.phone}
            onChange={(e) =>
              setSettings({
                ...settings,
                store: { ...settings.store, phone: e.target.value },
              })
            }
            className="form-input"
          />
        </div>
      </div>

      <div className="form-group">
        <label>Address *</label>
        <input
          type="text"
          value={settings.store.address}
          onChange={(e) =>
            setSettings({
              ...settings,
              store: { ...settings.store, address: e.target.value },
            })
          }
          className="form-input"
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>City *</label>
          <input
            type="text"
            value={settings.store.city}
            onChange={(e) =>
              setSettings({
                ...settings,
                store: { ...settings.store, city: e.target.value },
              })
            }
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label>State *</label>
          <input
            type="text"
            value={settings.store.state}
            onChange={(e) =>
              setSettings({
                ...settings,
                store: { ...settings.store, state: e.target.value },
              })
            }
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label>Zip Code *</label>
          <input
            type="text"
            value={settings.store.zip_code}
            onChange={(e) =>
              setSettings({
                ...settings,
                store: { ...settings.store, zip_code: e.target.value },
              })
            }
            className="form-input"
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Country *</label>
          <input
            type="text"
            value={settings.store.country}
            onChange={(e) =>
              setSettings({
                ...settings,
                store: { ...settings.store, country: e.target.value },
              })
            }
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label>Tax Rate (%) *</label>
          <input
            type="number"
            step="0.01"
            value={settings.store.tax_rate}
            onChange={(e) =>
              setSettings({
                ...settings,
                store: { ...settings.store, tax_rate: e.target.value },
              })
            }
            className="form-input"
          />
        </div>

      </div>

      <button onClick={() => handleSave('store')} className="btn-primary">
        Save Store Settings
      </button>
    </div>
  );

  const renderCurrencySettings = () => (
    <div className="settings-section">
      <h2>Currency Settings</h2>
      <p className="settings-description">
        Choose the currency that will be displayed throughout the store.
      </p>

      <div className="form-group">
        <label>Currency Code *</label>
        <select
          value={currencySettings.currency_code}
          onChange={(e) => {
            const code = e.target.value;
            const symbols = {
              'KES': 'KSh',
              'USD': '$',
              'EUR': '€',
              'GBP': '£',
              'TZS': 'TSh',
              'UGX': 'USh'
            };
            setCurrencySettings({
              currency_code: code,
              currency: symbols[code] || code
            });
          }}
          className="form-input"
        >
          <option value="KES">KES - Kenyan Shilling (KSh)</option>
          <option value="USD">USD - US Dollar ($)</option>
          <option value="EUR">EUR - Euro (€)</option>
          <option value="GBP">GBP - British Pound (£)</option>
          <option value="TZS">TZS - Tanzanian Shilling (TSh)</option>
          <option value="UGX">UGX - Ugandan Shilling (USh)</option>
        </select>
      </div>

      <div className="form-group">
        <label>Currency Symbol *</label>
        <input
          type="text"
          value={currencySettings.currency}
          onChange={(e) =>
            setCurrencySettings({
              ...currencySettings,
              currency: e.target.value,
            })
          }
          className="form-input"
          placeholder="e.g., KSh, $, €"
        />
      </div>

      <div className="currency-preview">
        <h3>Preview</h3>
        <p>Price Display: {currencySettings.currency} 1,000.00</p>
      </div>

      <button onClick={handleCurrencyUpdate} className="btn-primary">
        Save Currency Settings
      </button>
    </div>
  );

  const renderBusinessHours = () => {
    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];

    return (
      <div className="settings-section">
        <h2>Business Hours</h2>
        {days.map((day) => (
          <div key={day} className="business-hours-row">
            <div className="day-label">{day.charAt(0).toUpperCase() + day.slice(1)}</div>
            <div className="time-inputs">
              <input
                type="time"
                value={settings.business[`${day}_open`]}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    business: {
                      ...settings.business,
                      [`${day}_open`]: e.target.value,
                    },
                  })
                }
                className="form-input"
              />
              <span>to</span>
              <input
                type="time"
                value={settings.business[`${day}_close`]}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    business: {
                      ...settings.business,
                      [`${day}_close`]: e.target.value,
                    },
                  })
                }
                className="form-input"
              />
              <label className="closed-label">
                <input
                  type="checkbox"
                  checked={!settings.business[`${day}_open`]}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSettings({
                        ...settings,
                        business: {
                          ...settings.business,
                          [`${day}_open`]: '',
                          [`${day}_close`]: '',
                        },
                      });
                    } else {
                      setSettings({
                        ...settings,
                        business: {
                          ...settings.business,
                          [`${day}_open`]: '09:00',
                          [`${day}_close`]: '17:00',
                        },
                      });
                    }
                  }}
                />
                Closed
              </label>
            </div>
          </div>
        ))}

        <button onClick={() => handleSave('business')} className="btn-primary">
          Save Business Hours
        </button>
      </div>
    );
  };

  const renderPaymentSettings = () => (
    <div className="settings-section">
      <h2>Payment Settings</h2>

      <div className="payment-method">
        <h3>Cash Payments</h3>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={settings.payment.cash_enabled}
            onChange={(e) =>
              setSettings({
                ...settings,
                payment: { ...settings.payment, cash_enabled: e.target.checked },
              })
            }
          />
          <span>Enable Cash Payments</span>
        </label>
      </div>

      <div className="payment-method">
        <h3>Stripe</h3>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={settings.payment.stripe_enabled}
            onChange={(e) =>
              setSettings({
                ...settings,
                payment: { ...settings.payment, stripe_enabled: e.target.checked },
              })
            }
          />
          <span>Enable Stripe</span>
        </label>

        {settings.payment.stripe_enabled && (
          <>
            <div className="form-group">
              <label>Publishable Key</label>
              <input
                type="text"
                value={settings.payment.stripe_publishable_key}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    payment: {
                      ...settings.payment,
                      stripe_publishable_key: e.target.value,
                    },
                  })
                }
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label>Secret Key</label>
              <input
                type="password"
                value={settings.payment.stripe_secret_key}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    payment: {
                      ...settings.payment,
                      stripe_secret_key: e.target.value,
                    },
                  })
                }
                className="form-input"
              />
            </div>
          </>
        )}
      </div>

      <div className="payment-method">
        <h3>PayPal</h3>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={settings.payment.paypal_enabled}
            onChange={(e) =>
              setSettings({
                ...settings,
                payment: { ...settings.payment, paypal_enabled: e.target.checked },
              })
            }
          />
          <span>Enable PayPal</span>
        </label>

        {settings.payment.paypal_enabled && (
          <div className="form-group">
            <label>PayPal Client ID</label>
            <input
              type="text"
              value={settings.payment.paypal_client_id}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  payment: {
                    ...settings.payment,
                    paypal_client_id: e.target.value,
                  },
                })
              }
              className="form-input"
            />
          </div>
        )}
      </div>

      <button onClick={() => handleSave('payment')} className="btn-primary">
        Save Payment Settings
      </button>
    </div>
  );

  const renderNotificationSettings = () => (
    <div className="settings-section">
      <h2>Notification Settings</h2>

      <label className="checkbox-label">
        <input
          type="checkbox"
          checked={settings.notification.email_notifications}
          onChange={(e) =>
            setSettings({
              ...settings,
              notification: {
                ...settings.notification,
                email_notifications: e.target.checked,
              },
            })
          }
        />
        <span>Enable Email Notifications</span>
      </label>

      <label className="checkbox-label">
        <input
          type="checkbox"
          checked={settings.notification.low_stock_alert}
          onChange={(e) =>
            setSettings({
              ...settings,
              notification: {
                ...settings.notification,
                low_stock_alert: e.target.checked,
              },
            })
          }
        />
        <span>Low Stock Alerts</span>
      </label>

      <label className="checkbox-label">
        <input
          type="checkbox"
          checked={settings.notification.order_notifications}
          onChange={(e) =>
            setSettings({
              ...settings,
              notification: {
                ...settings.notification,
                order_notifications: e.target.checked,
              },
            })
          }
        />
        <span>Order Notifications</span>
      </label>

      <label className="checkbox-label">
        <input
          type="checkbox"
          checked={settings.notification.customer_notifications}
          onChange={(e) =>
            setSettings({
              ...settings,
              notification: {
                ...settings.notification,
                customer_notifications: e.target.checked,
              },
            })
          }
        />
        <span>Customer Notifications</span>
      </label>

      <button onClick={() => handleSave('notification')} className="btn-primary">
        Save Notification Settings
      </button>
    </div>
  );

  if (loading) {
    return <div className="loading-spinner">Loading settings...</div>;
  }

  return (
    <div className="admin-settings">
      <div className="page-header">
        <h1>Settings</h1>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)} className="close-btn">×</button>
        </div>
      )}

      {success && (
        <div className="success-message">
          {success}
          <button onClick={() => setSuccess(null)} className="close-btn">×</button>
        </div>
      )}

      {/* Tabs */}
      <div className="settings-tabs">
        <button
          className={`tab ${activeTab === 'store' ? 'active' : ''}`}
          onClick={() => setActiveTab('store')}
        >
          Store Info
        </button>
        <button
          className={`tab ${activeTab === 'currency' ? 'active' : ''}`}
          onClick={() => setActiveTab('currency')}
        >
          Currency
        </button>
        <button
          className={`tab ${activeTab === 'business' ? 'active' : ''}`}
          onClick={() => setActiveTab('business')}
        >
          Business Hours
        </button>
        <button
          className={`tab ${activeTab === 'payment' ? 'active' : ''}`}
          onClick={() => setActiveTab('payment')}
        >
          Payment
        </button>
        <button
          className={`tab ${activeTab === 'notification' ? 'active' : ''}`}
          onClick={() => setActiveTab('notification')}
        >
          Notifications
        </button>
      </div>

      {/* Tab Content */}
      <div className="settings-content">
        {activeTab === 'store' && renderStoreSettings()}
        {activeTab === 'currency' && renderCurrencySettings()}
        {activeTab === 'business' && renderBusinessHours()}
        {activeTab === 'payment' && renderPaymentSettings()}
        {activeTab === 'notification' && renderNotificationSettings()}
      </div>
    </div>
  );
};

export default AdminSettings;
