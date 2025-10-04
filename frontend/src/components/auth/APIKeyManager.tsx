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
  expires_at?: string;
  key_version: number;
  rotation_warning_sent: boolean;
}

interface ExpiringKey {
  id: string;
  provider: string;
  key_name?: string;
  expires_at: string;
  days_until_expiry: number;
  key_version: number;
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

  // Security feature states
  const [expiringKeys, setExpiringKeys] = useState<ExpiringKey[]>([]);
  const [showRotateDialog, setShowRotateDialog] = useState(false);
  const [rotatingKeyId, setRotatingKeyId] = useState<string | null>(null);
  const [rotatingProvider, setRotatingProvider] = useState<ApiProvider>('openai');
  const [newRotationKey, setNewRotationKey] = useState('');

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

  const loadExpiringKeys = useCallback(async () => {
    const token = localStorage.getItem('auth_token');
    if (!token) return;

    try {
      const response = await fetch(buildApiUrl('/api/auth/api-keys/expiring'), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setExpiringKeys(data.expiring_keys || []);
      }
    } catch (error) {
      console.error('Failed to load expiring keys:', error);
    }
  }, []);

  useEffect(() => {
    void loadUserInfo();
  }, [loadUserInfo]);

  useEffect(() => {
    void loadExpiringKeys();
  }, [loadExpiringKeys]);

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

  const handleRotateApiKey = async (keyId: string, provider: ApiProvider) => {
    setRotatingKeyId(keyId);
    setRotatingProvider(provider);
    setShowRotateDialog(true);
  };

  const confirmRotateApiKey = async () => {
    if (!rotatingKeyId || !newRotationKey) return;

    try {
      const token = localStorage.getItem('auth_token');
      if (!token) throw new Error('Authentication token is missing');

      const response = await fetch(buildApiUrl(`/api/auth/api-keys/${rotatingKeyId}/rotate`), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          new_api_key: newRotationKey,
          provider: rotatingProvider,
          key_name: apiKeys.find(k => k.id === rotatingKeyId)?.key_name
        })
      });

      if (response.ok) {
        await loadApiKeys();
        await loadExpiringKeys();
        setShowRotateDialog(false);
        setRotatingKeyId(null);
        setNewRotationKey('');
        alert('API key rotated successfully!');
      } else {
        const message = await parseApiError(response, 'Failed to rotate API key');
        throw new Error(message);
      }
    } catch (error) {
      console.error('Error rotating API key:', error);
      if (error instanceof Error) {
        alert(error.message);
      }
    }
  };

  // Helper function to calculate days until expiry
  const getDaysUntilExpiry = (expiresAt?: string): number | null => {
    if (!expiresAt) return null;
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffMs = expiry.getTime() - now.getTime();
    return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  };

  // Helper function to get expiration badge color
  const getExpirationBadge = (expiresAt?: string): { text: string; color: string } | null => {
    const days = getDaysUntilExpiry(expiresAt);
    if (days === null) return null;

    if (days < 0) {
      return { text: 'Expired', color: 'bg-red-100 text-red-800 border-red-300' };
    } else if (days <= 7) {
      return { text: `${days}d left`, color: 'bg-red-100 text-red-800 border-red-300' };
    } else if (days <= 30) {
      return { text: `${days}d left`, color: 'bg-yellow-100 text-yellow-800 border-yellow-300' };
    } else {
      return { text: `${days}d left`, color: 'bg-green-100 text-green-800 border-green-300' };
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

      {/* Expiring Keys Warning Widget */}
      {expiringKeys.length > 0 && (
        <div className="mb-6 p-4 border-l-4 border-orange-500 bg-orange-50 rounded-r-lg">
          <div className="flex items-start">
            <svg className="w-6 h-6 text-orange-500 mr-3 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="flex-1">
              <h4 className="text-lg font-semibold text-orange-900 mb-2">
                {expiringKeys.length} API Key{expiringKeys.length > 1 ? 's' : ''} Expiring Soon
              </h4>
              <p className="text-sm text-orange-800 mb-3">
                The following keys will expire within 7 days. Rotate them to maintain uninterrupted service.
              </p>
              <div className="space-y-2">
                {expiringKeys.map((key) => (
                  <div key={key.id} className="flex justify-between items-center bg-white p-3 rounded-md border border-orange-200">
                    <div>
                      <span className="font-medium text-gray-900">
                        {key.provider.toUpperCase()}
                        {key.key_name && ` - ${key.key_name}`}
                      </span>
                      <span className="ml-2 text-sm text-orange-700">
                        (v{key.key_version}, expires in {key.days_until_expiry} day{key.days_until_expiry !== 1 ? 's' : ''})
                      </span>
                    </div>
                    <button
                      onClick={() => handleRotateApiKey(key.id, key.provider as ApiProvider)}
                      className="text-sm bg-orange-600 text-white px-3 py-1 rounded hover:bg-orange-700"
                    >
                      Rotate Now
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

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
          apiKeys.map((key) => {
            const badge = getExpirationBadge(key.expires_at);

            return (
              <div key={key.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-medium text-lg">
                        {key.provider.toUpperCase()}
                        {key.key_name && ` - ${key.key_name}`}
                      </h4>
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                        v{key.key_version}
                      </span>
                      {badge && (
                        <span className={`text-xs px-2 py-1 rounded-full border ${badge.color}`}>
                          {badge.text}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600">
                      Created: {new Date(key.created_at).toLocaleDateString()} |
                      Used {key.usage_count} times
                      {key.last_used && ` | Last used: ${new Date(key.last_used).toLocaleDateString()}`}
                    </p>
                    {key.expires_at && (
                      <p className="text-xs text-gray-500 mt-1">
                        Expires: {new Date(key.expires_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>

                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => handleRotateApiKey(key.id, key.provider as ApiProvider)}
                      className="text-blue-600 hover:text-blue-800 px-3 py-1 text-sm border border-blue-300 rounded hover:bg-blue-50 flex items-center gap-1"
                      title="Rotate API key"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Rotate
                    </button>
                    <button
                      onClick={() => handleDeleteApiKey(key.id)}
                      className="text-red-600 hover:text-red-800 px-3 py-1 text-sm border border-red-300 rounded hover:bg-red-50"
                      title="Delete API key"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Rotation Dialog Modal */}
      {showRotateDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
            <h3 className="text-xl font-semibold mb-4">Rotate API Key</h3>
            <p className="text-sm text-gray-600 mb-4">
              Provide a new {rotatingProvider?.toUpperCase()} API key to replace the existing one.
              The version will be incremented and the old key will be securely removed.
            </p>

            <div className="mb-4">
              <label htmlFor="rotation_key" className="block text-sm font-medium text-gray-700 mb-2">
                New {rotatingProvider?.toUpperCase()} API Key
              </label>
              <input
                type="password"
                id="rotation_key"
                value={newRotationKey}
                onChange={(e) => setNewRotationKey(e.target.value)}
                placeholder="sk-..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
              />
            </div>

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowRotateDialog(false);
                  setRotatingKeyId(null);
                  setNewRotationKey('');
                }}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmRotateApiKey}
                disabled={!newRotationKey}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Rotate Key
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};