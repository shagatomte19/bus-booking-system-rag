import React, { useState } from 'react';
import { createBooking } from '../services/api';

const BookingForm = ({ bus, onSuccess, onCancel }) => {
  const [userName, setUserName] = useState('');
  const [phone, setPhone] = useState('');
  const [travelDate, setTravelDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // Get today's date in YYYY-MM-DD format for min attribute
  const today = new Date().toISOString().split('T')[0];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);

    if (!userName || !phone || !travelDate) {
      setError('Please fill in all fields');
      return;
    }

    if (phone.length < 10) {
      setError('Please enter a valid phone number');
      return;
    }

    setLoading(true);

    try {
      await createBooking({
        userName,
        phone,
        fromDistrict: bus.from_district,
        toDistrict: bus.to_district,
        busProvider: bus.provider_name,
        travelDate,
      });

      setSuccess(true);
      setTimeout(() => {
        onSuccess();
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create booking');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="card">
        <h2 style={{ marginBottom: '24px', color: '#667eea' }}>Book Your Ticket</h2>

        <div className="result-card" style={{ marginBottom: '30px' }}>
          <div className="result-title">{bus.provider_name}</div>
          <div className="result-info">
            <strong>Route:</strong> {bus.from_district} → {bus.to_district}
          </div>
          <div className="result-info">
            <strong>Drop Point:</strong> {bus.drop_point}
          </div>
          <div className="result-info">
            <strong>Price:</strong> ৳{bus.price}
          </div>
        </div>

        {error && <div className="error">{error}</div>}
        {success && (
          <div className="success">
            ✓ Booking created successfully! Redirecting...
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <input
              type="text"
              className="form-input"
              placeholder="Enter your full name"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              required
              minLength="2"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Phone Number</label>
            <input
              type="tel"
              className="form-input"
              placeholder="Enter your phone number"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
              pattern="[0-9+]{10,15}"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Travel Date</label>
            <input
              type="date"
              className="form-input"
              value={travelDate}
              onChange={(e) => setTravelDate(e.target.value)}
              required
              min={today}
            />
          </div>

          <div style={{ display: 'flex', gap: '15px', marginTop: '30px' }}>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || success}
              style={{ flex: 1 }}
            >
              {loading ? 'Booking...' : 'Confirm Booking'}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onCancel}
              disabled={loading || success}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BookingForm;