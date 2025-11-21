import React, { useState, useEffect } from 'react';
import { storeLocationAPI } from '../services/api';
import '../styles/StoreLocation.css';

const StoreLocation = () => {
  const [location, setLocation] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fallback store data if backend doesn't have it yet
  const fallbackLocation = {
    name: 'Happy Place Boutique',
    address: 'Store No. 22, 1st Floor, Bethel Business Centre, Opp. Uhuru Gardens, Langata Rd.',
    city: 'Nairobi',
    state: 'Kenya',
    zip_code: '',
    phone: '(555) 123-4567',
    email: 'info@happyplaceboutique.com',
    hours_of_operation: JSON.stringify({
      'Monday - Friday': '10:00 AM - 7:00 PM',
      'Saturday': '10:00 AM - 6:00 PM',
      'Sunday': '12:00 PM - 5:00 PM'
    })
  };

  useEffect(() => {
    fetchStoreLocation();
  }, []);

  const fetchStoreLocation = async () => {
    setLoading(true);

    try {
      const response = await storeLocationAPI.getAll();
      if (response.data.length > 0) {
        setLocation(response.data[0]);
      } else {
        // Use fallback data if no store location in database
        setLocation(fallbackLocation);
      }
    } catch (err) {
      // Use fallback data if API call fails
      console.log('Using fallback store location data');
      setLocation(fallbackLocation);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading store location...</div>;

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
                href="https://maps.app.goo.gl/bxYZSxqY3RiBhE6a8"
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
          <div className="map-container">
            <iframe
              src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3988.7549935192574!2d36.79894054026614!3d-1.322830198670181!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x182f106a25f9e90b%3A0x1b9de7f24625c365!2sBethel%20Business%20Centre!5e0!3m2!1sen!2sus!4v1763751744617!5m2!1sen!2sus"
              width="100%"
              height="450"
              style={{ border: 0 }}
              allowFullScreen=""
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
              title="Happy Place Boutique Location Map"
            ></iframe>
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
