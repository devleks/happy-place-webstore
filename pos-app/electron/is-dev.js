/**
 * Simple development environment check
 * Alternative to electron-is-dev package
 */

// Temporarily force production mode for testing
module.exports = false;

// Original check (commented out for testing):
// module.exports = process.env.NODE_ENV === 'development' || 
//                  process.defaultApp || 
//                  /[\\/]electron-prebuilt[\\/]/.test(process.execPath) || 
//                  /[\\/]electron[\\/]/.test(process.execPath);
