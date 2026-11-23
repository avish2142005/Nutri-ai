import React, { useState } from 'react';
import { Eye, ShieldAlert, Sparkles, Activity, Layers } from 'lucide-react';

export default function SeverityGauge({ severity, originalImageUrl }) {
  const [showOverlay, setShowOverlay] = useState(false);

  if (!severity) return null;

  const {
    level = 'Mild',
    score = 0.2,
    affected_percentage = 0,
    lesion_count = 0,
    canopy_risk = 'Low',
    action_urgency = 'Monitoring',
    overlay_image = null
  } = severity;

  const levelStyles = {
    Healthy: {
      badgeBg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      barColor: 'bg-emerald-500',
      textColor: 'text-emerald-700',
      description: 'Zero or negligible lesion symptoms detected on leaf surface.'
    },
    Mild: {
      badgeBg: 'bg-sky-50 text-sky-700 border-sky-200',
      barColor: 'bg-sky-500',
      textColor: 'text-sky-700',
      description: 'Early focal lesions covering less than 15% of leaf surface.'
    },
    Moderate: {
      badgeBg: 'bg-amber-50 text-amber-700 border-amber-200',
      barColor: 'bg-amber-500',
      textColor: 'text-amber-700',
      description: 'Spreading lesions covering 15% - 35% of leaf surface.'
    },
    Severe: {
      badgeBg: 'bg-rose-50 text-rose-700 border-rose-200',
      barColor: 'bg-rose-500',
      textColor: 'text-rose-700',
      description: 'Extensive necrosis (>35% leaf area) with high risk of defoliation.'
    }
  };

  const currentStyle = levelStyles[level] || levelStyles.Mild;

  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Automated Severity Quantification
            </span>
            <h4 className="text-sm font-bold text-slate-800">
              Disease Severity Estimation
            </h4>
          </div>
        </div>

        <span className={`text-xs px-3 py-1 rounded-full font-bold border ${currentStyle.badgeBg}`}>
          {level.toUpperCase()} SEVERITY
        </span>
      </div>

      {/* Progress Bar Gauge */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
          <span>Affected Foliar Area</span>
          <span className={`font-black ${currentStyle.textColor}`}>{affected_percentage.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden p-0.5">
          <div
            className={`h-full rounded-full transition-all duration-500 ${currentStyle.barColor}`}
            style={{ width: `${Math.min(100, Math.max(4, affected_percentage))}%` }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-slate-400 font-medium px-0.5">
          <span>Healthy (0%)</span>
          <span>Mild (&le;15%)</span>
          <span>Moderate (&le;35%)</span>
          <span>Severe (&gt;35%)</span>
        </div>
      </div>

      {/* Key Metric Cards */}
      <div className="grid grid-cols-3 gap-3 text-center">
        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
          <span className="text-[10px] font-bold text-slate-400 block uppercase">Lesion Count</span>
          <span className="text-base font-black text-slate-800">{lesion_count}</span>
        </div>
        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
          <span className="text-[10px] font-bold text-slate-400 block uppercase">Canopy Risk</span>
          <span className="text-xs font-bold text-slate-700 block mt-1">{canopy_risk}</span>
        </div>
        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
          <span className="text-[10px] font-bold text-slate-400 block uppercase">Urgency</span>
          <span className="text-[11px] font-bold text-emerald-700 block mt-1 truncate" title={action_urgency}>
            {action_urgency}
          </span>
        </div>
      </div>

      {/* Visual Diagnostic Overlay Toggle */}
      {overlay_image && (
        <div className="pt-2 border-t border-slate-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-emerald-600" />
              <span>Computer Vision Lesion Segmentation</span>
            </span>
            <button
              type="button"
              onClick={() => setShowOverlay(!showOverlay)}
              className="text-xs font-bold px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 flex items-center gap-1 transition-colors"
            >
              <Eye className="w-3.5 h-3.5" />
              <span>{showOverlay ? 'Hide Lesion Overlay' : 'View AI Lesion HUD'}</span>
            </button>
          </div>

          {showOverlay && (
            <div className="mt-2 rounded-xl overflow-hidden border border-slate-200 bg-slate-900 shadow-md">
              <img
                src={overlay_image}
                alt="AI Lesion HUD Overlay"
                className="w-full max-h-64 object-contain mx-auto"
              />
              <div className="p-2 bg-slate-800 text-[11px] text-slate-300 text-center font-medium">
                Contour boundaries highlight chlorotic and necrotic tissue segmented by HSV morphological masks.
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
