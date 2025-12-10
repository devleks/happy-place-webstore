/**
 * Simple development environment check
 * Alternative to electron-is-dev package
 */

module.exports = process.env.NODE_ENV === 'development' || 
                 process.defaultApp || 
                 /[\\/]electron-prebuilt[\\/]/.test(process.execPath) || 
                 /[\\/]electron[\\/]/.test(process.execPath);
