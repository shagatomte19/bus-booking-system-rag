import React, { useState } from 'react';
import Navigation from './components/Navigation';
import SearchBuses from './components/SearchBuses';
import MyBookings from './components/MyBookings';
import ProviderChat from './components/ProviderChat';

function App() {
  const [currentPage, setCurrentPage] = useState('search');

  const renderPage = () => {
    switch (currentPage) {
      case 'search':
        return <SearchBuses />;
      case 'bookings':
        return <MyBookings />;
      case 'chat':
        return <ProviderChat />;
      default:
        return <SearchBuses />;
    }
  };

  return (
    <div className="app">
      <Navigation currentPage={currentPage} setCurrentPage={setCurrentPage} />
      {renderPage()}
    </div>
  );
}

export default App;