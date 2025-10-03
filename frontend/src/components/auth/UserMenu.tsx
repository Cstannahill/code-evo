import React, { useState, useEffect } from 'react';
import { APIKeyManager } from './APIKeyManager';
import { getApiBaseUrl } from '../../config/environment';

interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_guest: boolean;
  created_at: string;
  last_login?: string;
}

export const UserMenu: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showAPIKeys, setShowAPIKeys] = useState(false);

  useEffect(() => {
    loadUserInfo();
  }, []);

  const loadUserInfo = async () => {
    const token = localStorage.getItem('auth_token');
    if (!token) return;

    try {
      const apiBaseUrl = getApiBaseUrl();

      const response = await fetch(`${apiBaseUrl}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      }
    } catch (error: unknown) {
      if (error instanceof Error) {
        console.error('Failed to load user info:', error);
      } else {
        console.error('Failed to load user info due to unknown error');
      }
    }
  };

  if (!user) return null;

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    window.location.reload();
    setShowDropdown(false);
  };

  return (
    <>
      <div className="relative">
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="flex items-center space-x-2 text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md"
        >
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm ${user.is_guest ? 'bg-gray-500' : 'bg-blue-500'
            }`}>
            {user.is_guest ? 'G' : user.username.charAt(0).toUpperCase()}
          </div>
          <span className="text-sm">
            {user.is_guest ? 'Guest User' : user.username}
          </span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {showDropdown && (
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
            <div className="px-4 py-2 text-sm text-gray-900 border-b">
              <div className="font-medium">{user.username}</div>
              <div className="text-gray-500">{user.email}</div>
              {user.is_guest && (
                <div className="text-xs text-orange-500 mt-1">Guest Session</div>
              )}
            </div>

            <button
              onClick={() => {
                setShowAPIKeys(true);
                setShowDropdown(false);
              }}
              className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
            >
              {user.is_guest ? 'Set API Keys' : 'Manage API Keys'}
            </button>

            {!user.is_guest && (
              <>
                <a
                  href="/repositories/user/my-repositories"
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  onClick={() => setShowDropdown(false)}
                >
                  My Repositories
                </a>

                <a
                  href="/repositories/global"
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  onClick={() => setShowDropdown(false)}
                >
                  Browse Global Repositories
                </a>
              </>
            )}

            <button
              onClick={handleLogout}
              className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
            >
              Logout
            </button>
          </div>
        )}
      </div>

      {showAPIKeys && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex min-h-screen">
          <div className="bg-white rounded-lg max-w-6xl w-full max-h-[85vh] overflow-y-auto relative shadow-xl m-auto">
            <button
              onClick={() => setShowAPIKeys(false)}
              className="absolute top-6 right-6 text-gray-500 hover:text-gray-700 z-20 bg-white rounded-full p-2 shadow-lg border hover:bg-gray-50"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <div className="p-8">
              <APIKeyManager />
            </div>
          </div>
        </div>
      )}
    </>
  );
};