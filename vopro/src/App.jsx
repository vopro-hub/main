import { Routes, Route, Navigate } from 'react-router-dom';
import { useState, useContext } from 'react';
import { ThemeProvider } from './context/ThemeContext.jsx';
import Header from './components/Header';
import Navbar from './components/Navbar';
import { AuthProvider } from './context/AuthContext.jsx'

import Home from './pages/Home.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import Office from './pages/Office.jsx';
import PublicOffice from './pages/PublicOffice.jsx';
import Forgot_password from './pages/ForgotPassword.jsx';

function App() {
const [menuOpen, setMenuOpen] = useState(false);
  
  const toggleMenu = () => setMenuOpen(prev => !prev);
  const closeMenu = () => setMenuOpen(false);

  return (
    <ThemeProvider>
      <Header toggleMenu={toggleMenu} />
      <Navbar isOpen={menuOpen} closeMenu={closeMenu} />
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/office" element={<Office />} />
          <Route path="/public/offices/:slug" element={<PublicOffice />} />
          <Route path="/forgot-password" element={<Forgot_password />} />
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
