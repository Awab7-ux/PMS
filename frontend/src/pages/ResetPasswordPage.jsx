import { useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { authApi } from '../services/api';

export default function ResetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await authApi.resetPassword(params.get('token') || '', password);
      setSuccess('Password reset successful. You can now sign in.');
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card card">
        <h1>New password</h1>
        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="label">New Password</label>
            <input className="input" type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={12} />
          </div>
          <button className="btn btn-primary" style={{ width: '100%' }}>Reset password</button>
        </form>
        <div className="footer"><Link to="/login">Back to login</Link></div>
      </div>
    </div>
  );
}
