/**
 * FarmAI API client - Single source of truth for all backend communications.
 */
const BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Handle API response errors cleanly.
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch {
      // Ignore json parse error on raw text failures
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

export const api = {
  /**
   * Account Criteria: Sign up, Sign in, Logout, and Current user profile
   */
  async signUp(fullName, email, password, preferredLanguage = 'en') {
    const res = await fetch(`${BASE_URL}/api/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        full_name: fullName,
        email,
        password,
        preferred_language: preferredLanguage
      }),
    });
    return handleResponse(res);
  },

  async signIn(email, password) {
    const res = await fetch(`${BASE_URL}/api/auth/signin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    return handleResponse(res);
  },

  async signOut() {
    const res = await fetch(`${BASE_URL}/api/auth/logout`, {
      method: 'POST',
    });
    return handleResponse(res);
  },

  async getMe(token) {
    const res = await fetch(`${BASE_URL}/api/auth/me?token=${encodeURIComponent(token)}`);
    return handleResponse(res);
  },

  /**
   * Health check
   */
  async getHealth() {
    const res = await fetch(`${BASE_URL}/health`);
    return handleResponse(res);
  },

  /**
   * Analyze uploaded crop leaf image
   */
  async analyzeCrop(formData) {
    const res = await fetch(`${BASE_URL}/api/analyze`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse(res);
  },

  /**
   * Fetch current weather & 3-day forecast
   */
  async getWeather(lat = 13.3409, lon = 74.7421) {
    const res = await fetch(`${BASE_URL}/api/weather?lat=${lat}&lon=${lon}`);
    return handleResponse(res);
  },

  /**
   * Fetch irrigation advisory
   */
  async getIrrigation(lat = 13.3409, lon = 74.7421, crop = 'Tomato', growthStage = 'Vegetative', soilMoisture = 45.0) {
    const query = new URLSearchParams({
      lat: String(lat),
      lon: String(lon),
      crop,
      growth_stage: growthStage,
      soil_moisture_pct: String(soilMoisture)
    });
    const res = await fetch(`${BASE_URL}/api/irrigation?${query.toString()}`);
    return handleResponse(res);
  },

  /**
   * Fetch Sentinel-2 NDVI monitoring data
   */
  async getSatelliteNdvi(lat = 13.3409, lon = 74.7421, sizeM = 1000, days = 30) {
    const query = new URLSearchParams({
      lat: String(lat),
      lon: String(lon),
      size_m: String(sizeM),
      days: String(days)
    });
    const res = await fetch(`${BASE_URL}/api/satellite/ndvi?${query.toString()}`);
    return handleResponse(res);
  },

  /**
   * Send assistant chat message
   */
  async sendChat(message, analysisId = null, language = 'en') {
    const res = await fetch(`${BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        analysis_id: analysisId,
        language
      }),
    });
    return handleResponse(res);
  },

  /**
   * Fetch analysis history
   */
  async getHistory(farmId = null, limit = 20) {
    const query = new URLSearchParams({ limit: String(limit) });
    if (farmId) query.append('farm_id', String(farmId));
    const res = await fetch(`${BASE_URL}/api/history?${query.toString()}`);
    return handleResponse(res);
  }
};
