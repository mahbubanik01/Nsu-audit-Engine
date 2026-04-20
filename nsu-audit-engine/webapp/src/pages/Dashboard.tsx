import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { UploadZone } from '../components/UploadZone';
import { api } from '../services/api';
import type { AuditResponse } from '../types';
import { LogOut, User as UserIcon, BookOpen, AlertTriangle, History, Upload, FolderOpen } from 'lucide-react';
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
  const [activeTab, setActiveTab] = useState<'audit' | 'past_audits' | 'history'>('audit');
  const [callHistory, setCallHistory] = useState<CallEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [pastAudits, setPastAudits] = useState<AuditResponse[]>([]);
  const [pastAuditsLoading, setPastAuditsLoading] = useState(false);

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
    } catch (err: any) {
      console.error('Audit Error:', err);
      const errorMessage = err.response?.data?.detail || 
        'Failed to process transcript. Ensure your local OCR tunnel is active.';
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

  const fetchPastAudits = async () => {
    setPastAuditsLoading(true);
    try {
      const res = await api.get('/api/v1/audit/history');
      setPastAudits(res.data.audits || []);
    } catch {
      console.error('Failed to fetch past audits');
    } finally {
      setPastAuditsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory();
    } else if (activeTab === 'past_audits') {
      fetchPastAudits();
    }
  }, [activeTab]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Clean Navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-slate-900 text-white p-2 rounded-lg">
              <BookOpen className="w-5 h-5" />
            </div>
            <span className="font-bold text-lg text-slate-900 tracking-tight">NSU Audit</span>
          </div>

          {/* Tab Switcher */}
          <div className="flex items-center bg-slate-100 rounded-xl p-1">
            <button
              onClick={() => setActiveTab('audit')}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-sm font-bold transition-all ${
                activeTab === 'audit'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <Upload className="w-4 h-4" />
              <span>Audit</span>
            </button>
            <button
              onClick={() => setActiveTab('past_audits')}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-sm font-bold transition-all ${
                activeTab === 'past_audits'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <FolderOpen className="w-4 h-4" />
              <span>Past Scans</span>
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-sm font-bold transition-all ${
                activeTab === 'history'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <History className="w-4 h-4" />
              <span>API Telemetry</span>
            </button>
          </div>
          
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2 text-xs font-bold text-slate-600 bg-slate-100 px-3 py-1.5 rounded-full">
              {user?.picture ? (
                <img src={user.picture} alt="" className="w-4 h-4 rounded-full" />
              ) : (
                <UserIcon className="w-4 h-4" />
              )}
              <span>{user?.name || user?.email}</span>
            </div>
            <button 
              onClick={logout}
              className="text-slate-400 hover:text-red-600 transition-colors"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        
        {activeTab === 'audit' && (
          <div className="space-y-8">
            {!auditData && (
              <section className="space-y-8 py-10 text-center max-w-2xl mx-auto">
                <div className="space-y-2">
                  <h2 className="text-3xl font-black text-slate-900 tracking-tight">Transcript Audit</h2>
                  <p className="text-slate-500 font-medium text-lg">Upload your NSU advising transcript for verification.</p>
                </div>

                <div className="space-y-6">
                   <div className="flex items-center justify-center space-x-3 bg-white border border-slate-200 px-5 py-3 rounded-2xl shadow-sm inline-flex">
                      <span className="text-xs font-black text-slate-500 uppercase tracking-widest">Program:</span>
                      <select 
                        value={program} 
                        onChange={(e) => setProgram(e.target.value)}
                        className="bg-transparent border-none focus:ring-0 font-bold text-slate-900 cursor-pointer outline-none"
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
                  <div className="bg-red-50 text-red-700 p-5 rounded-2xl border border-red-100 flex items-start space-x-4 text-left">
                    <AlertTriangle className="w-6 h-6 shrink-0 mt-0.5" />
                    <div className="text-sm font-bold leading-relaxed">{error}</div>
                  </div>
                )}
              </section>
            )}

            {auditData && (
              <div className="space-y-6">
                <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                  <h2 className="text-2xl font-black text-slate-900 tracking-tight">Audit Report</h2>
                  <button 
                    onClick={() => setAuditData(null)}
                    className="text-xs font-black uppercase tracking-widest bg-slate-100 hover:bg-slate-200 text-slate-900 px-4 py-2 rounded-lg transition-all"
                  >
                    Scan New
                  </button>
                </div>
                <AuditResults data={auditData} />
              </div>
            )}
          </div>
        )}

        {activeTab === 'history' && (
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-black text-slate-900 tracking-tight">API Telemetry</h2>
              <button
                onClick={fetchHistory}
                disabled={historyLoading}
                className="text-xs font-black uppercase tracking-widest bg-slate-900 text-white px-4 py-2 rounded-lg disabled:opacity-50"
              >
                {historyLoading ? 'Syncing...' : 'Refresh'}
              </button>
            </div>

            <div className="bg-white border border-slate-200 rounded-3xl overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-black text-[10px] uppercase tracking-widest">
                      <th className="px-6 py-4">Method</th>
                      <th className="px-6 py-4">Endpoint</th>
                      <th className="px-6 py-4 text-center">Status</th>
                      <th className="px-6 py-4 text-right">Latency</th>
                      <th className="px-6 py-4 text-right">Time</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-medium">
                    {callHistory.map((call) => (
                      <tr key={call.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-6 py-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-black tracking-widest ${
                            call.method === 'POST' ? 'bg-blue-50 text-blue-700' : 'bg-emerald-50 text-emerald-700'
                          }`}>
                            {call.method}
                          </span>
                        </td>
                        <td className="px-6 py-4 font-mono text-xs text-slate-500 truncate max-w-[150px]">
                          {call.path}
                        </td>
                        <td className={`px-6 py-4 text-center font-bold ${call.status_code < 300 ? 'text-emerald-600' : 'text-red-600'}`}>
                          {call.status_code}
                        </td>
                        <td className="px-6 py-4 text-right text-slate-400 font-mono text-xs">
                          {call.duration_ms.toFixed(0)}ms
                        </td>
                        <td className="px-6 py-4 text-right text-slate-400 text-[10px] font-bold uppercase">
                          {new Date(call.timestamp).toLocaleTimeString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        )}

        {activeTab === 'past_audits' && (
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-black text-slate-900 tracking-tight">Past Scans</h2>
              <button
                onClick={fetchPastAudits}
                disabled={pastAuditsLoading}
                className="text-xs font-black uppercase tracking-widest bg-slate-900 text-white px-4 py-2 rounded-lg disabled:opacity-50"
              >
                {pastAuditsLoading ? 'Syncing...' : 'Refresh'}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {pastAudits.length === 0 && !pastAuditsLoading && (
                <div className="col-span-full py-10 text-center text-slate-500 font-medium bg-white rounded-3xl border border-slate-200 shadow-sm">
                  No past scans found.
                </div>
              )}
              {pastAudits.map((audit, idx) => (
                <div key={idx} className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-4 hover:border-blue-200 transition-colors">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-black text-slate-900 text-lg">{audit.student.name}</h3>
                      <p className="text-xs font-bold text-slate-500">{audit.student.id} • {audit.program}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-[10px] font-black tracking-widest uppercase ${audit.summary.is_eligible ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
                      {audit.summary.is_eligible ? 'Eligible' : 'Not Eligible'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <div className="font-bold text-slate-700">CGPA: <span className="font-black text-slate-900">{audit.summary.cgpa.toFixed(2)}</span></div>
                    <div className="text-xs text-slate-400 font-medium">
                      {(audit as any).scan_timestamp ? new Date((audit as any).scan_timestamp).toLocaleString() : 'Recent'}
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setAuditData(audit);
                      setActiveTab('audit');
                    }}
                    className="w-full text-center py-2.5 bg-slate-50 hover:bg-slate-100 text-slate-900 font-black text-[10px] uppercase tracking-widest rounded-xl transition-colors"
                  >
                    View Full Report
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}


