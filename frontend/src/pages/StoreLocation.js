import React, { useState, useEffect } from 'react';
import { storeLocationAPI } from '../services/api';
import '../styles/StoreLocation.css';

const StoreLocation = () => {
  const [location, setLocation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStoreLocation();
  }, []);

  const fetchStoreLocation = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await storeLocationAPI.getAll();
      if (response.data.length > 0) {
        setLocation(response.data[0]);
      }
    } catch (err) {
      setError('Failed to load store location. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading store location...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!location) return <div className="error">Store location not found</div>;

  const hours = location.hours_of_operation ? JSON.parse(location.hours_of_operation) : {};

  return (
    <div className="store-location-page">
      <div className="store-header">
        <h1>Visit Our Store</h1>
        <p className="store-subtitle">We'd love to see you in person!</p>
      </div>

      <div className="store-content">
        <div className="store-info-section">
          <div className="info-card">
            <h2>{location.name}</h2>

            <div className="info-group">
              <h3>Address</h3>
              <p>{location.address}</p>
              <p>
                {location.city}, {location.state} {location.zip_code}
              </p>
            </div>

            <div className="info-group">
              <h3>Contact</h3>
              {location.phone && (
                <p>
                  <strong>Phone:</strong> <a href={`tel:${location.phone}`}>{location.phone}</a>
                </p>
              )}
              {location.email && (
                <p>
                  <strong>Email:</strong> <a href={`mailto:${location.email}`}>{location.email}</a>
                </p>
              )}
            </div>

            <div className="info-group">
              <h3>Hours of Operation</h3>
              <div className="hours-list">
                {Object.entries(hours).map(([day, hours]) => (
                  <div key={day} className="hours-item">
                    <span className="day">{day}:</span>
                    <span className="time">{hours}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="info-group">
              <a
                href={`https://www.google.com/maps/search/?api=1&query=${location.latitude},${location.longitude}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary"
              >
                Get Directions
              </a>
            </div>
          </div>
        </div>

        <div className="map-section">
          <div className="map-placeholder">
            <p>Map View</p>
            <p className="map-coordinates">
              Lat: {location.latitude}, Long: {location.longitude}
            </p>
            <p className="map-note">
              To display an actual map, integrate with Google Maps API or similar service
            </p>
            <a
              href={`https://www.google.com/maps/search/?api=1&query=${location.latitude},${location.longitude}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary"
            >
              View on Google Maps
            </a>
          </div>
        </div>
      </div>

      <div className="visit-info">
        <h2>What to Expect</h2>
        <div className="visit-features">
          <div className="feature">
            <h3>Personal Styling</h3>
            <p>Our friendly staff can help you find the perfect outfit for any occasion</p>
          </div>
          <div className="feature">
            <h3>Try Before You Buy</h3>
            <p>See and feel the quality of our clothing in person</p>
          </div>
          <div className="feature">
            <h3>In-Stock Items</h3>
            <p>Check online inventory and we'll have it ready for you to try on</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StoreLocation;
