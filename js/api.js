/* ==========================================================================
   ALERTORA AI — Backend Ready API Service Layer
   Abstracts data fetching between simulated local mock data & FastAPI backend.
   ========================================================================== */

class AlertoraAPIService {
  constructor() {
    this.useLiveBackend = false; // Toggle to true when Python FastAPI backend is active
    this.baseURL = "http://localhost:8000/api";
  }

  // Fetch System Status
  async getSystemStatus() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(`${this.baseURL}/system-status`);
        return await response.json();
      } catch (err) {
        console.warn("Live API unavailable, falling back to simulated data.", err);
      }
    }
    return ALERTORA_DATA.system;
  }

  // Fetch All Locations
  async getLocations() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(`${this.baseURL}/locations`);
        return await response.json();
      } catch (err) {
        console.warn("Live API unavailable, using simulated locations.", err);
      }
    }
    return ALERTORA_DATA.locations;
  }

  // Fetch Nowcast Timeline for Specific Location
  async getLocationNowcast(locationId) {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(`${this.baseURL}/prediction?location_id=${locationId}`);
        return await response.json();
      } catch (err) {
        console.warn("Live API forecast unavailable, using fallback.", err);
      }
    }
    const loc = ALERTORA_DATA.locations.find(l => l.id === locationId) || ALERTORA_DATA.locations[0];
    return loc;
  }

  // Fetch Major Hazard Cards Summary
  async getHazardsSummary() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(`${this.baseURL}/hazards-summary`);
        return await response.json();
      } catch (err) {
        console.warn("Live API unavailable.", err);
      }
    }
    return ALERTORA_DATA.hazardsSummary;
  }

  // Fetch AI Safety Advisor Precautions
  async getSafetyPrecautions(hazardType = "THUNDERSTORM") {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(`${this.baseURL}/precautions?hazard=${hazardType}`);
        return await response.json();
      } catch (err) {
        console.warn("Live API precautions unavailable.", err);
      }
    }
    return ALERTORA_DATA.precautionsDatabase[hazardType] || ALERTORA_DATA.precautionsDatabase["THUNDERSTORM"];
  }

  // Fetch Emergency Alerts Feed
  async getAlerts() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(`${this.baseURL}/alerts`);
        return await response.json();
      } catch (err) {
        console.warn("Live API alerts unavailable.", err);
      }
    }
    return ALERTORA_DATA.alertsFeed;
  }

  // Fetch EOC Command Center District Grid
  async getEOCData() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(`${this.baseURL}/eoc`);
        return await response.json();
      } catch (err) {
        console.warn("Live API EOC data unavailable.", err);
      }
    }
    return ALERTORA_DATA.eocDistricts;
  }

  // Fetch XAI Explainable AI Factors
  async getXAIFactors() {
    return ALERTORA_DATA.xaiFactors;
  }

  // Fetch Data Fusion Logs & Sensor Status
  async getFusionLogs() {
    return ALERTORA_DATA.fusionLogs;
  }

  // Trigger Simulated Emergency Warning (Demo Action)
  async triggerPublicWarning(districtName) {
    console.log(`[ALERTORA API] Public Emergency Warning triggered for district: ${districtName}`);
    return {
      status: "SUCCESS",
      message: `Emergency Cell Broadcast & Siren warning dispatched for ${districtName}`,
      timestamp: new Date().toLocaleTimeString()
    };
  }
  // Fetch Validated July 29 Forecast Data
  async getForecastJuly29() {
    try {
      const response = await fetch("data/processed/alertora_forecast_july29_0200.json");
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      return await response.json();
    } catch (err) {
      console.error("[ALERTORA API] Error fetching July 29 forecast JSON:", err);
      return null;
    }
  }

  // Fetch Validated July 29 Risk Zones
  async getRiskZonesJuly29() {
    try {
      const response = await fetch("data/processed/risk_zones_july29_0200.json");
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      return await response.json();
    } catch (err) {
      console.error("[ALERTORA API] Error fetching July 29 risk zones JSON:", err);
      return null;
    }
  }

  // Fetch Spatial Nowcast Trajectory Output
  async getNowcastTrajectory() {
    try {
      const response = await fetch("person-b/output/nowcast_result.json");
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      return await response.json();
    } catch (err) {
      console.error("[ALERTORA API] Error fetching nowcast result JSON:", err);
      return null;
    }
  }
}

// Global API instance
window.alertoraAPI = new AlertoraAPIService();

