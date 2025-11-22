import React from 'react';

const Navigation = ({ currentPage, setCurrentPage }) => {
  return (
    <nav className="nav">
      <div className="nav-container">
        <div className="nav-brand">🚌 Bus Booking</div>
        <ul className="nav-links">
          <li>
            <button
              className={`nav-link ${currentPage === 'search' ? 'active' : ''}`}
              onClick={() => setCurrentPage('search')}
            >
              Search Buses
            </button>
          </li>
          <li>
            <button
              className={`nav-link ${currentPage === 'bookings' ? 'active' : ''}`}
              onClick={() => setCurrentPage('bookings')}
            >
              My Bookings
            </button>
          </li>
          <li>
            <button
              className={`nav-link ${currentPage === 'chat' ? 'active' : ''}`}
              onClick={() => setCurrentPage('chat')}
            >
              Provider Info
            </button>
          </li>
        </ul>
      </div>
    </nav>
  );
};

export default Navigation;