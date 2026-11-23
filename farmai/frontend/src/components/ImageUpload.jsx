import React, { useState, useRef } from 'react';
import { UploadCloud, Image as ImageIcon, X, AlertCircle, Camera, Smartphone } from 'lucide-react';

export default function ImageUpload({ onImageSelected, selectedImage, disabled, onOpenLiveCamera }) {
  const [dragOver, setDragOver] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const fileInputRef = useRef(null);
  const nativeCameraInputRef = useRef(null);

  const handleFileChange = (file) => {
    setErrorMsg('');
    if (!file) return;

    // Validate type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      setErrorMsg('Please upload a valid image file (JPEG, PNG, or WebP).');
      return;
    }

    // Validate size (8 MB)
    if (file.size > 8 * 1024 * 1024) {
      setErrorMsg('Image size exceeds 8 MB. Please select a smaller photo.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      onImageSelected({
        file,
        previewUrl: e.target.result,
        name: file.name
      });
    };
    reader.readAsDataURL(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (disabled) return;
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const clearSelection = (e) => {
    e.stopPropagation();
    onImageSelected(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Helper to generate a demo sample leaf image on the fly with Canvas
  const loadDemoSample = (diseaseType) => {
    const canvas = document.createElement('canvas');
    canvas.width = 300;
    canvas.height = 300;
    const ctx = canvas.getContext('2d');

    // Draw leafy background
    ctx.fillStyle = '#2d6a4f';
    ctx.fillRect(0, 0, 300, 300);

    // Draw leaf shape
    ctx.beginPath();
    ctx.ellipse(150, 150, 110, 70, Math.PI / 4, 0, 2 * Math.PI);
    ctx.fillStyle = '#52b788';
    ctx.fill();

    // Leaf vein
    ctx.strokeStyle = '#d8f3dc';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(80, 220);
    ctx.lineTo(220, 80);
    ctx.stroke();

    if (diseaseType === 'early_blight') {
      // Concentric target spots
      for (let i = 0; i < 4; i++) {
        const cx = 130 + i * 20;
        const cy = 130 - i * 10;
        ctx.beginPath();
        ctx.arc(cx, cy, 18, 0, 2 * Math.PI);
        ctx.fillStyle = '#744210';
        ctx.fill();
        ctx.beginPath();
        ctx.arc(cx, cy, 10, 0, 2 * Math.PI);
        ctx.fillStyle = '#451a03';
        ctx.fill();
      }
    } else if (diseaseType === 'late_blight') {
      // Irregular dark water-soaked rot
      ctx.beginPath();
      ctx.arc(170, 130, 35, 0, 2 * Math.PI);
      ctx.fillStyle = '#1c1917';
      ctx.fill();
    }

    canvas.toBlob((blob) => {
      const sampleFile = new File([blob], `${diseaseType}_leaf_sample.jpg`, { type: 'image/jpeg' });
      handleFileChange(sampleFile);
    }, 'image/jpeg');
  };

  return (
    <div className="w-full space-y-3">
      {/* Mobile Live Camera Quick Trigger Button */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => {
            if (onOpenLiveCamera) {
              onOpenLiveCamera();
            } else if (nativeCameraInputRef.current) {
              nativeCameraInputRef.current.click();
            }
          }}
          disabled={disabled}
          className="flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500 text-white font-bold text-xs sm:text-sm shadow-md shadow-emerald-700/20 active:scale-98 transition-all"
        >
          <Camera className="w-4 h-4 animate-pulse" />
          <span>Live Camera Scan</span>
        </button>

        <button
          type="button"
          onClick={() => nativeCameraInputRef.current?.click()}
          disabled={disabled}
          className="flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-100 font-bold text-xs sm:text-sm shadow-sm active:scale-98 transition-all"
        >
          <Smartphone className="w-4 h-4 text-emerald-400" />
          <span>Phone Camera Snap</span>
        </button>
      </div>

      {/* Hidden native mobile camera input */}
      <input
        type="file"
        ref={nativeCameraInputRef}
        accept="image/*"
        capture="environment"
        onChange={(e) => e.target.files && handleFileChange(e.target.files[0])}
        className="hidden"
        disabled={disabled}
      />

      {/* Drag & drop container */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all duration-200 ${
          dragOver
            ? 'border-emerald-500 bg-emerald-50/50 scale-[1.01]'
            : 'border-slate-300 hover:border-emerald-400 bg-white hover:bg-slate-50/50'
        } ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => e.target.files && handleFileChange(e.target.files[0])}
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          disabled={disabled}
        />

        {selectedImage ? (
          <div className="relative flex flex-col items-center">
            <div className="relative group rounded-xl overflow-hidden shadow-md max-h-64 border border-slate-200">
              <img
                src={selectedImage.previewUrl}
                alt="Selected crop leaf"
                className="object-contain max-h-60 w-auto rounded-lg"
              />
              <button
                type="button"
                onClick={clearSelection}
                className="absolute top-2 right-2 bg-slate-900/70 hover:bg-slate-900 text-white p-1.5 rounded-full transition-colors"
                title="Remove image"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="mt-3 text-sm font-medium text-slate-700 truncate max-w-xs">
              {selectedImage.name}
            </p>
            <span className="text-xs text-emerald-600 font-semibold mt-1">
              Click or drag to replace image
            </span>
          </div>
        ) : (
          <div className="py-8 flex flex-col items-center justify-center">
            <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 mb-4 shadow-inner">
              <UploadCloud className="w-8 h-8" />
            </div>
            <h3 className="text-base font-semibold text-slate-800">
              Upload Crop Leaf Photo
            </h3>
            <p className="text-sm text-slate-500 mt-1 max-w-sm">
              Drag & drop a clear photo of an infected or healthy leaf, or tap to browse
            </p>
            <div className="mt-4 flex items-center gap-2 text-xs text-slate-400">
              <span>Supports JPG, PNG, WebP</span>
              <span>•</span>
              <span>Max 8 MB</span>
            </div>
          </div>
        )}
      </div>

      {errorMsg && (
        <div className="mt-3 flex items-center gap-2 text-sm text-rose-600 bg-rose-50 border border-rose-200 p-3 rounded-xl">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Quick 1-Click Samples for Easy Evaluation */}
      <div className="mt-3 flex items-center justify-between flex-wrap gap-2 text-xs">
        <span className="text-slate-500 font-medium">Quick Test Samples:</span>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => loadDemoSample('early_blight')}
            className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-medium transition-colors border border-emerald-200"
          >
            Early Blight Sample
          </button>
          <button
            type="button"
            onClick={() => loadDemoSample('late_blight')}
            className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-medium transition-colors border border-emerald-200"
          >
            Late Blight Sample
          </button>
          <button
            type="button"
            onClick={() => loadDemoSample('healthy')}
            className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-medium transition-colors border border-emerald-200"
          >
            Healthy Leaf Sample
          </button>
        </div>
      </div>
    </div>
  );
}
