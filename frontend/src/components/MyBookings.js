import React, { useState } from 'react';
import { getBookingsByPhone, cancelBooking } from '../services/api';

const MyBookings = () => {
  const [phone, setPhone] = useState('');
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setBookings([]);

    if (!phone || phone.length < 10) {
      setError('Please enter a valid phone number');
      return;
    }

    setLoading(true);

    try {
      const data = await getBookingsByPhone(phone);
      setBookings(data);
      
      if (data.length === 0) {
        setError('No bookings found for this phone number');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch bookings');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (bookingId) => {
    if (!window.confirm('Are you sure you want to cancel this booking?')) {
      return;
    }

    try {
      await cancelBooking(bookingId);
      setSuccess('Booking cancelled successfully');
      
      // Update the booking status locally
      setBookings(bookings.map(booking =>
        booking.id === bookingId
          ? { ...booking, status: 'cancelled' }
          : booking
      ));
      
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to cancel booking');
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="container">
      <div className="card">
        <h2 style={{ marginBottom: '24px', color: '#667eea' }}>My Bookings</h2>

        <form onSubmit={handleSearch}>
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

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Searching...' : 'View Bookings'}
          </button>
        </form>
      </div>

      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}

      {bookings.length > 0 && (
        <div className="card">
          <h3 style={{ marginBottom: '20px', color: '#333' }}>
            Found {bookings.length} booking{bookings.length > 1 ? 's' : ''}
          </h3>

          {bookings.map((booking) => (
            <div key={booking.id} className="booking-card">
              <div className="booking-header">
                <div>
                  <strong style={{ fontSize: '18px', color: '#667eea' }}>
                    {booking.bus_provider}
                  </strong>
                </div>
                <span
                  className={`booking-status ${
                    booking.status === 'active' ? 'status-active' : 'status-cancelled'
                  }`}
                >
                  {booking.status.toUpperCase()}
                </span>
              </div>

              <div style={{ marginBottom: '10px' }}>
                <div className="result-info">
                  <strong>Route:</strong> {booking.from_district} → {booking.to_district}
                </div>
                <div className="result-info">
                  <strong>Passenger:</strong> {booking.user_name}
                </div>
                <div className="result-info">
                  <strong>Phone:</strong> {booking.phone}
                </div>
                <div className="result-info">
                  <strong>Travel Date:</strong> {booking.travel_date}
                </div>
                <div className="result-info">
                  <strong>Booked On:</strong> {formatDate(booking.booking_date)}
                </div>
              </div>

              {booking.status === 'active' && (
                <button
                  className="btn btn-danger"
                  onClick={() => handleCancel(booking.id)}
                  style={{ marginTop: '10px' }}
                >
                  Cancel Booking
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {!loading && bookings.length === 0 && phone && !error && (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <p>No bookings found</p>
        </div>
      )}
    </div>
  );
};

export default MyBookings;