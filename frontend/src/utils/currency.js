/**
 * Currency Utility Functions
 * Handles currency formatting and display throughout the application
 */

// Default currency settings
const DEFAULT_CURRENCY = {
  symbol: 'KSh',
  code: 'KES',
};

// Currency settings cache
let currencySettings = { ...DEFAULT_CURRENCY };

/**
 * Initialize currency settings from API or localStorage
 */
export const initializeCurrency = async () => {
  try {
    // Try to get from localStorage first
    const cached = localStorage.getItem('currency_settings');
    if (cached) {
      currencySettings = JSON.parse(cached);
    }

    // Fetch from API (public endpoint, no auth needed)
    const response = await fetch(
      `${process.env.REACT_APP_API_URL || 'http://localhost:5001/api'}/settings/public`
    );

    if (response.ok) {
      const data = await response.json();
      if (data.success && data.settings) {
        const newSettings = {
          symbol: data.settings.currency || DEFAULT_CURRENCY.symbol,
          code: data.settings.currency_code || DEFAULT_CURRENCY.code,
        };

        currencySettings = newSettings;
        localStorage.setItem('currency_settings', JSON.stringify(newSettings));
      }
    }
  } catch (error) {
    console.error('Failed to fetch currency settings:', error);
    // Use default or cached settings
  }

  return currencySettings;
};

/**
 * Get current currency settings
 */
export const getCurrencySettings = () => {
  return currencySettings;
};

/**
 * Format a number as currency
 * @param {number} amount - The amount to format
 * @param {boolean} showSymbol - Whether to show the currency symbol
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (amount, showSymbol = true) => {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return showSymbol ? `${currencySettings.symbol} 0.00` : '0.00';
  }

  const formatted = Number(amount).toLocaleString('en-KE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  return showSymbol ? `${currencySettings.symbol} ${formatted}` : formatted;
};

/**
 * Update currency settings
 * @param {Object} newSettings - New currency settings {symbol, code}
 */
export const updateCurrencySettings = (newSettings) => {
  currencySettings = { ...currencySettings, ...newSettings };
  localStorage.setItem('currency_settings', JSON.stringify(currencySettings));
};

/**
 * Get currency symbol only
 * @returns {string} Currency symbol
 */
export const getCurrencySymbol = () => {
  return currencySettings.symbol;
};

/**
 * Get currency code only
 * @returns {string} Currency code
 */
export const getCurrencyCode = () => {
  return currencySettings.code;
};
