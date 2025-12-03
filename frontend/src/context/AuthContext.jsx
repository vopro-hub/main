import { createContext, useState, useEffect } from 'react';
import { api, me } from '../api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const savedUser = sessionStorage.getItem('user');
    return savedUser ? JSON.parse(savedUser) : null;
  });

  const [token, setToken] = useState(() => sessionStorage.getItem('token') || null);
  const [loading, setLoading] = useState(true);

  // Load user if a session token exists
  useEffect(() => {
    const loadUser = async () => {
      if (token && !user) {
        try {
          const userData = await me();
          setUser(userData);

          // save user to session
          sessionStorage.setItem('user', JSON.stringify(userData));
        } catch (err) {
          console.error('Session validation failed:', err);
          logout();
        }
      }
      setLoading(false);
    };
    loadUser();
  }, [token]);

  // 🔐 Login
  const login = async (credentials) => {
    const res = await api.post('accounts/login/', credentials);
    const { access, user } = res.data;

    setToken(access);
    setUser(user);

    // save session
    sessionStorage.setItem('token', access);
    sessionStorage.setItem('user', JSON.stringify(user));
  };

  // 🧾 Register
  const register = async (formData) => {
    await api.post('accounts/register/', formData);
    // auto login after register
    await login({
      username: formData.username,
      password: formData.password,
    });
  };

  // 🔓 Logout (clear sessionStorage)
  const logout = () => {
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
