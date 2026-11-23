import React, { useState } from 'react';
import { 
  MapPin, 
  Satellite, 
  Navigation, 
  Search, 
  Layers, 
  Activity, 
  HelpCircle, 
  Sparkles, 
  Check, 
  Globe,
  Compass,
  Loader2
} from 'lucide-react';
import NdviMap from '../components/NdviMap';

const PRESET_REGIONS = [
  {
    name: 'Punjab Wheat Belt',
    location: 'Ludhiana, Punjab',
    crop: 'Wheat & Basmati Rice',
    lat: 30.9010,
    lon: 75.8573,
    icon: '🌾',
  },
  {
    name: 'Kolar Solanaceous Basin',
    location: 'Kolar, Karnataka',
    crop: 'Tomato, Chilli & Pepper',
    lat: 13.1367,
    lon: 78.1292,
    icon: '🍅',
  },
  {
    name: 'Nashik Vineyard Valley',
    location: 'Nashik, Maharashtra',
    crop: 'Grape & Onion',
    lat: 19.9975,
    lon: 73.7898,
    icon: '🍇',
  },
  {
    name: 'Warangal Cotton & Corn',
    location: 'Warangal, Telangana',
    crop: 'Cotton & Maize',
    lat: 17.9689,
    lon: 79.5941,
    icon: '🌽',
  },
  {
    name: 'Kashmir Apple Orchards',
    location: 'Sopore, J&K',
    crop: 'Apple',
    lat: 34.2982,
    lon: 74.4690,
    icon: '🍎',
  },
  {
    name: 'Agra Potato Farmland',
    location: 'Agra, Uttar Pradesh',
    crop: 'Potato',
    lat: 27.1767,
    lon: 78.0081,
    icon: '🥔',
  },
  {
    name: 'Coastal Udupi Plantation',
    location: 'Udupi, Karnataka',
    crop: 'Rice & Banana',
    lat: 13.3409,
    lon: 74.7421,
    icon: '🌿',
  },
];

export default function FieldMap() {
  const [lat, setLat] = useState(13.3409);
  const [lon, setLon] = useState(74.7421);
  const [inputLat, setInputLat] = useState('13.3409');
  const [inputLon, setInputLon] = useState('74.7421');
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [locatingGps, setLocatingGps] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [selectedPreset, setSelectedPreset] = useState('Coastal Udupi Plantation');

  const handleApplyCoordinates = (e) => {
    e.preventDefault();
    const parsedLat = parseFloat(inputLat);
    const parsedLon = parseFloat(inputLon);
    if (!isNaN(parsedLat) && !isNaN(parsedLon)) {
      setLat(parsedLat);
      setLon(parsedLon);
      setSelectedPreset('Custom Coordinates');
      setStatusMessage('');
    }
  };

  const handleSelectPreset = (preset) => {
    setLat(preset.lat);
    setLon(preset.lon);
    setInputLat(preset.lat.toString());
    setInputLon(preset.lon.toString());
    setSelectedPreset(preset.name);
    setStatusMessage('');
  };

  const handleMapLocationChange = (newLat, newLon) => {
    setLat(newLat);
    setLon(newLon);
    setInputLat(newLat.toFixed(5));
    setInputLon(newLon.toFixed(5));
    setSelectedPreset('Selected on Map');
  };

  // Live Browser GPS Geolocation
  const handleUseGpsLocation = () => {
    if (!navigator.geolocation) {
      setStatusMessage('Geolocation is not supported by your browser.');
      return;
    }
    setLocatingGps(true);
    setStatusMessage('Acquiring real-time GPS coordinates...');

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const userLat = position.coords.latitude;
        const userLon = position.coords.longitude;
        setLat(userLat);
        setLon(userLon);
        setInputLat(userLat.toFixed(5));
        setInputLon(userLon.toFixed(5));
        setSelectedPreset('My Live GPS Location');
        setStatusMessage(`Acquired GPS: ${userLat.toFixed(4)}°, ${userLon.toFixed(4)}° (accuracy ~${Math.round(position.coords.accuracy || 10)}m)`);
        setLocatingGps(false);
      },
      (err) => {
        console.warn('GPS location lookup failed:', err.message);
        setStatusMessage('GPS permission denied or unavailable. You can search by village/city name.');
        setLocatingGps(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
    );
  };

  // OpenStreetMap Nominatim Geocoder Search
  const handleSearchLocation = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearching(true);
    setStatusMessage(`Searching OpenStreetMap for "${searchQuery}"...`);

    try {
      const endpoint = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&limit=1`;
      const res = await fetch(endpoint, {
        headers: {
          'Accept': 'application/json',
          'User-Agent': 'KrishiNetra-AgriPlatform/1.0'
        }
      });
      const data = await res.json();
      if (data && data.length > 0) {
        const place = data[0];
        const newLat = parseFloat(place.lat);
        const newLon = parseFloat(place.lon);
        setLat(newLat);
        setLon(newLon);
        setInputLat(newLat.toFixed(5));
        setInputLon(newLon.toFixed(5));
        setSelectedPreset(place.display_name.split(',')[0]);
        setStatusMessage(`Located: ${place.display_name}`);
      } else {
        setStatusMessage(`Location "${searchQuery}" not found. Try adding a state or country name.`);
      }
    } catch (err) {
      console.error('Geocoder error:', err);
      setStatusMessage('Failed to connect to geocoding service. Please enter coordinates directly.');
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-emerald-900 via-slate-900 to-slate-900 rounded-2xl p-6 text-white shadow-md border border-emerald-800/30">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase tracking-wider mb-1">
              <Globe className="w-4 h-4" />
              <span>Earth Observation Satellite Intelligence</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-white">
              Sentinel-2 Field Satellite NDVI Observatory
            </h1>
            <p className="text-sm text-slate-300 mt-1 max-w-2xl">
              Track vegetative vigor, detect microclimatic crop stress, and monitor chlorophyll density using real ESA Copernicus Sentinel-2 multispectral satellite telemetry and sub-meter Esri satellite imagery.
            </p>
          </div>

          {/* Location Actions: GPS + Geocoder Search + Lat/Lon */}
          <div className="flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center gap-2 self-start lg:self-auto">
            {/* GPS Button */}
            <button
              type="button"
              onClick={handleUseGpsLocation}
              disabled={locatingGps}
              className="flex items-center justify-center gap-2 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-md transition-all whitespace-nowrap"
              title="Use current GPS location"
            >
              {locatingGps ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Navigation className="w-3.5 h-3.5" />}
              <span>{locatingGps ? 'Locating...' : 'My GPS Location'}</span>
            </button>

            {/* Address / Village Search */}
            <form onSubmit={handleSearchLocation} className="flex items-center gap-1.5 bg-slate-800/90 p-1.5 rounded-xl border border-slate-700">
              <Search className="w-3.5 h-3.5 text-slate-400 ml-2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search village, city, farm..."
                className="bg-transparent text-xs text-white placeholder-slate-400 px-2 py-1 focus:outline-hidden w-36 sm:w-44"
              />
              <button
                type="submit"
                disabled={searching}
                className="px-2.5 py-1 bg-slate-700 hover:bg-slate-600 text-slate-100 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
              >
                {searching ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Find'}
              </button>
            </form>

            {/* Quick Coordinate Direct Box */}
            <form 
              onSubmit={handleApplyCoordinates}
              className="flex items-center gap-2 bg-slate-800/80 p-1.5 rounded-xl border border-slate-700/80"
            >
              <div className="flex items-center gap-1 px-1">
                <span className="text-[11px] font-bold text-slate-400">Lat:</span>
                <input
                  type="text"
                  value={inputLat}
                  onChange={(e) => setInputLat(e.target.value)}
                  className="w-14 sm:w-16 bg-slate-900 border border-slate-700 rounded px-1.5 py-1 text-xs text-white font-mono focus:outline-hidden focus:border-emerald-500"
                  placeholder="Lat"
                />
              </div>
              <div className="flex items-center gap-1 px-1">
                <span className="text-[11px] font-bold text-slate-400">Lon:</span>
                <input
                  type="text"
                  value={inputLon}
                  onChange={(e) => setInputLon(e.target.value)}
                  className="w-14 sm:w-16 bg-slate-900 border border-slate-700 rounded px-1.5 py-1 text-xs text-white font-mono focus:outline-hidden focus:border-emerald-500"
                  placeholder="Lon"
                />
              </div>
              <button
                type="submit"
                className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition-all shadow-xs"
              >
                Go
              </button>
            </form>
          </div>
        </div>

        {/* Live Feedback / Geolocation Status message */}
        {statusMessage && (
          <div className="mt-3 py-1.5 px-3 bg-slate-800/70 rounded-lg border border-slate-700 text-xs text-emerald-300 flex items-center gap-2">
            <Compass className="w-3.5 h-3.5 shrink-0" />
            <span className="truncate">{statusMessage}</span>
          </div>
        )}

        {/* Agricultural Region Quick Selector Pills */}
        <div className="mt-5 pt-4 border-t border-slate-800/80">
          <div className="flex items-center gap-2 mb-2 text-xs text-slate-400 font-semibold">
            <MapPin className="w-3.5 h-3.5 text-emerald-400" />
            <span>Select Indian Agricultural Belt:</span>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin">
            {PRESET_REGIONS.map((preset) => {
              const isSelected = selectedPreset === preset.name;
              return (
                <button
                  key={preset.name}
                  type="button"
                  onClick={() => handleSelectPreset(preset)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all border ${
                    isSelected
                      ? 'bg-emerald-600 text-white border-emerald-500 shadow-sm shadow-emerald-900/30 font-bold'
                      : 'bg-slate-800/60 text-slate-300 border-slate-700 hover:bg-slate-700 hover:text-white'
                  }`}
                >
                  <span>{preset.icon}</span>
                  <span>{preset.name}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${isSelected ? 'bg-emerald-700 text-emerald-100' : 'bg-slate-700 text-slate-300'}`}>
                    {preset.crop}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Interactive Satellite Map Component */}
      <NdviMap 
        lat={lat} 
        lon={lon} 
        onLocationChange={handleMapLocationChange} 
      />

      {/* Educational Guide: How Satellite NDVI Works for Farmers */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center mb-3">
            <Activity className="w-4 h-4" />
          </div>
          <h4 className="text-sm font-bold text-slate-900">How NDVI Detects Foliar Stress</h4>
          <p className="text-xs text-slate-600 mt-1 leading-relaxed">
            Healthy chlorophyll absorbs red light (Band 4) and reflects near-infrared (Band 8). When crops suffer water stress, fungal blight, or nitrogen deficiency, cellular reflectance collapses, showing immediate drops in NDVI.
          </p>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center mb-3">
            <Satellite className="w-4 h-4" />
          </div>
          <h4 className="text-sm font-bold text-slate-900">10-Meter Ground Resolution</h4>
          <p className="text-xs text-slate-600 mt-1 leading-relaxed">
            Sentinel-2 provides 10-meter Ground Sampling Distance (GSD). Each pixel represents a 10m × 10m farm section, enabling precise zonal scouting without walking the entire acreage.
          </p>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center mb-3">
            <Sparkles className="w-4 h-4" />
          </div>
          <h4 className="text-sm font-bold text-slate-900">Precision Variable-Rate Spraying</h4>
          <p className="text-xs text-slate-600 mt-1 leading-relaxed">
            By overlaying the NDVI heatmap on real satellite photography, farmers can target fertilizers and bio-fungicides directly to the stressed zones, reducing chemical usage by 30–40%.
          </p>
        </div>
      </div>
    </div>
  );
}
