import { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Command, Lock, User, ArrowRight, Loader2 } from 'lucide-react';

const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://codesense-backend-a472.onrender.com';

export default function Auth() {
  const [mode, setMode] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/${mode}`, { username, password });
      navigate('/app');
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      width: '100%',
      background: 'linear-gradient(135deg, #0a0b0f 0%, #0f1219 40%, #121829 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      position: 'relative',
      overflow: 'hidden',
    }}>

      {/* Background glow orbs */}
      <div style={{
        position: 'absolute', top: '15%', left: '20%',
        width: '400px', height: '400px',
        background: 'radial-gradient(circle, rgba(92,103,255,0.12) 0%, transparent 70%)',
        borderRadius: '50%', pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', bottom: '10%', right: '15%',
        width: '300px', height: '300px',
        background: 'radial-gradient(circle, rgba(139,92,246,0.08) 0%, transparent 70%)',
        borderRadius: '50%', pointerEvents: 'none',
      }} />

      {/* Card */}
      <div style={{
        background: 'rgba(22, 25, 35, 0.85)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: '20px',
        padding: '48px 44px',
        width: '100%',
        maxWidth: '420px',
        color: '#f0f2f5',
        boxShadow: '0 25px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(92,103,255,0.05)',
        position: 'relative',
        zIndex: 1,
      }}>

        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '36px' }}>
          <div style={{
            width: '38px', height: '38px', borderRadius: '10px',
            background: 'linear-gradient(135deg, #5c67ff, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 4px 15px rgba(92,103,255,0.3)',
          }}>
            <Command size={20} color="white" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1.05rem', letterSpacing: '-0.02em', lineHeight: 1.2 }}>
              CodeSense AI
            </div>
            <div style={{ fontSize: '0.72rem', color: '#6b7280', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              Codebase Intelligence
            </div>
          </div>
        </div>

        {/* Heading */}
        <div style={{ marginBottom: '32px' }}>
          <h2 style={{
            fontSize: '1.6rem', fontWeight: 700, letterSpacing: '-0.03em',
            margin: '0 0 6px', color: '#f0f2f5', lineHeight: 1.2,
          }}>
            {mode === 'login' ? 'Welcome back' : 'Create account'}
          </h2>
          <p style={{ fontSize: '0.88rem', color: '#6b7280', margin: 0 }}>
            {mode === 'login'
              ? 'Sign in to continue to your workspace'
              : 'Start exploring your codebase with AI'}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>

          {/* Username field */}
          <div style={{ position: 'relative' }}>
            <div style={{
              position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)',
              color: '#4b5563', pointerEvents: 'none',
            }}>
              <User size={16} />
            </div>
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              style={{
                width: '100%',
                background: 'rgba(15,17,26,0.6)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '10px',
                padding: '13px 14px 13px 40px',
                color: '#f0f2f5',
                fontSize: '14px',
                outline: 'none',
                transition: 'border-color 0.2s, box-shadow 0.2s',
                fontFamily: 'inherit',
              }}
              onFocus={e => {
                e.target.style.borderColor = '#5c67ff';
                e.target.style.boxShadow = '0 0 0 3px rgba(92,103,255,0.12)';
              }}
              onBlur={e => {
                e.target.style.borderColor = 'rgba(255,255,255,0.08)';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          {/* Password field */}
          <div style={{ position: 'relative' }}>
            <div style={{
              position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)',
              color: '#4b5563', pointerEvents: 'none',
            }}>
              <Lock size={16} />
            </div>
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              style={{
                width: '100%',
                background: 'rgba(15,17,26,0.6)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '10px',
                padding: '13px 14px 13px 40px',
                color: '#f0f2f5',
                fontSize: '14px',
                outline: 'none',
                transition: 'border-color 0.2s, box-shadow 0.2s',
                fontFamily: 'inherit',
              }}
              onFocus={e => {
                e.target.style.borderColor = '#5c67ff';
                e.target.style.boxShadow = '0 0 0 3px rgba(92,103,255,0.12)';
              }}
              onBlur={e => {
                e.target.style.borderColor = 'rgba(255,255,255,0.08)';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          {/* Error */}
          {error && (
            <div style={{
              background: 'rgba(239,68,68,0.1)',
              border: '1px solid rgba(239,68,68,0.2)',
              borderRadius: '8px',
              padding: '10px 12px',
              color: '#fca5a5',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}>
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            style={{
              background: loading
                ? 'rgba(92,103,255,0.5)'
                : 'linear-gradient(135deg, #5c67ff, #7c3aed)',
              color: '#fff',
              border: 'none',
              borderRadius: '10px',
              padding: '13px',
              fontWeight: 600,
              fontSize: '15px',
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              marginTop: '4px',
              transition: 'opacity 0.2s, transform 0.1s',
              boxShadow: loading ? 'none' : '0 4px 15px rgba(92,103,255,0.35)',
              letterSpacing: '-0.01em',
              fontFamily: 'inherit',
            }}
            onMouseOver={e => { if (!loading) e.currentTarget.style.opacity = '0.92'; }}
            onMouseOut={e => { e.currentTarget.style.opacity = '1'; }}
            onMouseDown={e => { if (!loading) e.currentTarget.style.transform = 'scale(0.985)'; }}
            onMouseUp={e => { e.currentTarget.style.transform = 'scale(1)'; }}
          >
            {loading
              ? <><Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> Please wait...</>
              : <>{mode === 'login' ? 'Sign in' : 'Create account'} <ArrowRight size={16} /></>
            }
          </button>
        </form>

        {/* Divider */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '12px',
          margin: '24px 0',
        }}>
          <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.06)' }} />
          <span style={{ color: '#4b5563', fontSize: '12px' }}>or</span>
          <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.06)' }} />
        </div>

        {/* Toggle mode */}
        <p style={{ textAlign: 'center', fontSize: '13.5px', color: '#6b7280', margin: 0 }}>
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}
            style={{
              background: 'none', border: 'none',
              color: '#818cf8', cursor: 'pointer',
              fontWeight: 600, fontSize: '13.5px',
              textDecoration: 'underline', textDecorationColor: 'rgba(129,140,248,0.4)',
              fontFamily: 'inherit',
              transition: 'color 0.15s',
            }}
            onMouseOver={e => e.currentTarget.style.color = '#a5b4fc'}
            onMouseOut={e => e.currentTarget.style.color = '#818cf8'}
          >
            {mode === 'login' ? 'Register' : 'Sign in'}
          </button>
        </p>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
