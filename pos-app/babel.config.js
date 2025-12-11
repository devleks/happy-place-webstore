/**
 * Babel Configuration for Jest
 * Transforms JSX and modern JavaScript for testing
 */

module.exports = {
  presets: [
    // Transform modern JavaScript to Node-compatible code
    ['@babel/preset-env', { 
      targets: { node: 'current' }
    }],
    
    // Transform JSX to JavaScript
    ['@babel/preset-react', { 
      runtime: 'automatic'  // Use new JSX transform
    }]
  ]
};
