import { createContext, useContext, useState, useEffect } from 'react';
import type { AuthContextType, UserProfile } from '../types';
import { api } from '../services/api';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function loadStoredUser(): UserProfile | null {
  try {
    const raw = localStorage.getItem('nsu_user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('nsu_token'));
  const [user, setUser] = useState<UserProfile | null>(loadStoredUser());

  const login = (newToken: string, userProfile: UserProfile) => {
    localStorage.setItem('nsu_token', newToken);
    localStorage.setItem('nsu_user', JSON.stringify(userProfile));
    setToken(newToken);
    setUser(userProfile);
  };

  const logout = () => {
    localStorage.removeItem('nsu_token');
    localStorage.removeItem('nsu_user');
    setToken(null);
    setUser(null);
  };

  useEffect(() => {
    if (token && !user) {
      // No stored profile — validate token and build a minimal profile from /me
      api.get('/api/v1/auth/me')
        .then(response => {
          const profile: UserProfile = {
            email: response.data.email,
            name: response.data.name || response.data.email.split('@')[0],
            domain: response.data.domain,
            role: response.data.role,
          };
          localStorage.setItem('nsu_user', JSON.stringify(profile));
          setUser(profile);
        })
        .catch(() => {
          logout();
        });
    }
  }, [token]);

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
