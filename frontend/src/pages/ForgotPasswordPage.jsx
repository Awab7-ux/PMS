import { useState } from 'react';
import { Link } from 'react-router-dom';
import { authApi } from '../services/api';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const res = await authApi.forgotPassword(email);
      setMessage(res.message || 'If an account exists, a reset link has been sent.');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card card">
        <h1>Reset password</h1>
        <p className="subtitle">Enter your email to receive a reset link</p>
        {error && <div className="alert alert-error">{error}</div>}
        {message && <div className="alert alert-success">{message}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="label">Email</label>
            <input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <button className="btn btn-primary" style={{ width: '100%' }}>Send reset link</button>
        </form>
        <div className="footer"><Link to="/login">Back to login</Link></div>
      </div>
    </div>
  );
}
