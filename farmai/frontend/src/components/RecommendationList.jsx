import React from 'react';
import { Eye, Scissors, Droplet, Sprout, AlertCircle, CheckCircle } from 'lucide-react';

const CATEGORY_CONFIG = {
  monitoring: {
    label: 'Scouting & Monitoring',
    color: 'bg-sky-50 text-sky-800 border-sky-200',
    badge: 'bg-sky-600 text-white',
    icon: Eye
  },
  cultural: {
    label: 'Cultural & Sanitation',
    color: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    badge: 'bg-emerald-600 text-white',
    icon: Scissors
  },
  water: {
    label: 'Water & Irrigation',
    color: 'bg-cyan-50 text-cyan-800 border-cyan-200',
    badge: 'bg-cyan-600 text-white',
    icon: Droplet
  },
  biological: {
    label: 'Biological & Organic Controls',
    color: 'bg-teal-50 text-teal-800 border-teal-200',
    badge: 'bg-teal-600 text-white',
    icon: Sprout
  },
  'chemical-advisory': {
    label: 'Chemical Advisory (Last Resort)',
    color: 'bg-amber-50 text-amber-900 border-amber-300',
    badge: 'bg-amber-600 text-white',
    icon: AlertCircle
  }
};

export default function RecommendationList({ recommendations = [] }) {
  if (!recommendations || recommendations.length === 0) return null;

  // Group by category while preserving IPM order
  const orderedCategories = ['monitoring', 'cultural', 'water', 'biological', 'chemical-advisory'];
  const grouped = {};
  orderedCategories.forEach(cat => { grouped[cat] = []; });

  recommendations.forEach(item => {
    const cat = item.category || 'monitoring';
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(item);
  });

  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="text-xs font-semibold text-emerald-600 tracking-wider uppercase">Integrated Pest Management</span>
          <h4 className="text-base font-bold text-slate-900">Recommended Action Plan</h4>
        </div>
        <span className="text-xs bg-emerald-50 text-emerald-700 font-bold px-2.5 py-1 rounded-full border border-emerald-200">
          IPM Hierarchical
        </span>
      </div>

      <div className="space-y-4">
        {orderedCategories.map(cat => {
          const items = grouped[cat];
          if (!items || items.length === 0) return null;
          const conf = CATEGORY_CONFIG[cat] || CATEGORY_CONFIG.monitoring;
          const Icon = conf.icon;
          const isChemical = cat === 'chemical-advisory';

          return (
            <div
              key={cat}
              className={`rounded-xl border p-4 ${conf.color} ${isChemical ? 'shadow-sm' : ''}`}
            >
              <div className="flex items-center gap-2 mb-2.5">
                <span className={`p-1.5 rounded-lg ${conf.badge}`}>
                  <Icon className="w-4 h-4" />
                </span>
                <h5 className="text-xs font-bold uppercase tracking-wider">
                  {conf.label}
                </h5>
              </div>

              <ul className="space-y-2">
                {items.map((it, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-xs font-medium leading-relaxed">
                    <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 opacity-70" />
                    <span>{it.action}</span>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}
