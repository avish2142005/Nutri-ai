import React, { useState, useEffect } from 'react';
import { Droplet, AlertCircle, CheckCircle2, RotateCw } from 'lucide-react';
import { api } from '../api/client';

export default function IrrigationCard({ lat = 13.3409, lon = 74.7421, crop = "Tomato" }) {
  const [soilMoisture, setSoilMoisture] = useState(42);
  const [advisory, setAdvisory] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchAdvisory = async (moisture) => {
    setLoading(true);
    try {
      const res = await api.getIrrigation(lat, lon, crop, "Vegetative", moisture);
      setAdvisory(res);
    } catch (err) {
      console.error("Irrigation fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdvisory(soilMoisture);
  }, [lat, lon, crop]);

  const handleSliderChange = (e) => {
    const val = Number(e.target.value);
    setSoilMoisture(val);
    fetchAdvisory(val);
  };

  const decisionStyles = {
    IRRIGATE_NOW: {
      badge: 'bg-blue-600 text-white',
      border: 'border-blue-200',
      bg: 'bg-blue-50/50',
      label: 'IRRIGATE NOW',
      color: 'text-blue-800'
    },
    SKIP_TODAY: {
      badge: 'bg-emerald-600 text-white',
      border: 'border-emerald-200',
      bg: 'bg-emerald-50/50',
      label: 'SKIP TODAY',
      color: 'text-emerald-800'
    },
    REDUCE_WATER: {
      badge: 'bg-amber-500 text-white',
      border: 'border-amber-200',
      bg: 'bg-amber-50/50',
      label: 'REDUCE WATER',
      color: 'text-amber-800'
    }
  };

  const style = advisory ? decisionStyles[advisory.decision] || decisionStyles.SKIP_TODAY : decisionStyles.SKIP_TODAY;

  return (
    <div className={`rounded-2xl p-5 border ${style.border} ${style.bg} shadow-sm transition-all`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Droplet className="w-5 h-5 text-blue-600" />
          <h4 className="text-sm font-bold text-slate-800">Smart Irrigation Scheduler</h4>
        </div>
        {advisory && (
          <span className={`text-[11px] font-black px-2.5 py-1 rounded-full ${style.badge}`}>
            {style.label}
          </span>
        )}
      </div>

      {/* Soil moisture slider */}
      <div className="bg-white/80 rounded-xl p-3 border border-slate-200/80 mb-3">
        <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1">
          <span>Field Soil Moisture</span>
          <span className="font-bold text-blue-700">{soilMoisture}%</span>
        </div>
        <input
          type="range"
          min="15"
          max="85"
          value={soilMoisture}
          onChange={handleSliderChange}
          className="w-full accent-blue-600 cursor-pointer h-2 bg-slate-200 rounded-lg"
        />
        <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-medium">
          <span>Dry (15%)</span>
          <span>Optimal (45%)</span>
          <span>Saturated (85%)</span>
        </div>
      </div>

      {/* Reasons list */}
      {advisory && advisory.reasons && (
        <ul className="space-y-1.5 text-xs text-slate-700 font-medium">
          {advisory.reasons.map((r, i) => (
            <li key={i} className="flex items-start gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 mt-0.5 flex-shrink-0" />
              <span>{r}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
