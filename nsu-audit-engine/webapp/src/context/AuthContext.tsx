import { createContext, useContext, useState, useEffect } from 'react';
import type { AuthContextType, UserProfile } from '../types';
import { api } from '../services/api';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('nsu_token'));
  const [user, setUser] = useState<UserProfile | null>(null);

  const login = (newToken: string, userProfile: UserProfile) => {
    localStorage.setItem('nsu_token', newToken);
    setToken(newToken);
    setUser(userProfile);
  };

  const logout = () => {
    localStorage.removeItem('nsu_token');
    setToken(null);
    setUser(null);
  };

  useEffect(() => {
    if (token && !user) {
      api.get('/api/v1/auth/me')
        .then(response => {
          setUser(response.data);
        })
        .catch(error => {
          console.error('Failed to validate session. Logging out.', error);
          logout();
        });
    }
  }, [token, user]);

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
