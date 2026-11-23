import React, { useState, useEffect } from 'react';
import { History as HistoryIcon, Clock, ChevronRight, Calendar, AlertCircle } from 'lucide-react';
import { api } from '../api/client';

export default function History({ onSelectAnalysis }) {
  const [historyItems, setHistoryItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadHistory() {
      setLoading(true);
      try {
        const records = await api.getHistory();
        setHistoryItems(records);
      } catch (err) {
        console.error("Failed to load history:", err);
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, []);

  const riskBadgeStyles = {
    LOW: 'bg-emerald-100 text-emerald-800',
    MEDIUM: 'bg-amber-100 text-amber-800',
    HIGH: 'bg-rose-100 text-rose-800',
    UNCERTAIN: 'bg-purple-100 text-purple-800'
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">Audit & Archive</span>
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <HistoryIcon className="w-5 h-5 text-emerald-600" />
            Crop Diagnosis History
          </h2>
        </div>
        <span className="text-xs bg-slate-100 text-slate-700 font-bold px-3 py-1 rounded-full">
          {historyItems.length} Analyses Recorded
        </span>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-20 bg-white rounded-2xl border border-slate-200 animate-pulse" />
          ))}
        </div>
      ) : historyItems.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 border border-slate-200 text-center">
          <Clock className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-700">No Past Records Found</h3>
          <p className="text-xs text-slate-500 mt-1">Run your first crop image diagnosis on the dashboard to build field history.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm divide-y divide-slate-100 overflow-hidden">
          {historyItems.map((item) => (
            <div
              key={item.id}
              onClick={() => onSelectAnalysis && item.response_json && onSelectAnalysis(item.response_json)}
              className="p-4 hover:bg-slate-50/80 transition-colors flex items-center justify-between gap-4 cursor-pointer"
            >
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center font-black text-emerald-700 text-sm">
                  #{item.id}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-bold text-slate-900">{item.disease_label}</h4>
                    <span className="text-xs text-slate-500 font-semibold">• {item.crop}</span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-1 font-medium">
                    <Calendar className="w-3 h-3" />
                    <span>{new Date(item.created_at).toLocaleString()}</span>
                    <span>•</span>
                    <span>Confidence: {(item.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${riskBadgeStyles[item.risk_level] || 'bg-slate-100 text-slate-700'}`}>
                  {item.risk_level} ({item.risk_score} pts)
                </span>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
