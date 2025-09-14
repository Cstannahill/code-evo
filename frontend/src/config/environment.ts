// Environment configuration for Code Evolution Tracker
// Automatically detects and configures API endpoints based on environment

interface EnvironmentConfig {
  apiBaseUrl: string;
  environment: 'development' | 'production';
  isLocal: boolean;
}

function getEnvironmentConfig(): EnvironmentConfig {
  // Check if we're running in development mode
  const isDevelopment = import.meta.env.DEV;
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  
  // Get API URL from environment variable or use defaults
  const envApiUrl = import.meta.env.VITE_API_BASE_URL;
  
  let apiBaseUrl: string;
  let environment: 'development' | 'production';
  
  if (isDevelopment && isLocal) {
    // Local development - use localhost backend
    apiBaseUrl = envApiUrl || 'http://localhost:8080';
    environment = 'development';
  } else if (envApiUrl) {
    // Production with custom API URL (from environment variable)
    apiBaseUrl = envApiUrl;
    environment = 'production';
  } else {
    // Default production Railway URL
    apiBaseUrl = 'https://backend-production-712a.up.railway.app';
    environment = 'production';
  }
  
  return {
    apiBaseUrl,
    environment,
    isLocal
  };
}

// Export the configuration
export const config = getEnvironmentConfig();

// Helper functions
export const isLocalDevelopment = () => config.isLocal && config.environment === 'development';
export const isProduction = () => config.environment === 'production';
export const getApiBaseUrl = () => config.apiBaseUrl;

// Log configuration for debugging
if (isLocalDevelopment()) {
  console.log('🔧 Environment Config:', {
    apiBaseUrl: config.apiBaseUrl,
    environment: config.environment,
    isLocal: config.isLocal,
    hostname: window.location.hostname,
    dev: import.meta.env.DEV
  });
}
