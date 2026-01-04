/**
 * React Entry Point
 * PWA with IndexedDB
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { initializeDatabase } from './db';
import * as serviceWorkerRegistration from './serviceWorkerRegistration';

// Initialize IndexedDB and render app after it's ready
const root = ReactDOM.createRoot(document.getElementById('root'));

initializeDatabase()
  .then(() => {
    console.log('✅ Database initialized and seeded');
    // Render app after database is ready
    root.render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    );
  })
  .catch((error) => {
    console.error('❌ Database initialization failed:', error);
    // Still render app but show error
    root.render(
      <React.StrictMode>
        <div style={{padding: '20px', textAlign: 'center'}}>
          <h2>Database Initialization Failed</h2>
          <p>{error.message}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      </React.StrictMode>
    );
  });

// Register service worker for PWA functionality
serviceWorkerRegistration.register({
  onSuccess: (registration) => {
    console.log('✅ PWA: Service worker registered successfully');
  },
  onUpdate: (registration) => {
    console.log('📦 PWA: New version available. Please refresh.');
    // Optionally show update notification to user
  }
});
