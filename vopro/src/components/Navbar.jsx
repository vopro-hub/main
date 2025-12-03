import React, { useContext } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useLocation } from 'react-router'
import { AuthContext } from '../context/AuthContext.jsx'
import '../static/navbar.css'

const Navbar = ({ isOpen, closeMenu }) => {
  const { user, logout } = useContext(AuthContext);
  const location = useLocation()

  

  const links = [
    { path: '/office', label: 'Office' },
  ]

  return (
    <nav className={`nav-drawer ${isOpen ? 'open' : ''}`}>
      <ul>
        {links.map(link => (
          <li key={link.path}>
            <NavLink
              to={link.path}
              onClick={closeMenu}
              className={({ isActive }) =>
                isActive || location.pathname === link.path ? 'active' : ''
              }
            >
              {link.label}
            </NavLink>
          </li>
        ))}
           
        {user ? (
          <>
            <li><button onClick={logout} className="logout-btn">Logout</button></li>
          </>
        ) : (
          <>
            <li><NavLink to="/login" onClick={closeMenu}>Login</NavLink></li>
            <li><NavLink to="/register" onClick={closeMenu}>Register</NavLink></li>
          </>
        )}
      </ul>
    </nav>
  )
}

export default Navbar
