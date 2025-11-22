import React, { useState } from 'react';
import { searchBuses } from '../services/api';
import BookingForm from './BookingForm';

const SearchBuses = () => {
  const [fromDistrict, setFromDistrict] = useState('');
  const [toDistrict, setToDistrict] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedBus, setSelectedBus] = useState(null);

  const districts = [
    'Dhaka', 'Chattogram', 'Khulna', 'Rajshahi', 'Sylhet',
    'Barishal', 'Rangpur', 'Mymensingh', 'Comilla', 'Bogra'
  ];

  const handleSearch = async (e) => {
    e.preventDefault();
    setError('');
    setResults([]);
    setSelectedBus(null);

    if (!fromDistrict || !toDistrict) {
      setError('Please select both origin and destination districts');
      return;
    }

    if (fromDistrict === toDistrict) {
      setError('Origin and destination must be different');
      return;
    }

    setLoading(true);

    try {
      const data = await searchBuses(
        fromDistrict,
        toDistrict,
        maxPrice ? parseInt(maxPrice) : null
      );
      setResults(data);
      
      if (data.length === 0) {
        setError('No buses found for this route');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to search buses');
    } finally {
      setLoading(false);
    }
  };

  const handleBookClick = (bus) => {
    setSelectedBus(bus);
  };

  const handleBookingSuccess = () => {
    setSelectedBus(null);
    setResults([]);
    setFromDistrict('');
    setToDistrict('');
    setMaxPrice('');
  };

  if (selectedBus) {
    return (
      <BookingForm
        bus={selectedBus}
        onSuccess={handleBookingSuccess}
        onCancel={() => setSelectedBus(null)}
      />
    );
  }

  return (
    <div className="container">
      <div className="card">
        <h2 style={{ marginBottom: '24px', color: '#667eea' }}>Search Buses</h2>

        <form onSubmit={handleSearch}>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">From District</label>
              <select
                className="form-select"
                value={fromDistrict}
                onChange={(e) => setFromDistrict(e.target.value)}
              >
                <option value="">Select origin</option>
                {districts.map((district) => (
                  <option key={district} value={district}>
                    {district}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">To District</label>
              <select
                className="form-select"
                value={toDistrict}
                onChange={(e) => setToDistrict(e.target.value)}
              >
                <option value="">Select destination</option>
                {districts.map((district) => (
                  <option key={district} value={district}>
                    {district}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Max Price (Optional)</label>
            <input
              type="number"
              className="form-input"
              placeholder="Enter maximum price"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
              min="0"
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Searching...' : 'Search Buses'}
          </button>
        </form>
      </div>

      {error && <div className="error">{error}</div>}

      {results.length > 0 && (
        <div className="card">
          <h3 style={{ marginBottom: '20px', color: '#333' }}>
            Found {results.length} bus{results.length > 1 ? 'es' : ''}
          </h3>
          <div className="result-grid">
            {results.map((bus, index) => (
              <div key={index} className="result-card">
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
                <button
                  className="btn btn-primary"
                  style={{ marginTop: '15px', width: '100%' }}
                  onClick={() => handleBookClick(bus)}
                >
                  Book Now
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchBuses;