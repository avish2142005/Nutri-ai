import React from 'react';
import { Thermometer, Droplets, CloudRain, Wind, Calendar } from 'lucide-react';

export default function WeatherCard({ weather, forecast = [], locationName = "Udupi, Karnataka" }) {
  if (!weather) {
    return (
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm animate-pulse">
        <div className="h-6 bg-slate-200 rounded w-1/3 mb-4"></div>
        <div className="grid grid-cols-3 gap-3">
          <div className="h-16 bg-slate-100 rounded-xl"></div>
          <div className="h-16 bg-slate-100 rounded-xl"></div>
          <div className="h-16 bg-slate-100 rounded-xl"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="text-xs font-semibold tracking-wider text-emerald-700 uppercase">Live Weather Intel</span>
          <h3 className="text-base font-bold text-slate-800">{locationName}</h3>
        </div>
        <div className="text-right">
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">
            Source: {weather.source || 'Open-Meteo'}
          </span>
        </div>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-3 gap-3">
        {/* Temperature */}
        <div className="bg-amber-50/60 border border-amber-100/80 rounded-xl p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between text-amber-700">
            <span className="text-xs font-medium">Temp</span>
            <Thermometer className="w-4 h-4" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-extrabold text-amber-900">{weather.temperature_c}°</span>
            <span className="text-xs text-amber-700 ml-0.5">C</span>
          </div>
        </div>

        {/* Humidity */}
        <div className="bg-blue-50/60 border border-blue-100/80 rounded-xl p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between text-blue-700">
            <span className="text-xs font-medium">Humidity</span>
            <Droplets className="w-4 h-4" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-extrabold text-blue-900">{weather.humidity_pct}</span>
            <span className="text-xs text-blue-700 ml-0.5">%</span>
          </div>
        </div>

        {/* Rain Probability */}
        <div className="bg-indigo-50/60 border border-indigo-100/80 rounded-xl p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between text-indigo-700">
            <span className="text-xs font-medium">Rain Prob</span>
            <CloudRain className="w-4 h-4" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-extrabold text-indigo-900">{weather.rain_probability_pct}</span>
            <span className="text-xs text-indigo-700 ml-0.5">%</span>
          </div>
        </div>
      </div>

      {/* Precipitation 24h note */}
      {weather.precipitation_mm_24h > 0 && (
        <div className="mt-3 text-xs text-indigo-800 bg-indigo-50/80 px-3 py-1.5 rounded-lg flex items-center gap-1.5">
          <CloudRain className="w-3.5 h-3.5 flex-shrink-0" />
          <span>Expected 24h Rainfall: <strong>{weather.precipitation_mm_24h} mm</strong></span>
        </div>
      )}

      {/* 3-Day Forecast mini strip if available */}
      {forecast && forecast.length > 0 && (
        <div className="mt-4 pt-3 border-t border-slate-100">
          <div className="flex items-center gap-1 text-xs font-semibold text-slate-500 mb-2">
            <Calendar className="w-3.5 h-3.5" />
            <span>3-Day Outlook</span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {forecast.slice(0, 3).map((day, idx) => (
              <div key={idx} className="bg-slate-50 rounded-lg p-2 text-center text-xs">
                <span className="text-[10px] text-slate-400 block font-medium">
                  {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
                </span>
                <span className="font-bold text-slate-700 block mt-0.5">
                  {Math.round(day.temperature_max_c)}° / {Math.round(day.temperature_min_c)}°
                </span>
                <span className="text-[10px] text-blue-600 font-semibold block mt-0.5">
                  {Math.round(day.precipitation_probability_max)}% rain
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
