import { useState, useEffect } from 'react';
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
  const [googleScriptLoaded, setGoogleScriptLoaded] = useState(false);

  // Dev/OTP Login state
  const [showEmailLogin, setShowEmailLogin] = useState(false);
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [devMessage, setDevMessage] = useState('');

  const GOOGLE_CLIENT_ID = '834924534674-dpe5j0pogrc64c3j23v6d2584ubn72kn.apps.googleusercontent.com';

  useEffect(() => {
    // Check if Google Identity Services script is loaded
    const checkScript = () => {
      if ((window as any).google?.accounts?.id) {
        console.log('✅ Google Identity Services loaded');
        setGoogleScriptLoaded(true);
      } else {
        console.warn('⏳ Waiting for Google script...');
        setTimeout(checkScript, 500);
      }
    };
    checkScript();
  }, []);

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
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Authentication failed. Please use your NSU email.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

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
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to send OTP.';
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
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Invalid OTP.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-center items-center p-6">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-2xl p-10 space-y-8 border border-slate-200">
        
        <div className="text-center space-y-4">
          <div className="mx-auto w-20 h-20 bg-slate-50 rounded-2xl flex items-center justify-center border border-slate-100">
            <GraduationCap className="w-10 h-10 text-slate-900" />
          </div>
          <div className="space-y-1">
            <h1 className="text-3xl font-black text-slate-900 tracking-tight">NSU Audit</h1>
            <p className="text-slate-500 font-medium text-sm">Graduation Verification Portal</p>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-100 text-red-600 px-4 py-3 rounded-xl flex items-start space-x-3 text-sm font-semibold">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <p>{error}</p>
          </div>
        )}

        <div className="space-y-6">
          {isLoading ? (
            <div className="flex flex-col items-center py-8 text-slate-500 space-y-3">
              <Loader2 className="w-8 h-8 animate-spin text-slate-900" />
              <span className="text-sm font-bold uppercase tracking-widest">Processing...</span>
            </div>
          ) : !showEmailLogin ? (
            <div className="space-y-6">
              {/* Google Sign-in Wrapper */}
              <div id="google-button-container" className="flex justify-center min-h-[44px] w-full">
                {googleScriptLoaded ? (
                  <GoogleLogin
                    onSuccess={handleGoogleSuccess}
                    onError={() => setError('Google sign-in failed.')}
                    useOneTap
                    theme="filled_blue"
                    size="large"
                    shape="pill"
                    width="320"
                  />
                ) : (
                  <div className="animate-pulse bg-slate-100 h-11 w-full rounded-full" />
                )}
              </div>
              
              <div className="relative">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-200"></div></div>
                <div className="relative flex justify-center text-[10px] uppercase font-black tracking-widest text-slate-400">
                  <span className="bg-white px-4 italic">Alternative Access</span>
                </div>
              </div>

              <button
                onClick={() => setShowEmailLogin(true)}
                className="w-full flex items-center justify-center space-x-3 bg-slate-900 hover:bg-slate-800 text-white font-bold py-3.5 px-6 rounded-full transition-all active:scale-95 shadow-lg shadow-slate-900/10"
              >
                <Mail className="w-5 h-5" />
                <span>Sign in with Email</span>
              </button>
            </div>
          ) : !otpSent ? (
            <div className="space-y-4">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="student@northsouth.edu"
                className="w-full px-5 py-3.5 rounded-2xl border-2 border-slate-100 focus:border-slate-900 focus:outline-none transition-all font-medium"
              />
              <button
                onClick={handleRequestOtp}
                disabled={!email}
                className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-3.5 px-6 rounded-2xl transition-all disabled:opacity-50"
              >
                Request OTP
              </button>
              <button
                onClick={() => setShowEmailLogin(false)}
                className="w-full text-slate-400 hover:text-slate-900 text-xs font-bold transition-colors"
              >
                ← Use Google Sign-In
              </button>
            </div>
          ) : (
            <div className="space-y-5">
              {devMessage && (
                <div className="bg-emerald-50 border border-emerald-100 text-emerald-700 px-4 py-3 rounded-xl text-xs font-mono text-center">
                  {devMessage}
                </div>
              )}
              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                placeholder="6-digit code"
                maxLength={6}
                className="w-full px-5 py-4 rounded-2xl border-2 border-slate-100 text-center tracking-[0.5em] text-2xl font-black focus:border-slate-900 focus:outline-none transition-all"
              />
              <button
                onClick={handleVerifyOtp}
                disabled={otp.length !== 6}
                className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-3.5 px-6 rounded-2xl transition-all disabled:opacity-50"
              >
                Verify & Login
              </button>
            </div>
          )}
        </div>
        
        <p className="text-[10px] text-center text-slate-300 font-black uppercase tracking-[0.2em] pt-4">
          Automated Graduation Audit
        </p>
      </div>
    </div>
  );
}


