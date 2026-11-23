import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Camera, 
  SwitchCamera, 
  Zap, 
  ZapOff, 
  X, 
  Sparkles, 
  Activity, 
  AlertCircle, 
  CheckCircle, 
  RefreshCw, 
  Globe2, 
  Maximize2,
  ChevronRight,
  ShieldAlert,
  Sliders
} from 'lucide-react';
import { api } from '../api/client';

const SUPPORTED_CROPS = [
  { id: 'Tomato', name: 'Tomato' },
  { id: 'Potato', name: 'Potato' },
  { id: 'Apple', name: 'Apple' },
  { id: 'Corn', name: 'Corn / Maize' },
  { id: 'Rice', name: 'Rice / Paddy' },
  { id: 'Grape', name: 'Grape' },
  { id: 'Pepper', name: 'Bell Pepper' },
  { id: 'Cotton', name: 'Cotton' },
  { id: 'Wheat', name: 'Wheat' },
  { id: 'Banana', name: 'Banana' },
  { id: 'Brinjal', name: 'Brinjal' },
  { id: 'Chilli', name: 'Chilli' }
];

export default function LiveCameraScanner({ 
  isOpen, 
  onClose, 
  onCaptureComplete,
  preferredLanguage = 'en'
}) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const autoScanTimerRef = useRef(null);
  const fallbackInputRef = useRef(null);

  const [cameraActive, setCameraActive] = useState(false);
  const [facingMode, setFacingMode] = useState('environment'); // 'environment' (back) or 'user' (front)
  const [torchAvailable, setTorchAvailable] = useState(false);
  const [torchOn, setTorchOn] = useState(false);
  const [cameraError, setCameraError] = useState('');
  
  const [selectedCrop, setSelectedCrop] = useState('Tomato');
  const [isCapturing, setIsCapturing] = useState(false);
  const [autoScanEnabled, setAutoScanEnabled] = useState(false);
  const [lastScanResult, setLastScanResult] = useState(null);
  const [capturedSnapshot, setCapturedSnapshot] = useState(null);
  const [scanningPulse, setScanningPulse] = useState(false);

  // Stop camera stream cleanly
  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch (_) {}
      });
      streamRef.current = null;
    }
    if (autoScanTimerRef.current) {
      clearInterval(autoScanTimerRef.current);
      autoScanTimerRef.current = null;
    }
    setCameraActive(false);
    setTorchOn(false);
  }, []);

  // Start camera stream
  const startStream = useCallback(async (mode = facingMode) => {
    stopStream();
    setCameraError('');

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setCameraError('Camera API is not supported on this browser or device. You can take a photo via gallery or native camera picker.');
      return;
    }

    try {
      const constraints = {
        audio: false,
        video: {
          facingMode: { ideal: mode },
          width: { ideal: 1920, min: 640 },
          height: { ideal: 1080, min: 480 }
        }
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      setCameraActive(true);

      // Check torch capability
      const videoTrack = stream.getVideoTracks()[0];
      if (videoTrack) {
        const capabilities = videoTrack.getCapabilities ? videoTrack.getCapabilities() : {};
        if (capabilities.torch) {
          setTorchAvailable(true);
        } else {
          setTorchAvailable(false);
        }
      }
    } catch (err) {
      console.warn('getUserMedia error:', err);
      let msg = 'Could not access camera. Please allow camera permissions in browser settings.';
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        msg = 'Camera permission denied. Please allow camera access in your mobile browser settings to scan crops live.';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        msg = 'No camera device detected on this device.';
      }
      setCameraError(msg);
      setCameraActive(false);
    }
  }, [facingMode, stopStream]);

  // Handle open/close lifecycle
  useEffect(() => {
    if (isOpen) {
      startStream('environment');
    } else {
      stopStream();
      setLastScanResult(null);
      setCapturedSnapshot(null);
      setAutoScanEnabled(false);
    }
    return () => {
      stopStream();
    };
  }, [isOpen, startStream, stopStream]);

  // Flip camera (Rear <-> Front)
  const toggleFacingMode = () => {
    const nextMode = facingMode === 'environment' ? 'user' : 'environment';
    setFacingMode(nextMode);
    startStream(nextMode);
  };

  // Toggle Torch/Flashlight
  const toggleTorch = async () => {
    if (!streamRef.current) return;
    const track = streamRef.current.getVideoTracks()[0];
    if (track && torchAvailable) {
      try {
        const nextState = !torchOn;
        await track.applyConstraints({
          advanced: [{ torch: nextState }]
        });
        setTorchOn(nextState);
      } catch (e) {
        console.warn('Failed to toggle torch:', e);
      }
    }
  };

  // Capture current video frame to JPEG Blob
  const grabFrame = useCallback(() => {
    return new Promise((resolve) => {
      if (!videoRef.current || !canvasRef.current) {
        resolve(null);
        return;
      }
      const video = videoRef.current;
      const canvas = canvasRef.current;
      
      const vw = video.videoWidth || 640;
      const vh = video.videoHeight || 480;

      canvas.width = vw;
      canvas.height = vh;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        resolve(null);
        return;
      }

      ctx.drawImage(video, 0, 0, vw, vh);

      const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
      canvas.toBlob((blob) => {
        if (blob) {
          resolve({ blob, dataUrl });
        } else {
          resolve(null);
        }
      }, 'image/jpeg', 0.92);
    });
  }, []);

  // Perform single frame diagnostic capture
  const handleShutterCapture = async () => {
    if (isCapturing) return;
    setIsCapturing(true);
    setScanningPulse(true);

    try {
      if (window.navigator?.vibrate) {
        window.navigator.vibrate(50);
      }
    } catch (_) {}

    const frame = await grabFrame();
    if (!frame) {
      setIsCapturing(false);
      setScanningPulse(false);
      return;
    }

    setCapturedSnapshot(frame.dataUrl);

    const file = new File([frame.blob], `live_leaf_scan_${Date.now()}.jpg`, { type: 'image/jpeg' });

    // Send to backend diagnosis
    try {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('crop', selectedCrop);
      formData.append('lat', '13.3409');
      formData.append('lon', '74.7421');

      const result = await api.analyzeCrop(formData);
      setLastScanResult(result);

      if (onCaptureComplete) {
        onCaptureComplete({
          file,
          previewUrl: frame.dataUrl,
          name: file.name,
          result
        });
      }
    } catch (err) {
      console.error('Diagnostic error during live capture:', err);
      setCameraError(err.message || 'Diagnosis failed. Please center leaf clearly and retry.');
    } finally {
      setIsCapturing(false);
      setScanningPulse(false);
    }
  };

  // Native camera fallback (for devices where getUserMedia fails)
  const handleFallbackFile = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const reader = new FileReader();
      reader.onload = async (ev) => {
        const previewUrl = ev.target.result;
        setCapturedSnapshot(previewUrl);
        setIsCapturing(true);
        try {
          const formData = new FormData();
          formData.append('image', file);
          formData.append('crop', selectedCrop);
          const result = await api.analyzeCrop(formData);
          setLastScanResult(result);
          if (onCaptureComplete) {
            onCaptureComplete({
              file,
              previewUrl,
              name: file.name,
              result
            });
          }
        } catch (err) {
          setCameraError(err.message || 'Diagnosis failed on captured image.');
        } finally {
          setIsCapturing(false);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  // Continuous Auto-Scan Interval Effect
  useEffect(() => {
    if (autoScanEnabled && cameraActive && !capturedSnapshot) {
      autoScanTimerRef.current = setInterval(async () => {
        if (isCapturing) return;
        const frame = await grabFrame();
        if (!frame) return;

        const file = new File([frame.blob], `autoscan_${Date.now()}.jpg`, { type: 'image/jpeg' });
        try {
          const formData = new FormData();
          formData.append('image', file);
          formData.append('crop', selectedCrop);
          const res = await api.analyzeCrop(formData);
          setLastScanResult(res);
        } catch (_) {}
      }, 3500);
    } else {
      if (autoScanTimerRef.current) {
        clearInterval(autoScanTimerRef.current);
        autoScanTimerRef.current = null;
      }
    }

    return () => {
      if (autoScanTimerRef.current) {
        clearInterval(autoScanTimerRef.current);
      }
    };
  }, [autoScanEnabled, cameraActive, capturedSnapshot, grabFrame, isCapturing, selectedCrop]);

  if (!isOpen) return null;

  // Language helper for camera HUD
  const isKannada = preferredLanguage === 'kn';
  const isTulu = preferredLanguage === 'tcy';

  const getHudTitle = () => 'Live Mobile Crop Leaf Scanner';
  const getHudInstruction = () => 'Align infected leaf foliage inside the target frame';

  return (
    <div className="fixed inset-0 z-50 bg-black flex flex-col justify-between overflow-hidden touch-none select-none animate-fadeIn">
      {/* Hidden processing canvas */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Hidden fallback file input with capture="environment" for native phone camera */}
      <input
        type="file"
        ref={fallbackInputRef}
        accept="image/*"
        capture="environment"
        onChange={handleFallbackFile}
        className="hidden"
      />

      {/* Top HUD Controls Bar */}
      <div className="relative z-20 flex items-center justify-between p-4 bg-gradient-to-b from-black/90 via-black/50 to-transparent text-white">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onClose}
            className="w-10 h-10 rounded-full bg-white/20 hover:bg-white/30 backdrop-blur-md flex items-center justify-center text-white transition-all active:scale-95"
            title="Close Camera"
          >
            <X className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              <h2 className="text-xs sm:text-sm font-bold tracking-tight">{getHudTitle()}</h2>
            </div>
            <p className="text-[10px] text-slate-300 hidden sm:block">{getHudInstruction()}</p>
          </div>
        </div>

        {/* Quick Crop Selector Pill in Camera HUD */}
        <div className="flex items-center gap-2">
          <select
            value={selectedCrop}
            onChange={(e) => setSelectedCrop(e.target.value)}
            className="bg-black/60 backdrop-blur-md border border-white/20 text-white rounded-full px-3 py-1.5 text-xs font-bold focus:outline-hidden"
          >
            {SUPPORTED_CROPS.map((c) => (
              <option key={c.id} value={c.id} className="bg-slate-900 text-white">
                {c.name}
              </option>
            ))}
          </select>

          {/* Torch / Flashlight toggle if supported */}
          {torchAvailable && (
            <button
              type="button"
              onClick={toggleTorch}
              className={`w-9 h-9 rounded-full flex items-center justify-center transition-all ${
                torchOn ? 'bg-amber-400 text-black shadow-lg shadow-amber-400/50' : 'bg-white/20 text-white'
              }`}
              title="Toggle Flash / Torch"
            >
              {torchOn ? <Zap className="w-4 h-4" /> : <ZapOff className="w-4 h-4" />}
            </button>
          )}

          {/* Front / Rear Camera Flip */}
          <button
            type="button"
            onClick={toggleFacingMode}
            className="w-9 h-9 rounded-full bg-white/20 hover:bg-white/30 backdrop-blur-md flex items-center justify-center text-white transition-all active:scale-90"
            title="Switch Camera"
          >
            <SwitchCamera className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Viewfinder Video & Reticle Area */}
      <div className="relative flex-1 flex items-center justify-center bg-black overflow-hidden">
        {/* Live Video Stream */}
        {cameraActive && !capturedSnapshot && (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
        )}

        {/* Captured Freeze Snapshot Preview */}
        {capturedSnapshot && (
          <img
            src={capturedSnapshot}
            alt="Captured leaf"
            className="w-full h-full object-contain bg-slate-950"
          />
        )}

        {/* Camera Permission / Error Fallback Notice */}
        {cameraError && !cameraActive && !capturedSnapshot && (
          <div className="absolute inset-x-6 top-1/4 p-6 bg-slate-900/95 border border-rose-500/50 rounded-2xl text-center text-white space-y-4 max-w-md mx-auto shadow-2xl backdrop-blur-md">
            <div className="w-14 h-14 rounded-full bg-rose-500/20 text-rose-400 mx-auto flex items-center justify-center">
              <AlertCircle className="w-8 h-8" />
            </div>
            <h3 className="text-base font-bold text-white">Live Camera Access</h3>
            <p className="text-xs text-slate-300 leading-relaxed">{cameraError}</p>
            <div className="pt-2 flex flex-col gap-2">
              <button
                type="button"
                onClick={() => fallbackInputRef.current?.click()}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition-all shadow-lg flex items-center justify-center gap-2"
              >
                <Camera className="w-4 h-4" />
                <span>Open Phone Camera</span>
              </button>
              <button
                type="button"
                onClick={() => startStream('environment')}
                className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold"
              >
                Retry Live Stream
              </button>
            </div>
          </div>
        )}

        {/* Targeting Reticle & Leaf Scanner Overlay */}
        {cameraActive && !capturedSnapshot && (
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center p-8">
            {/* Reticle Box */}
            <div className="relative w-64 h-64 sm:w-80 sm:h-80 border-2 border-emerald-400/60 rounded-3xl overflow-hidden shadow-2xl">
              {/* Corner brackets */}
              <div className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-emerald-400 rounded-tl-2xl"></div>
              <div className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-emerald-400 rounded-tr-2xl"></div>
              <div className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-emerald-400 rounded-bl-2xl"></div>
              <div className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-emerald-400 rounded-br-2xl"></div>

              {/* Animated laser scanning line */}
              <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-emerald-400 to-transparent shadow-[0_0_12px_#34d399] animate-[scannerBeam_2.5s_ease-in-out_infinite]"></div>

              {/* Center Crosshair Guide */}
              <div className="absolute inset-0 flex items-center justify-center opacity-40">
                <div className="w-8 h-8 border border-white/50 rounded-full flex items-center justify-center">
                  <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full"></div>
                </div>
              </div>

              {/* Scanning Status Badge */}
              <div className="absolute bottom-3 inset-x-0 flex justify-center">
                <span className="bg-black/60 backdrop-blur-md text-emerald-400 text-[10px] font-bold px-3 py-1 rounded-full border border-emerald-500/30">
                  {autoScanEnabled ? '⚡ Live Detection Active' : 'KrishiNetra AI Vision Active'}
                </span>
              </div>
            </div>

            {/* Instruction Banner Under Reticle */}
            <p className="mt-4 text-xs font-semibold text-white/90 bg-black/60 backdrop-blur-md px-4 py-1.5 rounded-full border border-white/10 shadow-lg text-center max-w-xs">
              {getHudInstruction()}
            </p>
          </div>
        )}

        {/* Instant Detection Result Floating HUD Drawer */}
        {lastScanResult && (
          <div className="absolute bottom-24 inset-x-4 sm:inset-x-auto sm:w-[420px] bg-slate-900/95 backdrop-blur-lg border border-emerald-500/40 rounded-2xl p-4 text-white shadow-2xl animate-slideUp z-30">
            <div className="flex items-start justify-between gap-3 pb-2 border-b border-white/10">
              <div>
                <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider block">
                  {lastScanResult.crop} Disease Detected
                </span>
                <h3 className="text-lg font-black text-white leading-tight">
                  {lastScanResult.disease.label}
                </h3>
              </div>
              <div className="text-right">
                <span className="text-[10px] text-slate-400 block font-medium">Confidence</span>
                <span className="text-base font-black text-emerald-400">
                  {(lastScanResult.disease.confidence * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            {/* Severity & Localized summary */}
            <div className="mt-2.5 flex items-center justify-between text-xs">
              <span className="text-slate-300">Severity:</span>
              <span className="font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[11px]">
                {lastScanResult.disease.severity?.level?.toUpperCase() || 'MODERATE'} ({lastScanResult.disease.severity?.percentage || 35}%)
              </span>
            </div>

            {/* Localized Kannada or Tulu advisory */}
            {lastScanResult.multilingual_summary && (
              <div className="mt-2.5 p-2.5 rounded-xl bg-emerald-950/60 border border-emerald-800/60 text-xs">
                <p className="text-emerald-200 font-medium line-clamp-2">
                  {lastScanResult.multilingual_summary[preferredLanguage] ||
                    lastScanResult.multilingual_summary['en']}
                </p>
              </div>
            )}

            {/* Actions: Re-scan or View Full Advisory */}
            <div className="mt-3 flex gap-2">
              <button
                type="button"
                onClick={() => {
                  setCapturedSnapshot(null);
                  setLastScanResult(null);
                }}
                className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-bold transition-all text-center flex items-center justify-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Scan Another</span>
              </button>
              <button
                type="button"
                onClick={onClose}
                className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition-all text-center"
              >
                View Full Details
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Shutter & Capture Controls */}
      <div className="relative z-20 p-5 bg-gradient-to-t from-black via-black/80 to-transparent flex items-center justify-around">
        {/* Auto-scan mode toggle */}
        <div className="flex flex-col items-center">
          <button
            type="button"
            onClick={() => setAutoScanEnabled(!autoScanEnabled)}
            className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
              autoScanEnabled
                ? 'bg-emerald-500 text-white ring-4 ring-emerald-500/30'
                : 'bg-white/10 text-white/80 hover:bg-white/20'
            }`}
            title="Auto Continuous Scan"
          >
            <Activity className={`w-5 h-5 ${autoScanEnabled ? 'animate-pulse' : ''}`} />
          </button>
          <span className="text-[10px] font-bold text-white/80 mt-1">
            {autoScanEnabled ? 'Auto ON' : 'Live Scan'}
          </span>
        </div>

        {/* Big Shutter Button */}
        <div className="flex flex-col items-center">
          <button
            type="button"
            disabled={isCapturing}
            onClick={handleShutterCapture}
            className="relative w-20 h-20 rounded-full bg-white flex items-center justify-center shadow-2xl active:scale-90 transition-all border-4 border-slate-900 group"
          >
            <div className="w-16 h-16 rounded-full bg-emerald-600 group-hover:bg-emerald-500 flex items-center justify-center text-white transition-all shadow-inner">
              {isCapturing ? (
                <RefreshCw className="w-7 h-7 animate-spin" />
              ) : (
                <Camera className="w-7 h-7" />
              )}
            </div>
          </button>
          <span className="text-[11px] font-bold text-white mt-1.5 tracking-wide uppercase">
            {isCapturing ? 'Analyzing...' : 'Snap & Detect'}
          </span>
        </div>

        {/* Gallery / Fallback button */}
        <div className="flex flex-col items-center">
          <button
            type="button"
            onClick={() => fallbackInputRef.current?.click()}
            className="w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-all active:scale-95"
            title="Upload from Gallery"
          >
            <Sliders className="w-5 h-5" />
          </button>
          <span className="text-[10px] font-bold text-white/80 mt-1">Gallery</span>
        </div>
      </div>
    </div>
  );
}
