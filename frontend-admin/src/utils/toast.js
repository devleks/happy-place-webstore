import { toast } from 'react-toastify';

/**
 * Toast notification utility
 * Provides consistent toast notifications across the app
 */

export const showSuccess = (message) => {
  toast.success(message, {
    position: "top-right",
    autoClose: 3000,
    hideProgressBar: false,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
  });
};

export const showError = (message) => {
  toast.error(message, {
    position: "top-right",
    autoClose: 4000,
    hideProgressBar: false,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
  });
};

export const showInfo = (message) => {
  toast.info(message, {
    position: "top-right",
    autoClose: 3000,
    hideProgressBar: false,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
  });
};

export const showWarning = (message) => {
  toast.warning(message, {
    position: "top-right",
    autoClose: 3500,
    hideProgressBar: false,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
  });
};

export const showPromise = (promise, messages) => {
  /**
   * Show toast for promise-based operations
   * @param {Promise} promise - The promise to track
   * @param {Object} messages - Messages for pending, success, error states
   * @param {string} messages.pending - Message to show while pending
   * @param {string} messages.success - Message to show on success
   * @param {string} messages.error - Message to show on error
   */
  return toast.promise(
    promise,
    {
      pending: messages.pending || 'Loading...',
      success: messages.success || 'Success!',
      error: messages.error || 'An error occurred',
    },
    {
      position: "top-right",
      autoClose: 3000,
    }
  );
};

// Export default object with all methods
export default {
  success: showSuccess,
  error: showError,
  info: showInfo,
  warning: showWarning,
  promise: showPromise,
};
