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

  // Real-Time Server-Sent Events (SSE) Client
  initSSEConnection(callbacks = {}) {
    if (this.eventSource) {
      this.eventSource.close();
    }

    const sseUrl = `${this.baseURL}/events/stream`;
    console.log(`[ALERTORA SSE] Connecting to real-time event stream at ${sseUrl}...`);

    try {
      this.eventSource = new EventSource(sseUrl);

      this.eventSource.onopen = (evt) => {
        console.log("[ALERTORA SSE] Connection established successfully.");
        if (typeof callbacks.onStateChange === "function") {
          callbacks.onStateChange("CONNECTED");
        }
      };

      this.eventSource.onerror = (err) => {
        console.warn("[ALERTORA SSE] Connection dropped or pending reconnect...", err);
        if (typeof callbacks.onStateChange === "function") {
          callbacks.onStateChange("RECONNECTING");
        }
      };

      // Register standard typed event listeners
      const registerListener = (eventName, handler) => {
        if (typeof handler === "function") {
          this.eventSource.addEventListener(eventName, (e) => {
            try {
              const data = JSON.parse(e.data);
              handler(data);
            } catch (ex) {
              console.error(`[ALERTORA SSE] Error parsing ${eventName} payload:`, ex);
            }
          });
        }
      };

      registerListener("forecast_updated", callbacks.onForecastUpdated);
      registerListener("risk_zones_updated", callbacks.onRiskZonesUpdated);
      registerListener("storm_trajectory_updated", callbacks.onStormTrajectoryUpdated);
      registerListener("alert_created", callbacks.onAlertCreated);
      registerListener("system_status_updated", callbacks.onSystemStatusUpdated);
      registerListener("heartbeat", callbacks.onHeartbeat);

      return this.eventSource;
    } catch (e) {
      console.warn("[ALERTORA SSE] EventSource unavailable:", e);
      if (typeof callbacks.onStateChange === "function") {
        callbacks.onStateChange("DISCONNECTED");
      }
      return null;
    }
  }

  // Register device for spatial geohash-targeted notifications
  async registerDevice(deviceToken, lat, lng, platform = "web") {
    try {
      const response = await fetch(`${this.baseURL}/notifications/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_token: deviceToken,
          lat: lat,
          lng: lng,
          platform: platform
        })
      });
      return await response.json();
    } catch (err) {
      console.warn("[ALERTORA API] Device registration request failed:", err);
      return null;
    }
  }

  // Trigger emergency alert via FastAPI backend
  async triggerEmergencyAlert(payload) {
    try {
      const response = await fetch(`${this.baseURL}/alerts/evaluate-and-dispatch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      return await response.json();
    } catch (err) {
      console.warn("[ALERTORA API] Alert dispatch request failed:", err);
      return null;
    }
  }
}

// Global API instance
window.alertoraAPI = new AlertoraAPIService();


