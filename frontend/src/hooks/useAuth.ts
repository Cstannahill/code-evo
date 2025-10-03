import { useState, useEffect, createContext, useContext } from "react";
import { apiClient } from "../api/client";

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
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const useAuthProvider = (): AuthContextType => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem("auth_token");
    if (savedToken) {
      setToken(savedToken);
      loadUserInfo();
    } else {
      setLoading(false);
    }
  }, []);

  const loadUserInfo = async (): Promise<void> => {
    try {
      const userData = await apiClient.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error("Failed to load user info:", error);
      localStorage.removeItem("auth_token");
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username: string, password: string) => {
    const tokenData: AuthToken = await apiClient.login({ username, password });
    setToken(tokenData.access_token);
    localStorage.setItem("auth_token", tokenData.access_token);

    // Load full user info
    await loadUserInfo();
  };

  const register = async (data: RegisterData) => {
    await apiClient.register(data);
    // Auto-login after registration
    await login(data.username, data.password);
  };

  const loginAsGuest = async () => {
    const tokenData: AuthToken = await apiClient.createGuestSession();
    setToken(tokenData.access_token);
    localStorage.setItem("auth_token", tokenData.access_token);

    // Load guest user info
    await loadUserInfo();
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("auth_token");
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
    logout,
  };
};

export { AuthContext };
