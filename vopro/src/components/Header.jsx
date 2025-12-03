import React, { useContext } from 'react';
import { ThemeContext } from '../context/ThemeContext';
import '../static/header.css';

function Header({ toggleMenu }) {
  const { theme, toggleTheme } = useContext(ThemeContext); // ✅ FIXED

  return (
    <header className={`app-header theme-${theme}`}> {/* ✅ FIXED className */}
      <div className="logo">MyApp</div>

      <div className="header-buttons">
        {/* Menu toggle button */}
        <button className="menu-btn" onClick={toggleMenu}>
          &#9776;
        </button>

        {/* Theme toggle button with dynamic icon */}
        <button className="theme-toggle" onClick={toggleTheme}>
          {theme === 'dark' ? '☀️' : '🌙'} {/* ✅ FIXED */}
        </button>
      </div>
    </header>
  );
}

export default Header;
