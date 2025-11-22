import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const searchBuses = async (fromDistrict, toDistrict, maxPrice) => {
  const response = await api.post('/api/buses/search', {
    from_district: fromDistrict,
    to_district: toDistrict,
    max_price: maxPrice || null,
  });
  return response.data;
};

export const getAllProviders = async () => {
  const response = await api.get('/api/buses/providers');
  return response.data;
};

export const createBooking = async (bookingData) => {
  const response = await api.post('/api/bookings', {
    user_name: bookingData.userName,
    phone: bookingData.phone,
    from_district: bookingData.fromDistrict,
    to_district: bookingData.toDistrict,
    bus_provider: bookingData.busProvider,
    travel_date: bookingData.travelDate,
  });
  return response.data;
};

export const getBookingsByPhone = async (phone) => {
  const response = await api.get(`/api/bookings/${phone}`);
  return response.data;
};

export const cancelBooking = async (bookingId) => {
  const response = await api.delete(`/api/bookings/${bookingId}`);
  return response.data;
};

export const askProviderQuestion = async (question) => {
  const response = await api.post('/api/providers/ask', {
    question: question,
  });
  return response.data;
};

export default api;