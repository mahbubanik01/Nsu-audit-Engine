import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { UploadZone } from '../components/UploadZone';
import { api } from '../services/api';
import type { AuditResponse } from '../types';
import { LogOut, User as UserIcon, BookOpen, AlertTriangle, History, Upload } from 'lucide-react';
import AuditResults from '../components/AuditResults';

interface CallEntry {
  id: number;
  method: string;
  path: string;
  status_code: number;
  duration_ms: number;
  user: string | null;
  timestamp: string;
}

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [auditData, setAuditData] = useState<AuditResponse | null>(null);
  const [program, setProgram] = useState('BBA');
  const [activeTab, setActiveTab] = useState<'audit' | 'history'>('audit');
  const [callHistory, setCallHistory] = useState<CallEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const handleFileUpload = async (file: File) => {
    setIsLoading(true);
    setError(null);
    setAuditData(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('program_type', program);

    try {
      const response = await api.post('/api/v1/audit/run', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setAuditData(response.data);
    } catch (err: unknown) {
      console.error('Audit Error:', err);
      const errorMessage = (err as Record<string, any>).response?.data?.detail || 
        'Failed to process transcript. Ensure the network is online.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchHistory = async () => {
    setHistoryLoading(true);
    try {
      const res = await api.get('/api/v1/history?limit=100');
      setCallHistory(res.data.calls || []);
    } catch {
      console.error('Failed to fetch history');
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory();
    }
  }, [activeTab]);

  const methodColor = (m: string) => {
    const colors: Record<string, string> = {
      GET: 'bg-green-100 text-green-800',
      POST: 'bg-blue-100 text-blue-800',
      PUT: 'bg-yellow-100 text-yellow-800',
      DELETE: 'bg-red-100 text-red-800',
    };
    return colors[m] || 'bg-slate-100 text-slate-800';
  };

  const statusColor = (s: number) => {
    if (s < 300) return 'text-green-600';
    if (s < 400) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      {/* Navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-nsu-blue text-white p-2 rounded-lg">
              <BookOpen className="w-5 h-5" />
            </div>
            <span className="font-bold text-lg text-slate-800 tracking-tight">NSU Audit</span>
          </div>

          {/* Tab Switcher */}
          <div className="flex items-center bg-slate-100 rounded-lg p-1">
            <button
              onClick={() => setActiveTab('audit')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                activeTab === 'audit'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Audit</span>
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                activeTab === 'history'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <History className="w-3.5 h-3.5" />
              <span>API History</span>
            </button>
          </div>
          
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2 text-sm font-medium text-slate-600 bg-slate-100 px-3 py-1.5 rounded-full">
              {user?.picture ? (
                <img src={user.picture} alt="Profile" className="w-5 h-5 rounded-full" />
              ) : (
                <UserIcon className="w-4 h-4" />
              )}
              <span>{user?.name || user?.email}</span>
            </div>
            <button 
              onClick={logout}
              className="text-slate-400 hover:text-slate-900 transition-colors flex items-center space-x-1 text-sm font-medium"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        
        {/* ──── AUDIT TAB ──── */}
        {activeTab === 'audit' && (
          <>
            {!auditData && (
              <section className="space-y-6 pt-12 max-w-2xl mx-auto">
                <div className="text-center space-y-2">
                  <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
                    Upload your transcript
                  </h2>
                  <p className="text-slate-500 text-lg">
                    Drag and drop your North South University advising transcript securely.
                  </p>
                </div>

                <div className="flex flex-col items-center space-y-4">
                   <div className="flex items-center space-x-3 bg-white border border-slate-200 px-4 py-2 rounded-xl shadow-sm">
                      <span className="text-sm font-bold text-slate-600 uppercase tracking-wider">Target Program:</span>
                      <select 
                        value={program} 
                        onChange={(e) => setProgram(e.target.value)}
                        className="bg-transparent border-none focus:ring-0 font-bold text-nsu-blue cursor-pointer outline-none"
                      >
                        <option value="BBA">BBA</option>
                        <option value="CSE">CSE</option>
                      </select>
                   </div>
                   
                   <div className="w-full">
                     <UploadZone onFileSelect={handleFileUpload} isLoading={isLoading} />
                   </div>
                </div>
                
                {error && (
                  <div className="bg-red-50 text-red-700 p-4 rounded-xl border border-red-100 flex items-start space-x-3">
                    <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
                    <div className="text-sm font-medium">{error}</div>
                  </div>
                )}
              </section>
            )}

            {auditData && (
              <div>
                <div className="flex items-center justify-between mb-8">
                  <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Audit Report</h2>
                  <button 
                    onClick={() => setAuditData(null)}
                    className="text-sm bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 px-4 py-2 rounded-lg font-medium transition-colors shadow-sm"
                  >
                    Scan another document
                  </button>
                </div>
                <AuditResults data={auditData} />
              </div>
            )}
          </>
        )}

        {/* ──── HISTORY TAB ──── */}
        {activeTab === 'history' && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-slate-900 tracking-tight">API Call History</h2>
              <button
                onClick={fetchHistory}
                disabled={historyLoading}
                className="text-sm bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 px-4 py-2 rounded-lg font-medium transition-colors shadow-sm disabled:opacity-50"
              >
                {historyLoading ? 'Loading...' : 'Refresh'}
              </button>
            </div>

            {callHistory.length === 0 && !historyLoading && (
              <div className="text-center py-16 text-slate-400">
                <History className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p className="font-medium">No API calls logged yet.</p>
                <p className="text-sm mt-1">Start using the API to see calls appear here.</p>
              </div>
            )}

            {callHistory.length > 0 && (
              <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-left">
                        <th className="px-4 py-3 font-semibold text-slate-500 text-xs uppercase tracking-wider">#</th>
                        <th className="px-4 py-3 font-semibold text-slate-500 text-xs uppercase tracking-wider">Method</th>
                        <th className="px-4 py-3 font-semibold text-slate-500 text-xs uppercase tracking-wider">Path</th>
                        <th className="px-4 py-3 font-semibold text-slate-500 text-xs uppercase tracking-wider">Status</th>
                        <th className="px-4 py-3 font-semibold text-slate-500 text-xs uppercase tracking-wider">Duration</th>
                        <th className="px-4 py-3 font-semibold text-slate-500 text-xs uppercase tracking-wider">User</th>
                        <th className="px-4 py-3 font-semibold text-slate-500 text-xs uppercase tracking-wider">Time</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {callHistory.map((call) => (
                        <tr key={call.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="px-4 py-3 text-slate-400 font-mono text-xs">{call.id}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-0.5 rounded text-xs font-bold ${methodColor(call.method)}`}>
                              {call.method}
                            </span>
                          </td>
                          <td className="px-4 py-3 font-mono text-xs text-slate-700 max-w-[200px] truncate">
                            {call.path}
                          </td>
                          <td className={`px-4 py-3 font-bold text-xs ${statusColor(call.status_code)}`}>
                            {call.status_code}
                          </td>
                          <td className="px-4 py-3 text-slate-500 text-xs">
                            {call.duration_ms.toFixed(1)}ms
                          </td>
                          <td className="px-4 py-3 text-xs text-slate-500 max-w-[150px] truncate">
                            {call.user || '—'}
                          </td>
                          <td className="px-4 py-3 text-xs text-slate-400 whitespace-nowrap">
                            {new Date(call.timestamp).toLocaleTimeString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </section>
        )}

      </main>
    </div>
  );
}
