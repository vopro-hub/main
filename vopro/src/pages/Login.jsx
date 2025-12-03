import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import '../static/Login.css'; // 👈 Link to external CSS file
import {useNavigate, Link } from 'react-router-dom';

function Login() {
  const [form, setForm] = useState({ username: '', password: '' });
  const [errorMsg, setErrorMsg] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setErrorMsg(null);
    setLoading(true);

    try {
      await login(form);
      navigate('/office');
    } catch (error) {
      if (error.response?.status === 401) {
        setErrorMsg('Invalid username or password.');
      } else if (error.response) {
        setErrorMsg(`Error: ${error.response.status} - ${error.response.data.detail || 'Login failed'}`);
      } else if (error.request) {
        setErrorMsg('No response from server. Check your connection.');
      } else {
        setErrorMsg(error.message);
      }
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <form onSubmit={handleSubmit} className="login-form">
        <h2>Login</h2>
        <input
          name="username"
          onChange={handleChange}
          placeholder="Username"
          required
          value={form.username}
          className="login-input"
        />
        <input
          type="password"
          name="password"
          onChange={handleChange}
          placeholder="Password"
          required
          value={form.password}
          className="login-input"
        />
        <p className="forgot-password">
          <Link to="/forgot-password">Forgot Password?</Link>
        </p>
        <button type="submit" disabled={loading} className="login-button">
          {loading ? 'Logging in...' : 'Login'}
        </button>
        {errorMsg && <p className="error-message">{errorMsg}</p>}
       <p>
          Don’t have an account? <Link to="/register">Register</Link>
        </p>
      </form>
    </div>
  );
}

export default Login;
