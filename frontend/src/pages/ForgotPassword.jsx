import { useState } from 'react';
import axios from 'axios';
import '../static/ForgetPassword.css';
import { Link } from 'react-router-dom';

function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/api/password-reset/', { email });
      setMessage('Password reset link sent to your email.');
    } catch (err) {
      setMessage('Failed to send reset link.');
    }
  };

  return (
    <div className="form-container">
      <h2>Reset Your Password</h2>
      <form onSubmit={handleSubmit} className="form">
        <input
          type="email"
          placeholder="Enter your registered email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
        />
        <button type="submit">Send Reset Link</button>
        {message && <p className="error">{message}</p>}
         <p>Remember password? <Link to="/login">Login</Link></p>
      </form>
    </div>
  );
}

export default ForgotPassword;
