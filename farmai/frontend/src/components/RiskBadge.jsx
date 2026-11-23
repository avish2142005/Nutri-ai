import React from 'react';
import { ShieldCheck, AlertTriangle, AlertOctagon, HelpCircle } from 'lucide-react';

export default function RiskBadge({ level, score }) {
  const configs = {
    LOW: {
      bg: 'bg-emerald-50',
      border: 'border-emerald-200',
      text: 'text-emerald-800',
      badge: 'bg-emerald-600 text-white',
      bar: 'bg-emerald-500',
      icon: ShieldCheck,
      label: 'LOW RISK',
      desc: 'Disease pressure is low; standard routine maintenance is recommended.'
    },
    MEDIUM: {
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      text: 'text-amber-900',
      badge: 'bg-amber-500 text-white',
      bar: 'bg-amber-500',
      icon: AlertTriangle,
      label: 'MEDIUM RISK',
      desc: 'Moderate infection or favorable weather conditions detected; initiate cultural controls.'
    },
    HIGH: {
      bg: 'bg-rose-50',
      border: 'border-rose-200',
      text: 'text-rose-900',
      badge: 'bg-rose-600 text-white',
      bar: 'bg-rose-600',
      icon: AlertOctagon,
      label: 'HIGH RISK',
      desc: 'Aggressive disease pathogen and conducive weather detected; immediate action required.'
    },
    UNCERTAIN: {
      bg: 'bg-purple-50',
      border: 'border-purple-200',
      text: 'text-purple-900',
      badge: 'bg-purple-600 text-white',
      bar: 'bg-purple-500',
      icon: HelpCircle,
      label: 'UNCERTAIN',
      desc: 'Low visual confidence. Please capture a clear, well-lit photo of a single leaf.'
    }
  };

  const config = configs[level] || configs.LOW;
  const Icon = config.icon;

  return (
    <div className={`rounded-2xl p-5 border ${config.border} ${config.bg} shadow-sm`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`px-2.5 py-1 rounded-full text-xs font-extrabold tracking-wider ${config.badge} flex items-center gap-1.5`}>
            <Icon className="w-3.5 h-3.5" />
            {config.label}
          </span>
          <span className="text-xs font-semibold text-slate-500">Risk Assessment</span>
        </div>
        <div className="text-right">
          <span className="text-3xl font-black text-slate-900">{score}</span>
          <span className="text-xs text-slate-500 font-bold ml-1">/100</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-2.5 bg-slate-200/80 rounded-full overflow-hidden mb-2.5">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${config.bar}`}
          style={{ width: `${Math.min(100, Math.max(5, score))}%` }}
        />
      </div>

      <p className={`text-xs ${config.text} font-medium leading-relaxed`}>
        {config.desc}
      </p>
    </div>
  );
}
