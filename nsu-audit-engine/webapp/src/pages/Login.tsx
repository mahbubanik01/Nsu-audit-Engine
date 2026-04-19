import { useState } from 'react';
import { GoogleLogin, type CredentialResponse } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { GraduationCap, AlertCircle, Loader2, Mail } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Dev/OTP Login state
  const [showEmailLogin, setShowEmailLogin] = useState(false);
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [devMessage, setDevMessage] = useState('');

  const GOOGLE_CLIENT_ID = '834924534674-dpe5j0pogrc64c3j23v6d2584ubn72kn.apps.googleusercontent.com';

  const handleGoogleSuccess = async (credentialResponse: CredentialResponse) => {
    setIsLoading(true);
    setError('');
    try {
      const res = await api.post('/api/v1/auth/google', {
        credential: credentialResponse.credential,
        client_id: GOOGLE_CLIENT_ID
      });
      
      const { access_token, user } = res.data;
      login(access_token, user);
      navigate('/');
    } catch (err: unknown) {
      const errorMessage = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Authentication failed. Please use your NSU email.';
      setError(errorMessage);
      console.error('Login error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // ── OTP Login Flow ──
  const handleRequestOtp = async () => {
    if (!email.endsWith('@northsouth.edu')) {
      setError('Only @northsouth.edu emails are allowed.');
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      const res = await api.post('/api/v1/auth/request-otp', { email });
      setOtpSent(true);
      setDevMessage(res.data.message || 'OTP sent!');
    } catch (err: unknown) {
      const errorMessage = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Failed to send OTP.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    setIsLoading(true);
    setError('');
    try {
      const res = await api.post('/api/v1/auth/verify-otp', { email, otp });
      const { access_token, user } = res.data;
      login(access_token, user);
      navigate('/');
    } catch (err: unknown) {
      const errorMessage = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Invalid OTP.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl border border-slate-100 p-8 space-y-8 relative overflow-hidden">
        
        {/* Decorative line */}
        <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-nsu-blue to-nsu-cyan" />
        
        <div className="text-center space-y-2">
          <div className="mx-auto w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
            <GraduationCap className="w-8 h-8 text-nsu-blue" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">NSU Audit Engine</h1>
          <p className="text-slate-500 text-sm">Sign in with your @northsouth.edu account</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-100 text-red-600 px-4 py-3 rounded-xl flex items-start space-x-3 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <p>{error}</p>
          </div>
        )}

        <div className="flex flex-col items-center justify-center w-full space-y-4 pt-4">
          {isLoading ? (
            <div className="flex flex-col items-center text-slate-500 space-y-3">
              <Loader2 className="w-6 h-6 animate-spin text-nsu-cyan" />
              <span className="text-sm font-medium">Verifying credentials...</span>
            </div>
          ) : !showEmailLogin ? (
            <>
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={() => setError('Google initialization failed. Try Email Login below.')}
                useOneTap
                theme="outline"
                size="large"
                shape="pill"
              />
              
              <div className="flex items-center w-full space-x-3 pt-2">
                <div className="flex-1 h-px bg-slate-200" />
                <span className="text-xs text-slate-400 font-medium">OR</span>
                <div className="flex-1 h-px bg-slate-200" />
              </div>

              <button
                onClick={() => setShowEmailLogin(true)}
                className="w-full flex items-center justify-center space-x-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium py-2.5 px-4 rounded-full transition-colors text-sm"
              >
                <Mail className="w-4 h-4" />
                <span>Sign in with NSU Email (OTP)</span>
              </button>
            </>
          ) : !otpSent ? (
            <div className="w-full space-y-3">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="yourname@northsouth.edu"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-nsu-blue/20 focus:border-nsu-blue"
              />
              <button
                onClick={handleRequestOtp}
                disabled={!email}
                className="w-full bg-nsu-blue hover:bg-nsu-blue/90 text-white font-medium py-2.5 px-4 rounded-xl transition-colors text-sm disabled:opacity-50"
              >
                Send OTP
              </button>
              <button
                onClick={() => setShowEmailLogin(false)}
                className="w-full text-slate-400 hover:text-slate-600 text-xs font-medium transition-colors"
              >
                ← Back to Google Sign-In
              </button>
            </div>
          ) : (
            <div className="w-full space-y-3">
              {devMessage && (
                <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 rounded-xl text-xs font-mono whitespace-pre-wrap">
                  {devMessage}
                </div>
              )}
              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                placeholder="Enter 6-digit OTP"
                maxLength={6}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm text-center tracking-widest font-bold focus:outline-none focus:ring-2 focus:ring-nsu-blue/20 focus:border-nsu-blue"
              />
              <button
                onClick={handleVerifyOtp}
                disabled={otp.length !== 6}
                className="w-full bg-nsu-blue hover:bg-nsu-blue/90 text-white font-medium py-2.5 px-4 rounded-xl transition-colors text-sm disabled:opacity-50"
              >
                Verify & Sign In
              </button>
            </div>
          )}
        </div>
        
        <p className="text-xs text-center text-slate-400 font-medium pt-4">
          Secure, automated graduation auditing.
        </p>
      </div>
    </div>
  );
}
