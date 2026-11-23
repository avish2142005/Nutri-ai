import React, { useState, useEffect } from 'react';
import { 
  Sprout, 
  Activity, 
  Layers, 
  History as HistoryIcon, 
  ShieldCheck, 
  User, 
  LogOut, 
  LogIn, 
  UserPlus,
  Camera
} from 'lucide-react';
import { api } from './api/client';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import FieldMap from './pages/FieldMap';
import AuthModal from './components/AuthModal';
import LiveCameraScanner from './components/LiveCameraScanner';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [health, setHealth] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authInitialMode, setAuthInitialMode] = useState('signin');
  const [cameraOpen, setCameraOpen] = useState(false);

  // Check stored user session and backend status on mount
  useEffect(() => {
    const savedUser = localStorage.getItem('krishinetra_user');
    if (savedUser) {
      try {
        setCurrentUser(JSON.parse(savedUser));
      } catch (e) {
        console.warn('Failed to parse cached user:', e);
      }
    }

    async function checkBackend() {
      try {
        const h = await api.getHealth();
        setHealth(h);
      } catch (err) {
        setHealth({ status: 'offline', model_loaded: false, demo_mode: true });
      }
    }
    checkBackend();
  }, []);

  const handleOpenAuth = (mode = 'signin') => {
    setAuthInitialMode(mode);
    setAuthModalOpen(true);
  };

  const handleLogout = async () => {
    try {
      await api.signOut();
    } catch (_) {}
    localStorage.removeItem('krishinetra_user');
    setCurrentUser(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200/80 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Brand Logo & Title */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-700 to-green-500 flex items-center justify-center text-white shadow-md shadow-emerald-700/20">
                <Sprout className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-lg font-black text-slate-900 tracking-tight leading-none">
                  KrishiNetra
                </h1>
                <span className="text-[11px] text-emerald-700 font-semibold tracking-wide uppercase">
                  AI Agricultural Intelligence Platform
                </span>
              </div>
            </div>

            {/* Navigation Tabs */}
            <nav className="flex items-center gap-1 bg-slate-100/80 p-1 rounded-xl">
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  activeTab === 'dashboard'
                    ? 'bg-white text-emerald-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveTab('satellite')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  activeTab === 'satellite'
                    ? 'bg-white text-emerald-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Satellite NDVI
              </button>
              <button
                onClick={() => setActiveTab('history')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  activeTab === 'history'
                    ? 'bg-white text-emerald-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                History
              </button>
              <button
                onClick={() => setCameraOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 shadow-xs transition-all"
                title="Open Live Camera Scanner"
              >
                <Camera className="w-3.5 h-3.5 animate-pulse" />
                <span className="hidden sm:inline">Live Camera</span>
                <span className="sm:hidden">Camera</span>
              </button>
            </nav>

            {/* Account Criteria Controls & Health Status */}
            <div className="flex items-center gap-2.5">
              {/* User Authentication Badge / Sign In / Sign Up buttons */}
              {currentUser ? (
                <div className="flex items-center gap-2 bg-slate-50 border border-slate-200/90 rounded-xl px-2.5 py-1">
                  <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-xs">
                    {currentUser.full_name?.charAt(0) || 'F'}
                  </div>
                  <div className="hidden md:block text-left">
                    <span className="text-xs font-bold text-slate-800 block leading-tight truncate max-w-[110px]">
                      {currentUser.full_name}
                    </span>
                    <span className="text-[10px] text-emerald-700 font-semibold block uppercase">
                      {currentUser.preferred_language === 'kn' ? 'Kannada' : currentUser.preferred_language === 'tcy' ? 'Tulu' : 'Farmer'}
                    </span>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="p-1 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors ml-1"
                    title="Log out"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => handleOpenAuth('signin')}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold text-slate-700 hover:text-emerald-700 hover:bg-emerald-50 transition-all border border-slate-200"
                  >
                    <LogIn className="w-3.5 h-3.5" />
                    <span>Sign In</span>
                  </button>
                  <button
                    onClick={() => handleOpenAuth('signup')}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 shadow-xs transition-all"
                  >
                    <UserPlus className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">Sign Up</span>
                  </button>
                </div>
              )}

              {/* Health State Badge */}
              <div className="hidden lg:flex items-center gap-2">
                {health ? (
                  <div className="flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span>{health.demo_mode ? 'Demo' : 'Online'}</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-full bg-slate-100 text-slate-500 font-medium">
                    <Activity className="w-3 h-3 animate-spin" />
                    <span>Connecting...</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'satellite' && <FieldMap />}
        {activeTab === 'history' && <History />}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200/80 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>KrishiNetra: Deep Learning & IPM Agricultural Intelligence Platform</span>
          <span className="font-semibold text-emerald-700">ICAR / KVK IPM Standards Aligned</span>
        </div>
      </footer>

      {/* Auth Modal for Sign in / Sign up */}
      <AuthModal
        isOpen={authModalOpen}
        initialMode={authInitialMode}
        onClose={() => setAuthModalOpen(false)}
        onAuthSuccess={(user) => {
          setCurrentUser(user);
        }}
      />

      {/* Mobile Floating Action Camera Button (FAB) */}
      <button
        type="button"
        onClick={() => setCameraOpen(true)}
        className="fixed bottom-6 right-6 z-40 md:hidden bg-gradient-to-tr from-emerald-600 to-green-500 hover:from-emerald-500 text-white p-4 rounded-full shadow-2xl shadow-emerald-950/40 flex items-center justify-center border-2 border-white/80 active:scale-90 transition-all"
        title="Open Live Camera"
      >
        <Camera className="w-6 h-6 animate-pulse" />
      </button>

      {/* Global Live Camera Viewfinder */}
      <LiveCameraScanner
        isOpen={cameraOpen}
        onClose={() => setCameraOpen(false)}
        preferredLanguage={currentUser?.preferred_language || 'en'}
      />
    </div>
  );
}
