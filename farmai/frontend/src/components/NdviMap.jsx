import React, { useState, useEffect, useRef } from 'react';
import { 
  Layers, 
  MapPin, 
  Sliders, 
  AlertTriangle, 
  RefreshCw, 
  CheckCircle2, 
  Satellite, 
  Eye, 
  EyeOff, 
  Compass, 
  Calendar, 
  ShieldCheck, 
  TrendingUp, 
  Sprout,
  Activity
} from 'lucide-react';
import L from 'leaflet';
import { api } from '../api/client';

export default function NdviMap({ 
  lat = 13.3409, 
  lon = 74.7421, 
  onLocationChange 
}) {
  const [ndviData, setNdviData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [opacity, setOpacity] = useState(0.75);
  const [showNdviOverlay, setShowNdviOverlay] = useState(true);
  const [baseMapType, setBaseMapType] = useState('satellite'); // 'satellite' | 'carto' | 'osm'

  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const tileLayerRef = useRef(null);
  const labelLayerRef = useRef(null);
  const imageOverlayRef = useRef(null);
  const rectangleRef = useRef(null);
  const markerRef = useRef(null);

  // Fetch Sentinel-2 NDVI data from API
  const loadNdvi = async (targetLat, targetLon) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getSatelliteNdvi(targetLat, targetLon, 1000, 30);
      setNdviData(res);
    } catch (err) {
      console.error("Failed to load Sentinel-2 NDVI map:", err);
      setError(err.message || "Failed to fetch satellite imagery.");
    } finally {
      setLoading(false);
    }
  };

  // Initial data load and coordinate change
  useEffect(() => {
    loadNdvi(lat, lon);
  }, [lat, lon]);

  // Initialize Vanilla Leaflet Map
  useEffect(() => {
    let map = null;

    const initMap = () => {
      if (!mapContainerRef.current) return;
      if (mapInstanceRef.current) return;

      try {
        map = L.map(mapContainerRef.current, {
          center: [lat, lon],
          zoom: 15,
          scrollWheelZoom: true,
          attributionControl: true
        });

        // High-resolution Esri World Imagery Satellite TileLayer
        const satLayer = L.tileLayer(
          'https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
          {
            attribution: 'Tiles &copy; Esri',
            maxZoom: 19
          }
        ).addTo(map);

        // Place labels
        const labels = L.tileLayer(
          'https://services.arcgisonline.com/arcgis/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
          { maxZoom: 19, opacity: 0.75 }
        ).addTo(map);

        tileLayerRef.current = satLayer;
        labelLayerRef.current = labels;

        map.on('click', (e) => {
          if (onLocationChange) {
            onLocationChange(e.latlng.lat, e.latlng.lng);
          } else {
            loadNdvi(e.latlng.lat, e.latlng.lng);
          }
        });

        mapInstanceRef.current = map;
        map.invalidateSize();
      } catch (err) {
        console.error("Leaflet initialization error:", err);
      }
    };

    const rafId = requestAnimationFrame(initMap);
    const timer = setTimeout(initMap, 50);

    return () => {
      cancelAnimationFrame(rafId);
      clearTimeout(timer);
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.remove();
        } catch (_) {}
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Sync Map center when lat/lon change
  useEffect(() => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([lat, lon], mapInstanceRef.current.getZoom(), { duration: 0.8 });
      setTimeout(() => {
        if (mapInstanceRef.current) mapInstanceRef.current.invalidateSize();
      }, 200);
    }
  }, [lat, lon]);

  // Switch BaseMap Layers
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (tileLayerRef.current) {
      map.removeLayer(tileLayerRef.current);
      tileLayerRef.current = null;
    }
    if (labelLayerRef.current) {
      map.removeLayer(labelLayerRef.current);
      labelLayerRef.current = null;
    }

    if (baseMapType === 'satellite') {
      tileLayerRef.current = L.tileLayer(
        'https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        { attribution: 'Tiles &copy; Esri', maxZoom: 19 }
      ).addTo(map);

      labelLayerRef.current = L.tileLayer(
        'https://services.arcgisonline.com/arcgis/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 19, opacity: 0.65 }
      ).addTo(map);
    } else if (baseMapType === 'carto') {
      tileLayerRef.current = L.tileLayer(
        'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
        { attribution: '&copy; CARTO', maxZoom: 19 }
      ).addTo(map);
    } else if (baseMapType === 'osm') {
      tileLayerRef.current = L.tileLayer(
        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        { attribution: '&copy; OpenStreetMap contributors', maxZoom: 19 }
      ).addTo(map);
    }
  }, [baseMapType]);

  // Update NDVI Overlay and Bounds
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Clean previous overlay
    if (imageOverlayRef.current) {
      map.removeLayer(imageOverlayRef.current);
      imageOverlayRef.current = null;
    }
    if (rectangleRef.current) {
      map.removeLayer(rectangleRef.current);
      rectangleRef.current = null;
    }

    if (showNdviOverlay && ndviData?.overlay_png_base64 && ndviData?.bbox) {
      const bounds = [
        [ndviData.bbox[1], ndviData.bbox[0]],
        [ndviData.bbox[3], ndviData.bbox[2]]
      ];

      imageOverlayRef.current = L.imageOverlay(ndviData.overlay_png_base64, bounds, {
        opacity: opacity,
        zIndex: 400
      }).addTo(map);

      rectangleRef.current = L.rectangle(bounds, {
        color: '#22c55e',
        weight: 2,
        dashArray: '5, 5',
        fill: false
      }).addTo(map);
    }
  }, [ndviData, showNdviOverlay, opacity]);

  // Update Field Pin Marker
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (markerRef.current) {
      map.removeLayer(markerRef.current);
      markerRef.current = null;
    }

    const pinIcon = L.divIcon({
      className: 'custom-field-pin',
      html: `
        <div style="position: relative; width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;">
          <span style="position: absolute; width: 100%; height: 100%; border-radius: 50%; background: rgba(34, 197, 94, 0.4); animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></span>
          <div style="width: 26px; height: 26px; border-radius: 50%; background: #15803d; border: 2.5px solid #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; color: white;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="m12 8 v8"/><path d="m8 12 h8"/></svg>
          </div>
        </div>
      `,
      iconSize: [34, 34],
      iconAnchor: [17, 17],
    });

    markerRef.current = L.marker([lat, lon], { icon: pinIcon })
      .addTo(map)
      .bindPopup(`
        <div style="padding: 4px; font-family: sans-serif; font-size: 12px;">
          <div style="font-weight: bold; color: #0f172a; margin-bottom: 2px;">Selected Field Center</div>
          <div style="color: #64748b; font-family: monospace;">${lat.toFixed(4)}° N, ${lon.toFixed(4)}° E</div>
        </div>
      `);
  }, [lat, lon]);

  // Biomass Status Helper
  const getBiomassStatus = (mean) => {
    if (mean >= 0.65) return { label: 'Optimal Biomass Canopy', color: 'text-emerald-700 bg-emerald-50 border-emerald-200' };
    if (mean >= 0.50) return { label: 'Healthy Vegetative Growth', color: 'text-green-700 bg-green-50 border-green-200' };
    if (mean >= 0.35) return { label: 'Moderate Canopy Density', color: 'text-amber-700 bg-amber-50 border-amber-200' };
    return { label: 'Vegetation / Water Stress Detected', color: 'text-rose-700 bg-rose-50 border-rose-200' };
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Top Header & Telemetry Bar */}
      <div className="p-4 sm:p-5 border-b border-slate-100 flex items-center justify-between flex-wrap gap-3 bg-gradient-to-r from-slate-900 to-slate-800 text-white">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
            <Satellite className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
                Copernicus Sentinel-2 MSI
              </span>
              <span className="text-[10px] bg-slate-700/80 px-2 py-0.5 rounded text-slate-300 font-mono">
                10m GSD Resolution
              </span>
            </div>
            <h3 className="text-base sm:text-lg font-bold text-white flex items-center gap-1.5">
              High-Resolution Satellite Field Monitoring (NDVI)
            </h3>
          </div>
        </div>

        {/* Action badges */}
        <div className="flex items-center gap-2">
          {loading && (
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-950/60 border border-emerald-800/80 px-3 py-1 rounded-full">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Fetching Tiles...</span>
            </div>
          )}
          <button
            onClick={() => loadNdvi(lat, lon)}
            className="flex items-center gap-1.5 text-xs font-semibold bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-lg text-slate-200 transition-colors"
            title="Refresh satellite data"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Main Map & Metrics Area */}
      <div className="p-4 sm:p-6">
        {/* Metric summary banner */}
        {ndviData && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-center">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Mean NDVI</span>
              <div className="flex items-center justify-center gap-1 mt-0.5">
                <span className="text-2xl font-black text-slate-900">{ndviData.mean_ndvi.toFixed(2)}</span>
                <span className="text-[11px] font-bold text-slate-500">/ 1.0</span>
              </div>
              <span className={`text-[10px] font-bold px-2 py-0.5 mt-1 inline-block rounded-full border ${getBiomassStatus(ndviData.mean_ndvi).color}`}>
                {getBiomassStatus(ndviData.mean_ndvi).label}
              </span>
            </div>

            <div className="bg-emerald-50 border border-emerald-200/80 rounded-xl p-3 text-center">
              <span className="text-[10px] uppercase font-bold text-emerald-700 block tracking-wider">% Healthy Canopy</span>
              <span className="text-2xl font-black text-emerald-800 block mt-0.5">{ndviData.health_class_pct.healthy}%</span>
              <span className="text-[10px] font-medium text-emerald-600 block mt-1">NDVI &gt; 0.55</span>
            </div>

            <div className="bg-rose-50 border border-rose-200/80 rounded-xl p-3 text-center">
              <span className="text-[10px] uppercase font-bold text-rose-700 block tracking-wider">% Stressed Area</span>
              <span className="text-2xl font-black text-rose-800 block mt-0.5">{ndviData.health_class_pct.stressed}%</span>
              <span className="text-[10px] font-medium text-rose-600 block mt-1">NDVI 0.15 - 0.35</span>
            </div>

            <div className="bg-amber-50 border border-amber-200/80 rounded-xl p-3 text-center">
              <span className="text-[10px] uppercase font-bold text-amber-700 block tracking-wider">% Moderate Canopy</span>
              <span className="text-2xl font-black text-amber-800 block mt-0.5">{ndviData.health_class_pct.moderate}%</span>
              <span className="text-[10px] font-medium text-amber-600 block mt-1">NDVI 0.35 - 0.55</span>
            </div>
          </div>
        )}

        {/* Map Control Toolbar */}
        <div className="mb-3 flex items-center justify-between flex-wrap gap-2 text-xs">
          {/* Layer and Overlay Toggles */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-slate-500 font-semibold">Basemap:</span>
            <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-50">
              <button
                type="button"
                onClick={() => setBaseMapType('satellite')}
                className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                  baseMapType === 'satellite'
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                🛰️ Esri Satellite
              </button>
              <button
                type="button"
                onClick={() => setBaseMapType('carto')}
                className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                  baseMapType === 'carto'
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                🗺️ Detailed Map
              </button>
              <button
                type="button"
                onClick={() => setBaseMapType('osm')}
                className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                  baseMapType === 'osm'
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                🌍 OpenStreetMap
              </button>
            </div>

            <div className="h-4 w-[1px] bg-slate-200 mx-1 hidden sm:block"></div>

            <button
              type="button"
              onClick={() => setShowNdviOverlay(!showNdviOverlay)}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg border font-semibold transition-all ${
                showNdviOverlay
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                  : 'bg-slate-100 text-slate-500 border-slate-300 hover:text-slate-800'
              }`}
            >
              {showNdviOverlay ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
              <span>NDVI Heatmap Overlay</span>
            </button>
          </div>

          {/* Opacity Slider */}
          {showNdviOverlay && (
            <div className="flex items-center gap-2 text-xs text-slate-600 bg-slate-50 border border-slate-200 px-3 py-1 rounded-lg">
              <Sliders className="w-3.5 h-3.5 text-slate-400" />
              <span>Opacity:</span>
              <input
                type="range"
                min="0.2"
                max="1.0"
                step="0.05"
                value={opacity}
                onChange={(e) => setOpacity(parseFloat(e.target.value))}
                className="accent-emerald-600 cursor-pointer w-20 h-1.5 bg-slate-200 rounded"
              />
              <span className="font-mono text-[11px] font-bold text-slate-700 w-8 text-right">
                {Math.round(opacity * 100)}%
              </span>
            </div>
          )}
        </div>

        {/* Live Interactive Leaflet Map Container */}
        <div className="relative rounded-2xl overflow-hidden border border-slate-300 shadow-inner h-[500px] w-full bg-slate-900">
          <div
            ref={mapContainerRef}
            className="w-full h-full"
            style={{ width: '100%', height: '500px', minHeight: '500px' }}
          />

          {/* Floating Map HUD Banner */}
          <div className="absolute top-3 left-3 z-[1000] bg-slate-900/80 backdrop-blur-md border border-slate-700/80 px-3.5 py-2 rounded-xl text-white shadow-lg pointer-events-none">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              <span className="text-xs font-bold">Field: {lat.toFixed(4)}° N, {lon.toFixed(4)}° E</span>
            </div>
            <span className="text-[10px] text-slate-300 block mt-0.5">
              1,000m × 1,000m Sentinel-2 Field Parcel • Click map to re-target
            </span>
          </div>

          {/* Interactive Click-to-Target Hint */}
          <div className="absolute bottom-3 right-3 z-[1000] bg-white/90 backdrop-blur-sm border border-slate-200 px-3 py-1.5 rounded-lg shadow text-[11px] text-slate-600 flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5 text-emerald-600" />
            <span>Click any location to inspect field NDVI</span>
          </div>
        </div>

        {/* Continuous Color Legend & Spectral Scale */}
        <div className="mt-4 p-3 bg-slate-50 border border-slate-200 rounded-xl">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-700 mb-2">
            <span>NDVI Vegetation Index Spectrum</span>
            <span className="font-mono text-[11px] text-slate-500">Formula: (NIR - Red) / (NIR + Red)</span>
          </div>

          {/* Continuous Color Gradient Bar */}
          <div className="h-3.5 rounded-full overflow-hidden shadow-inner" style={{
            background: 'linear-gradient(to right, #8B4513 0%, #ef4444 20%, #eab308 45%, #22c55e 70%, #15803d 100%)'
          }}></div>

          {/* Scale Labels */}
          <div className="flex justify-between items-center text-[10px] font-bold text-slate-500 mt-1.5 px-0.5">
            <span>-0.1 (Water / Bare)</span>
            <span>0.2 (Severe Stress)</span>
            <span>0.4 (Moderate Vigor)</span>
            <span>0.6 (Healthy Canopy)</span>
            <span>0.88+ (Dense Biomass)</span>
          </div>
        </div>

        {/* Sentinel-2 Satellite Metadata & Precision Agronomy Advisory */}
        {ndviData && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            {/* Direct High-Resolution NDVI Sensor Raster Tile */}
            {ndviData.overlay_png_base64 && (
              <div className="p-3.5 rounded-xl border border-slate-200 bg-white flex flex-col items-center justify-center text-center">
                <div className="flex items-center gap-1.5 font-bold text-slate-800 mb-2 self-start">
                  <Activity className="w-4 h-4 text-emerald-600" />
                  <span>Sentinel-2 L2A Calibrated NDVI Raster</span>
                </div>
                <div className="relative w-48 h-48 rounded-xl overflow-hidden border border-slate-300 shadow-md bg-slate-950 p-1 flex items-center justify-center">
                  <img
                    src={ndviData.overlay_png_base64}
                    alt="Sentinel-2 NDVI Raster"
                    className="w-full h-full object-cover rounded-lg"
                  />
                  <span className="absolute bottom-2 right-2 text-[9px] bg-slate-900/80 text-emerald-400 font-mono px-1.5 py-0.5 rounded border border-slate-700">
                    256 × 256 BOA
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 mt-2">
                  Multispectral Index: (Band 8 - Band 4) / (Band 8 + Band 4)
                </span>
              </div>
            )}

            {/* Mission Telemetry */}
            <div className={`p-3.5 rounded-xl border border-slate-200 bg-white ${!ndviData.overlay_png_base64 ? 'md:col-span-1' : ''}`}>
              <h4 className="font-bold text-slate-800 flex items-center gap-1.5 mb-2">
                <Satellite className="w-4 h-4 text-emerald-600" />
                Copernicus Sentinel-2 Mission Telemetry
              </h4>
              <ul className="space-y-1.5 text-slate-600 text-[11px]">
                <li className="flex justify-between border-b border-slate-100 pb-1">
                  <span>Spectral Bands Used:</span>
                  <span className="font-semibold text-slate-800">B4 (Red 665nm) & B8 (NIR 842nm)</span>
                </li>
                <li className="flex justify-between border-b border-slate-100 pb-1">
                  <span>Calibration Level:</span>
                  <span className="font-semibold text-slate-800">L2A Bottom-Of-Atmosphere (BOA)</span>
                </li>
                <li className="flex justify-between border-b border-slate-100 pb-1">
                  <span>Ground Sampling Distance:</span>
                  <span className="font-semibold text-slate-800">10m / pixel</span>
                </li>
                <li className="flex justify-between border-b border-slate-100 pb-1">
                  <span>Cloud Aperture Clearance:</span>
                  <span className="font-semibold text-emerald-600">{100 - ndviData.cloud_cover_pct}% Clear Sky</span>
                </li>
                <li className="flex justify-between">
                  <span>Acquisition Date:</span>
                  <span className="font-semibold text-slate-800">{ndviData.acquired_on}</span>
                </li>
              </ul>
            </div>

            {/* Precision Agronomic Action Plan */}
            <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/50">
              <h4 className="font-bold text-emerald-900 flex items-center gap-1.5 mb-2">
                <Sprout className="w-4 h-4 text-emerald-700" />
                Satellite Precision Agronomy Advisory
              </h4>
              <div className="space-y-2 text-[11px] text-emerald-950">
                {ndviData.health_class_pct.stressed > 15 ? (
                  <p className="flex items-start gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
                    <span><strong>High Stress Alert:</strong> {ndviData.health_class_pct.stressed}% of the parcel displays acute foliar or water deficit. Perform on-foot ground scouting in the red zones to inspect for fungal blight or drip emitter clogging.</span>
                  </p>
                ) : (
                  <p className="flex items-start gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                    <span><strong>Optimal Vegetative Vigor:</strong> {ndviData.health_class_pct.healthy}% of canopy maintains strong chlorophyll absorption and photosynthetic activity. Maintain standard irrigation intervals.</span>
                  </p>
                )}
                <p className="text-slate-600 pt-1 border-t border-emerald-200/60">
                  <strong>Variable-Rate Fertilization:</strong> Target nitrogen top-dressing to the yellow/amber parcels (NDVI 0.35–0.50) to uniformize canopy maturity.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}