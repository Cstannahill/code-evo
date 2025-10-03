import React, { useState, useEffect, useCallback } from 'react';
import { getApiBaseUrl } from '../../config/environment';

interface APIKey {
  id: string;
  provider: string;
  key_name: string;
  created_at: string;
  last_used?: string;
  is_active: boolean;
  usage_count: number;
}

interface User {
  id: string;
  username: string;
  email: string;
  is_guest: boolean;
}

type ApiProvider = 'openai' | 'anthropic' | 'gemini';

interface NewApiKeyPayload {
  provider: ApiProvider;
  key_name: string;
  api_key: string;
}

interface GuestKeysPayload {
  openai_key: string;
  anthropic_key: string;
  gemini_key: string;
}

interface ApiErrorResponse {
  detail?: string;
  message?: string;
  error?: string;
}

const buildApiUrl = (path: string): string => {
  const baseUrl = getApiBaseUrl();
  return `${baseUrl}${path}`;
};

const parseApiError = async (response: Response, fallback: string): Promise<string> => {
  try {
    const data = (await response.json()) as ApiErrorResponse;
    return data.detail ?? data.message ?? data.error ?? fallback;
  } catch {
    return fallback;
  }
};

export const APIKeyManager: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newKey, setNewKey] = useState<NewApiKeyPayload>({
    provider: 'openai',
    key_name: '',
    api_key: ''
  });

  const [guestKeys, setGuestKeys] = useState<GuestKeysPayload>({
    openai_key: '',
    anthropic_key: '',
    gemini_key: ''
  });

  const loadApiKeys = useCallback(async () => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      console.warn('Cannot load API keys without auth token');
      return;
    }

    try {
      const response = await fetch(buildApiUrl('/api/auth/api-keys'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const keys = (await response.json()) as APIKey[];
        setApiKeys(keys);
        return;
      }

      const message = await parseApiError(response, 'Failed to load API keys');
      console.error(message);
    } catch (error) {
      console.error('Failed to load API keys:', error);
    }
  }, []);

  const loadUserInfo = useCallback(async () => {
    const token = localStorage.getItem('auth_token');
    if (!token) return;

    try {
      const response = await fetch(buildApiUrl('/api/auth/me'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.status === 401) {
        localStorage.removeItem('auth_token');
        setUser(null);
        return;
      }

      if (response.ok) {
        const userData = (await response.json()) as User;
        setUser(userData);

        if (!userData.is_guest) {
          await loadApiKeys();
        }
        return;
      }

      const message = await parseApiError(response, 'Failed to load user info');
      console.error(message);
    } catch (error) {
      console.error('Failed to load user info:', error);
    }
  }, [loadApiKeys]);

  useEffect(() => {
    void loadUserInfo();
  }, [loadUserInfo]);

  const handleAddApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Authentication token is missing. Please sign in again.');
      }

      const response = await fetch(buildApiUrl('/api/auth/api-keys'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newKey)
      });

      if (response.ok) {
        setNewKey({ provider: 'openai', key_name: '', api_key: '' });
        setShowAddForm(false);
        await loadApiKeys();
      } else {
        const message = await parseApiError(response, 'Failed to add API key');
        throw new Error(message);
      }
    } catch (error) {
      console.error('Error adding API key:', error);
      if (error instanceof Error) {
        alert(error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSetGuestKeys = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Authentication token is missing. Please sign in again.');
      }

      const response = await fetch(buildApiUrl('/api/auth/guest/api-keys'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(guestKeys)
      });

      if (response.ok) {
        const result = await response.json();
        alert(`API keys set for guest session: ${result.providers_set.join(', ')}`);
        setGuestKeys({ openai_key: '', anthropic_key: '', gemini_key: '' });
      } else {
        const message = await parseApiError(response, 'Failed to set guest API keys');
        throw new Error(message);
      }
    } catch (error) {
      console.error('Error setting guest API keys:', error);
      alert('Failed to set guest API keys');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteApiKey = async (keyId: string) => {
    if (!confirm('Are you sure you want to delete this API key?')) return;

    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Authentication token is missing. Please sign in again.');
      }

      const response = await fetch(buildApiUrl(`/api/auth/api-keys/${keyId}`), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        await loadApiKeys();
      } else {
        const message = await parseApiError(response, 'Failed to delete API key');
        throw new Error(message);
      }
    } catch (error) {
      console.error('Error deleting API key:', error);
      if (error instanceof Error) {
        alert(error.message);
      }
    }
  };

  if (!user) {
    return <div>Loading...</div>;
  }

  if (user.is_guest) {
    return (
      <div className="max-w-2xl mx-auto bg-white p-6 rounded-lg shadow-md">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold mb-2">Guest Session API Keys</h3>
          <p className="text-gray-600 mb-6">
            As a guest user, you can provide API keys for one-time use. These keys are temporarily stored and will expire in 24 hours.
          </p>
        </div>

        <form onSubmit={handleSetGuestKeys}>
          <div className="space-y-4">
            <div>
              <label htmlFor="openai_key" className="block text-sm font-medium text-gray-700 mb-2">
                OpenAI API Key (optional)
              </label>
              <input
                type="password"
                id="openai_key"
                value={guestKeys.openai_key}
                onChange={(e) => setGuestKeys(prev => ({ ...prev, openai_key: e.target.value }))}
                placeholder="sk-..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label htmlFor="anthropic_key" className="block text-sm font-medium text-gray-700 mb-2">
                Anthropic API Key (optional)
              </label>
              <input
                type="password"
                id="anthropic_key"
                value={guestKeys.anthropic_key}
                onChange={(e) => setGuestKeys(prev => ({ ...prev, anthropic_key: e.target.value }))}
                placeholder="sk-ant-..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label htmlFor="gemini_key" className="block text-sm font-medium text-gray-700 mb-2">
                Google Gemini API Key (optional)
              </label>
              <input
                type="password"
                id="gemini_key"
                value={guestKeys.gemini_key}
                onChange={(e) => setGuestKeys(prev => ({ ...prev, gemini_key: e.target.value }))}
                placeholder="AI..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-6 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Setting Keys...' : 'Set API Keys for Session'}
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-md">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-xl font-semibold">API Key Management</h3>
          <p className="text-sm text-gray-600 mt-1">Securely store your AI provider API keys</p>
        </div>
        <button
          onClick={() => {
            console.log('Header Add API Key button clicked, current showAddForm:', showAddForm);
            setShowAddForm(!showAddForm);
          }}
          className="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 font-medium flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          {showAddForm ? 'Cancel' : 'Add API Key'}
        </button>
      </div>

      {showAddForm && (
        <div className="mb-6 p-4 border rounded-lg bg-gray-50">
          <h4 className="text-lg font-medium mb-4">Add New API Key</h4>
          <p className="text-sm text-green-600 mb-4">✓ Form is rendering - showAddForm is true</p>
          <form onSubmit={handleAddApiKey}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label htmlFor="provider" className="block text-sm font-medium text-gray-700 mb-2">
                  Provider
                </label>
                <select
                  id="provider"
                  value={newKey.provider}
                  onChange={(e) => {
                    const provider = e.target.value as ApiProvider;
                    setNewKey(prev => ({ ...prev, provider }));
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="gemini">Google Gemini</option>
                </select>
              </div>

              <div>
                <label htmlFor="key_name" className="block text-sm font-medium text-gray-700 mb-2">
                  Key Name (optional)
                </label>
                <input
                  type="text"
                  id="key_name"
                  value={newKey.key_name}
                  onChange={(e) => setNewKey(prev => ({ ...prev, key_name: e.target.value }))}
                  placeholder="My API Key"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label htmlFor="api_key" className="block text-sm font-medium text-gray-700 mb-2">
                  API Key
                </label>
                <input
                  type="password"
                  id="api_key"
                  value={newKey.api_key}
                  onChange={(e) => setNewKey(prev => ({ ...prev, api_key: e.target.value }))}
                  placeholder="sk-..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="mt-4 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Adding...' : 'Add API Key'}
            </button>
          </form>
        </div>
      )}

      <div className="space-y-4">
        {apiKeys.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
            <div className="max-w-md mx-auto">
              <div className="mb-4">
                <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.029 5.924c-.138-.017-.275-.037-.413-.059m0 0a6 6 0 01-3.118-1.343M12 21c-2.67 0-4.67-2.67-4.67-4.67C4.67 13.67 7.33 12 12 12s4.67 1.67 4.67 4.67C16.67 18.33 14.33 21 12 21z" />
                </svg>
                <h4 className="text-lg font-medium text-gray-900 mb-2">No API keys configured</h4>
                <p className="text-gray-600 mb-6">
                  Add API keys for OpenAI, Anthropic, or Google Gemini to enable AI-powered repository analysis.
                </p>
              </div>
              <button
                onClick={() => {
                  console.log('Add API Key button clicked');
                  setShowAddForm(true);
                }}
                className="bg-blue-600 text-white py-3 px-6 rounded-md hover:bg-blue-700 font-medium transition-colors"
              >
                Add Your First API Key
              </button>
            </div>
          </div>
        ) : (
          apiKeys.map((key) => (
            <div key={key.id} className="border rounded-lg p-4 flex justify-between items-center">
              <div>
                <h4 className="font-medium">
                  {key.provider.toUpperCase()}
                  {key.key_name && ` - ${key.key_name}`}
                </h4>
                <p className="text-sm text-gray-600">
                  Created: {new Date(key.created_at).toLocaleDateString()} |
                  Used {key.usage_count} times
                  {key.last_used && ` | Last used: ${new Date(key.last_used).toLocaleDateString()}`}
                </p>
              </div>

              <button
                onClick={() => handleDeleteApiKey(key.id)}
                className="text-red-600 hover:text-red-800"
              >
                Delete
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};