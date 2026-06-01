import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';

export const OAuth2RedirectHandler: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const token = searchParams.get('token');

    if (token) {
      // Validate the token and fetch user details
      api.get('/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(response => {
        login(token, response.data);
        navigate('/dashboard');
      })
      .catch(error => {
        console.error('Failed to validate OAuth token:', error);
        navigate('/login');
      });
    } else {
      navigate('/login');
    }
  }, [location, navigate, login]);

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column' }}>
      <h2>Authenticating...</h2>
      <p>Please wait while we log you in.</p>
    </div>
  );
};
