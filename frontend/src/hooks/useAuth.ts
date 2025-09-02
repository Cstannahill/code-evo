import { useState, useEffect, createContext, useContext } from 'react';

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

interface AuthToken {
  access_token: string;
  token_type: string;
  user_id: string;
  username: string;
  is_guest: boolean;
}

interface RegisterData {
  username: string;
  email: string;
  full_name?: string;
  password: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isGuest: boolean;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  loginAsGuest: () => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const useAuthProvider = (): AuthContextType => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token');
    if (savedToken) {
      setToken(savedToken);
      loadUserInfo(savedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const loadUserInfo = async (authToken: string) => {
    try {
      const response = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        // Token might be invalid
        localStorage.removeItem('auth_token');
        setToken(null);
      }
    } catch (error) {
      console.error('Failed to load user info:', error);
      localStorage.removeItem('auth_token');
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username: string, password: string) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const tokenData: AuthToken = await response.json();
    setToken(tokenData.access_token);
    localStorage.setItem('auth_token', tokenData.access_token);
    
    // Load full user info
    await loadUserInfo(tokenData.access_token);
  };

  const register = async (data: RegisterData) => {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    // Auto-login after registration
    await login(data.username, data.password);
  };

  const loginAsGuest = async () => {
    const response = await fetch('/api/auth/guest', {
      method: 'POST'
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Guest login failed');
    }

    const tokenData: AuthToken = await response.json();
    setToken(tokenData.access_token);
    localStorage.setItem('auth_token', tokenData.access_token);
    
    // Load guest user info
    await loadUserInfo(tokenData.access_token);
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth_token');
  };

  return {
    user,
    token,
    isAuthenticated: !!user && !!token,
    isGuest: user?.is_guest || false,
    loading,
    login,
    register,
    loginAsGuest,
    logout
  };
};

export { AuthContext };