import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, User, Globe } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { NeoCard } from '../components/shared/NeoCard';
import { NeoButton } from '../components/shared/NeoButton';
import { NeoInput } from '../components/shared/NeoInput';
import api from '../api/axios';
import styles from './Auth.module.css';

export const Register: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const { data } = await api.post('/auth/register', { name, email, password });
      login(data.accessToken, data.user);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data || 'Failed to register');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    window.location.href = 'https://rag-based-pdf-llm-1.onrender.com/oauth2/authorization/google';
  };

  return (
    <div className={styles.authContainer}>
      <NeoCard className={styles.authCard}>
        <div className={styles.header}>
          <h2>Create Account</h2>
          <p>Join the Self-Healing RAG Platform</p>
        </div>

        {error && <div className={styles.errorAlert}>{error}</div>}

        <form onSubmit={handleRegister} className={styles.form}>
          <NeoInput
            label="Name"
            type="text"
            placeholder="John Doe"
            value={name}
            onChange={(e) => setName(e.target.value)}
            icon={<User size={18} />}
            required
          />
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
          <NeoInput
            label="Confirm Password"
            type="password"
            placeholder="••••••••"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            icon={<Lock size={18} />}
            required
          />

          <NeoButton fullWidth type="submit" disabled={loading}>
            {loading ? 'Creating Account...' : 'Sign Up'}
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
          <p>Already have an account? <Link to="/login" className={styles.link}>Login</Link></p>
        </div>
      </NeoCard>
    </div>
  );
};
