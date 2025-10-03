import React, { useState } from 'react';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';
import { getApiBaseUrl } from '../../config/environment';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type AuthMode = 'login' | 'register';

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const [mode, setMode] = useState<AuthMode>('login');

  const handleGuestLogin = async () => {
    try {
      const apiBaseUrl = getApiBaseUrl();

      const response = await fetch(`${apiBaseUrl}/api/auth/guest`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('Guest login failed');
      }

      const tokenData = await response.json();
      localStorage.setItem('auth_token', tokenData.access_token);
      window.location.reload();
      onClose();
    } catch (error: unknown) {
      if (error instanceof Error) {
        console.error('Guest login failed:', error);
      } else {
        console.error('Guest login failed with unknown error');
      }
      alert('Guest login failed. Please try again.');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex min-h-screen">
      <div className="bg-white rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto relative shadow-xl m-auto">
        <button
          onClick={onClose}
          className="absolute top-6 right-6 text-gray-500 hover:text-gray-700 z-20 bg-white rounded-full p-2 shadow-lg border hover:bg-gray-50"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="p-6">
          {mode === 'login' ? (
            <LoginForm
              onSwitchToRegister={() => setMode('register')}
              onGuestLogin={handleGuestLogin}
            />
          ) : (
            <RegisterForm
              onSwitchToLogin={() => setMode('login')}
            />
          )}
        </div>
      </div>
    </div>
  );
};