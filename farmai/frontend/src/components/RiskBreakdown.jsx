import React from 'react';
import { HelpCircle, CheckCircle2, ChevronRight } from 'lucide-react';

export default function RiskBreakdown({ factors = [] }) {
  if (!factors || factors.length === 0) return null;

  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
          <span>Explainable Risk Breakdown</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold">
            {factors.length} Factors
          </span>
        </h4>
        <span className="text-xs text-slate-500 font-medium">Transparent scoring</span>
      </div>

      <div className="divide-y divide-slate-100">
        {factors.map((factor, index) => {
          const isHigh = factor.points >= 15;
          const isMedium = factor.points > 0 && factor.points < 15;
          const isZero = factor.points === 0;

          return (
            <div key={index} className="py-3 first:pt-1 last:pb-1 flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-800">{factor.name}</span>
                  {isHigh && (
                    <span className="text-[10px] font-bold px-1.5 py-0.2 bg-rose-100 text-rose-700 rounded">
                      High Impact
                    </span>
                  )}
                  {isMedium && (
                    <span className="text-[10px] font-bold px-1.5 py-0.2 bg-amber-100 text-amber-700 rounded">
                      Moderate
                    </span>
                  )}
                  {isZero && (
                    <span className="text-[10px] font-semibold px-1.5 py-0.2 bg-slate-100 text-slate-600 rounded">
                      Neutral
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-600 mt-1 leading-normal">
                  {factor.reason}
                </p>
              </div>

              <div className="text-right flex-shrink-0">
                <span className={`text-sm font-black ${
                  isHigh ? 'text-rose-600' : isMedium ? 'text-amber-600' : 'text-slate-400'
                }`}>
                  +{factor.points}
                </span>
                <span className="text-[10px] text-slate-400 block font-medium">pts</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
