import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  AlertCircle,
  RefreshCw,
  CheckCircle,
  Leaf,
  Layers,
  Cpu,
  Globe2,
  ShieldCheck,
  X
} from 'lucide-react';
import { api } from '../api/client';
import ImageUpload from '../components/ImageUpload';
import WeatherCard from '../components/WeatherCard';
import RiskBadge from '../components/RiskBadge';
import RiskBreakdown from '../components/RiskBreakdown';
import RecommendationList from '../components/RecommendationList';
import IrrigationCard from '../components/IrrigationCard';
import SeverityGauge from '../components/SeverityGauge';
import ChatPanel from '../components/ChatPanel';
import LiveCameraScanner from '../components/LiveCameraScanner';

const SUPPORTED_CROPS = [
  { id: 'Tomato', name: 'Tomato (Solanum lycopersicum)' },
  { id: 'Potato', name: 'Potato (Solanum tuberosum)' },
  { id: 'Apple', name: 'Apple (Malus domestica)' },
  { id: 'Corn', name: 'Corn / Maize (Zea mays)' },
  { id: 'Rice', name: 'Rice / Paddy (Oryza sativa)' },
  { id: 'Grape', name: 'Grape (Vitis vinifera)' },
  { id: 'Pepper', name: 'Bell Pepper (Capsicum annuum)' },
  { id: 'Cotton', name: 'Cotton (Gossypium hirsutum)' },
  { id: 'Wheat', name: 'Wheat (Triticum aestivum)' },
  { id: 'Banana', name: 'Banana (Musa acuminata)' },
  { id: 'Brinjal', name: 'Brinjal / Eggplant (Solanum melongena)' },
  { id: 'Chilli', name: 'Chilli (Capsicum frutescens)' }
];

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'kn', label: 'ಕನ್ನಡ (Kannada)' },
  { code: 'tcy', label: 'ತುಳು (Tulu - ಕನ್ನಡ)' },
  { code: 'hi', label: 'हिन्दी (Hindi)' },
  { code: 'pa', label: 'ਪੰਜਾਬੀ (Punjabi)' },
  { code: 'te', label: 'తెలుగు (Telugu)' },
  { code: 'ta', label: 'தமிழ் (Tamil)' },
  { code: 'mr', label: 'मराठी (Marathi)' }
];

export default function Dashboard() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedCrop, setSelectedCrop] = useState('Tomato');
  const [selectedLang, setSelectedLang] = useState('en');
  const [cameraScannerOpen, setCameraScannerOpen] = useState(false);
  const [lat, setLat] = useState(13.3409);
  const [lon, setLon] = useState(74.7421);

  // Weather state
  const [weatherData, setWeatherData] = useState(null);
  const [forecastData, setForecastData] = useState([]);
  const [weatherLoading, setWeatherLoading] = useState(true);

  // Analysis state
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [warnings, setWarnings] = useState([]);

  // Fetch initial live weather
  useEffect(() => {
    async function loadWeather() {
      setWeatherLoading(true);
      try {
        const res = await api.getWeather(lat, lon);
        setWeatherData(res.current);
        setForecastData(res.forecast);
        if (res.warnings && res.warnings.length > 0) {
          setWarnings((prev) => [...prev, ...res.warnings]);
        }
      } catch (err) {
        console.error('Failed to fetch initial weather:', err);
      } finally {
        setWeatherLoading(false);
      }
    }
    loadWeather();
  }, [lat, lon]);

  const handleAnalyze = async () => {
    if (!selectedImage || !selectedImage.file) {
      setErrorMsg('Please select or upload a crop leaf image first.');
      return;
    }

    setErrorMsg('');
    setAnalyzing(true);

    const formData = new FormData();
    formData.append('image', selectedImage.file);
    formData.append('crop', selectedCrop);
    formData.append('architecture', 'efficientnet_b3');
    formData.append('lat', String(lat));
    formData.append('lon', String(lon));

    try {
      const res = await api.analyzeCrop(formData);
      setAnalysisResult(res);
      if (res.weather) setWeatherData(res.weather);
      if (res.warnings && res.warnings.length > 0) {
        setWarnings(res.warnings);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to analyze crop image.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleCameraCaptureComplete = ({ file, previewUrl, name, result }) => {
    setSelectedImage({ file, previewUrl, name });
    if (result) {
      setAnalysisResult(result);
      if (result.weather) setWeatherData(result.weather);
      if (result.warnings && result.warnings.length > 0) {
        setWarnings(result.warnings);
      }
    }
  };

  const dismissWarning = (idx) => {
    setWarnings((prev) => prev.filter((_, i) => i !== idx));
  };

  const getConditionTypeBadge = (type) => {
    switch (type) {
      case 'bacterial':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-50 text-purple-700 border border-purple-200">Bacterial Infection</span>;
      case 'viral':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">Viral Pathogen</span>;
      case 'nutrient':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-orange-50 text-orange-700 border border-orange-200">Nutrient Deficiency</span>;
      case 'healthy':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Healthy Foliage</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">Fungal Pathogen</span>;
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Farm & Deep Learning Model Context Bar */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-700 font-bold">
            <Leaf className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-slate-800">KrishiNetra Crop Health Station</h2>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold border border-emerald-200">
                12 Supported Crops
              </span>
            </div>
            <p className="text-xs text-slate-500">Live AI Diagnostics • Weather-Fused Risk • Multilingual Advisory</p>
          </div>
        </div>

        {/* Controls: Target Crop & Advisory Language */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* Target Crop */}
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600">
            <span>Crop:</span>
            <select
              value={selectedCrop}
              onChange={(e) => setSelectedCrop(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-slate-800 font-bold focus:outline-hidden focus:ring-2 focus:ring-emerald-500/20"
            >
              {SUPPORTED_CROPS.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Language Selector */}
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600">
            <Globe2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Language:</span>
            <select
              value={selectedLang}
              onChange={(e) => setSelectedLang(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-slate-800 font-bold focus:outline-hidden focus:ring-2 focus:ring-emerald-500/20"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Warnings Banner */}
      {warnings.length > 0 && (
        <div className="space-y-2">
          {warnings.map((warn, i) => (
            <div
              key={i}
              className="bg-amber-50 border border-amber-200 text-amber-900 px-4 py-2.5 rounded-xl text-xs flex items-center justify-between gap-2 shadow-sm"
            >
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                <span>{warn}</span>
              </div>
              <button
                onClick={() => dismissWarning(i)}
                className="text-amber-700 hover:text-amber-900 p-1"
                title="Dismiss warning"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Main Grid: Upload & Weather Column + Results Column */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Upload & Live Weather */}
        <div className="lg:col-span-5 space-y-6">
          {/* Upload Card */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
            <div>
              <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider">Step 1</span>
              <h3 className="text-base font-bold text-slate-800">Crop Leaf Inspection</h3>
            </div>

            <ImageUpload
              selectedImage={selectedImage}
              onImageSelected={setSelectedImage}
              disabled={analyzing}
              onOpenLiveCamera={() => setCameraScannerOpen(true)}
            />

            {errorMsg && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <button
              type="button"
              onClick={handleAnalyze}
              disabled={analyzing || !selectedImage}
              className={`w-full py-3.5 px-4 rounded-xl font-bold text-sm text-white flex items-center justify-center gap-2 transition-all shadow-md ${
                analyzing || !selectedImage
                  ? 'bg-slate-300 cursor-not-allowed shadow-none'
                  : 'bg-emerald-600 hover:bg-emerald-700 active:scale-[0.99] shadow-emerald-600/20'
              }`}
            >
              {analyzing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Analyzing Crop Leaf...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Run KrishiNetra Diagnosis</span>
                </>
              )}
            </button>
          </div>

          {/* Weather Card */}
          <WeatherCard
            weather={weatherData}
            forecast={forecastData}
            locationName="Udupi, Karnataka"
          />

          {/* Irrigation Card */}
          <IrrigationCard
            lat={lat}
            lon={lon}
            crop={selectedCrop}
          />
        </div>

        {/* Right Column: Analysis Results or Empty Placeholder */}
        <div className="lg:col-span-7 space-y-6">
          {analysisResult ? (
            <div className="space-y-6 animate-fadeIn">
              {/* Diagnosis Summary Card */}
              <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100 flex-wrap gap-2">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider">
                        {analysisResult.crop} Diagnosis
                      </span>
                      {getConditionTypeBadge(analysisResult.disease.condition_type)}
                    </div>
                    <h3 className="text-2xl font-black text-slate-900">
                      {analysisResult.disease.label}
                    </h3>
                  </div>

                  <div className="text-right">
                    <span className="text-xs text-slate-400 block font-medium">Confidence Score</span>
                    <span className="text-xl font-black text-emerald-600">
                      {(analysisResult.disease.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Plain-Language Explanation */}
                <div className="mt-3.5 p-3.5 rounded-xl bg-slate-50 border border-slate-200/60">
                  <p className="text-xs text-slate-700 font-medium leading-relaxed">
                    {analysisResult.explanation}
                  </p>
                </div>

                {/* Multilingual Farmer Audio/Text Advisory Box */}
                {analysisResult.multilingual_summary && (
                  <div className="mt-4 p-4 rounded-xl bg-emerald-50/70 border border-emerald-200/80 space-y-2">
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-800">
                        <Globe2 className="w-4 h-4 text-emerald-600" />
                        <span>Localized Farmer Advisory</span>
                      </div>
                      <div className="flex gap-1">
                        {LANGUAGES.map((lang) => (
                          <button
                            key={lang.code}
                            type="button"
                            onClick={() => setSelectedLang(lang.code)}
                            className={`px-2 py-0.5 rounded text-[11px] font-bold transition-all ${
                              selectedLang === lang.code
                                ? 'bg-emerald-700 text-white shadow-xs'
                                : 'bg-white text-emerald-700 hover:bg-emerald-100 border border-emerald-200'
                            }`}
                          >
                            {lang.label.split(' ')[0]}
                          </button>
                        ))}
                      </div>
                    </div>
                    <p className="text-xs font-semibold text-slate-800 leading-relaxed">
                      {analysisResult.multilingual_summary[selectedLang] ||
                        analysisResult.multilingual_summary['en']}
                    </p>
                  </div>
                )}

                {/* Top-K Predictions */}
                {analysisResult.disease.top_k && analysisResult.disease.top_k.length > 1 && (
                  <div className="mt-3 pt-3 border-t border-slate-100">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                      Differential Diagnoses (Top-3 Model Ranking)
                    </span>
                    <div className="space-y-1.5">
                      {analysisResult.disease.top_k.map((top, idx) => (
                        <div key={idx} className="flex items-center justify-between text-xs">
                          <span className="text-slate-600 font-medium">{top.label}</span>
                          <span className="text-slate-900 font-bold">{(top.confidence * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Disease Severity Estimation Component */}
              <SeverityGauge
                severity={analysisResult.disease.severity}
                originalImageUrl={selectedImage?.previewUrl}
              />

              {/* Risk Score & Explainable Breakdown */}
              <div className="grid grid-cols-1 gap-6">
                <RiskBadge
                  level={analysisResult.risk.level}
                  score={analysisResult.risk.score}
                />
                <RiskBreakdown
                  factors={analysisResult.risk.factors}
                />
              </div>

              {/* IPM Recommendations */}
              <RecommendationList
                recommendations={analysisResult.recommendations}
              />
            </div>
          ) : (
            /* Empty State Placeholder */
            <div className="bg-white rounded-2xl p-10 border border-slate-200 shadow-sm text-center flex flex-col items-center justify-center min-h-[420px]">
              <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4 shadow-inner">
                <Leaf className="w-8 h-8" />
              </div>
              <h3 className="text-base font-bold text-slate-800">
                KrishiNetra Diagnostic Engine Ready
              </h3>
              <p className="text-xs text-slate-500 max-w-sm mt-1.5 leading-relaxed">
                Upload or select a leaf photo on the left and tap <strong>Run KrishiNetra Diagnosis</strong> to receive instant disease diagnosis, severity quantification, local weather risk evaluation, and sustainable IPM recommendations.
              </p>
              <div className="mt-6 flex items-center gap-4 text-xs text-slate-400 font-medium flex-wrap justify-center">
                <span className="flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5 text-emerald-500" /> 12 Crops Supported</span>
                <span className="flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5 text-emerald-500" /> Multispectral AI Diagnosis</span>
                <span className="flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5 text-emerald-500" /> Severity Quantification</span>
                <span className="flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5 text-emerald-500" /> Multilingual Advisory</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Fullscreen Mobile Live Camera Scanner */}
      <LiveCameraScanner
        isOpen={cameraScannerOpen}
        onClose={() => setCameraScannerOpen(false)}
        onCaptureComplete={handleCameraCaptureComplete}
        preferredLanguage={selectedLang}
      />
    </div>
  );
}
