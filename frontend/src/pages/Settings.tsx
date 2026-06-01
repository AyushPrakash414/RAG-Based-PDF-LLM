import React, { useState, useRef } from 'react';
import { User, LogOut, Trash2, Upload } from 'lucide-react';
import { NeoCard } from '../components/shared/NeoCard';
import { NeoButton } from '../components/shared/NeoButton';
import { NeoThemeToggle } from '../components/shared/NeoThemeToggle';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';
import styles from './Settings.module.css';

export const Settings: React.FC = () => {
  const { user, logout, login } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('File is too large. Maximum size is 5MB.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    setError('');
    setSuccess('');

    try {
      const { data } = await api.post('/users/avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      
      // Update local user context with new avatar ID
      const token = localStorage.getItem('accessToken');
      if (token && user) {
        login(token, { ...user, avatarId: data.avatarId });
      }
      setSuccess('Profile picture updated successfully!');
    } catch (err: any) {
      setError(err.response?.data || 'Failed to upload image.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className={styles.settingsContainer}>
      <header className={styles.header}>
        <h1>Settings</h1>
        <p>Manage your account preferences</p>
      </header>

      <div className={styles.sections}>
        
        {/* Profile Section */}
        <section>
          <h2>Profile</h2>
          <NeoCard className={styles.settingsCard}>
            <div className={styles.profileRow}>
              <div className={styles.avatarSection}>
                <div className={styles.avatarLarge}>
                  {user?.avatarId ? (
                    <img src={`${import.meta.env.VITE_API_URL || 'http://localhost:8080'}/users/avatar/${user.avatarId}`} alt="Avatar" />
                  ) : user?.profilePicture ? (
                    <img src={user.profilePicture} alt="Avatar" />
                  ) : (
                    <User size={48} />
                  )}
                </div>
                
                <div className={styles.avatarUpload}>
                  <h4>Profile Picture</h4>
                  <p>JPG, PNG, or WEBP. Max 5MB.</p>
                  
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    style={{ display: 'none' }} 
                    accept="image/jpeg, image/png, image/webp"
                    onChange={handleAvatarUpload}
                  />
                  
                  <NeoButton 
                    variant="secondary" 
                    icon={<Upload size={16} />}
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                  >
                    {uploading ? 'Uploading...' : 'Upload Custom Avatar'}
                  </NeoButton>

                  {error && <p className={styles.errorText}>{error}</p>}
                  {success && <p className={styles.successText}>{success}</p>}
                </div>
              </div>

              <div className={styles.profileInfo}>
                <div className={styles.infoGroup}>
                  <label>Name</label>
                  <p>{user?.name}</p>
                </div>
                <div className={styles.infoGroup}>
                  <label>Email</label>
                  <p>{user?.email}</p>
                </div>
              </div>
            </div>
          </NeoCard>
        </section>

        {/* Theme Section */}
        <section>
          <h2>Preferences</h2>
          <NeoCard className={styles.settingsCard}>
            <div className={styles.preferenceRow}>
              <div>
                <h4>App Theme</h4>
                <p>Switch between light and dark mode.</p>
              </div>
              <NeoThemeToggle />
            </div>
          </NeoCard>
        </section>

        {/* Security Section */}
        <section>
          <h2>Security & Account</h2>
          <NeoCard className={styles.settingsCard}>
            <div className={styles.dangerZone}>
              <div className={styles.dangerItem}>
                <div>
                  <h4>Sign Out</h4>
                  <p>Log out of your current session.</p>
                </div>
                <NeoButton variant="secondary" icon={<LogOut size={16} />} onClick={logout}>
                  Log Out
                </NeoButton>
              </div>

              <div className={styles.dangerDivider}></div>

              <div className={styles.dangerItem}>
                <div>
                  <h4>Delete Account</h4>
                  <p>Permanently remove your data from our servers.</p>
                </div>
                <NeoButton variant="danger" icon={<Trash2 size={16} />}>
                  Delete Account
                </NeoButton>
              </div>
            </div>
          </NeoCard>
        </section>

      </div>
    </div>
  );
};
