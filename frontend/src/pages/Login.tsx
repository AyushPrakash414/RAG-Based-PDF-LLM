import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, Globe } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { NeoCard } from '../components/shared/NeoCard';
import { NeoButton } from '../components/shared/NeoButton';
import { NeoInput } from '../components/shared/NeoInput';
import api from '../api/axios';
import styles from './Auth.module.css';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const { data } = await api.post('/auth/login', { email, password });
      login(data.accessToken, data.user);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data || 'Failed to login');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8080';
    window.location.href = `${baseURL}/oauth2/authorization/google`;
  };

  return (
    <div className={styles.authContainer}>
      <NeoCard className={styles.authCard}>
        <div className={styles.header}>
          <h2>Welcome Back</h2>
          <p>Login to chat with your documents</p>
        </div>

        {error && <div className={styles.errorAlert}>{error}</div>}

        <form onSubmit={handleLogin} className={styles.form}>
          <NeoInput
            label="Email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            icon={<Mail size={18} />}
            required
          />
          <NeoInput
            label="Password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            icon={<Lock size={18} />}
            required
          />

          <div className={styles.links}>
            <Link to="/forgot-password" className={styles.link}>Forgot Password?</Link>
          </div>

          <NeoButton fullWidth type="submit" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </NeoButton>
        </form>

        <div className={styles.divider}>
          <span>OR</span>
        </div>

        <NeoButton 
          fullWidth 
          variant="secondary" 
          onClick={handleGoogleLogin}
          icon={<Globe size={18} />}
        >
          Continue With Google
        </NeoButton>

        <div className={styles.footer}>
          <p>Don't have an account? <Link to="/register" className={styles.link}>Create Account</Link></p>
        </div>
      </NeoCard>
    </div>
  );
};
