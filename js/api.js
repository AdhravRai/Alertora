/* ==========================================================================
   ALERTORA AI — Backend Ready API Service Layer
   Abstracts data fetching between simulated local mock data & FastAPI backend.
   ========================================================================== */

class AlertoraAPIService {
  constructor() {
    // FastAPI backend is active for development & production integration
    this.useLiveBackend = true;
    if (typeof window !== "undefined" && window.location) {
      const port = window.location.port;
      const protocol = window.location.protocol;
      // When running on local static dev servers (e.g. 8080 or 3000), backend is on port 8000
      if (protocol === "file:" || port === "8080" || port === "3000") {
        const host = window.location.hostname || "localhost";
        this.baseURL = `http://${host}:8000/api`;
      } else {
        // Production (Render / Cloud) or unified FastAPI server: use same-origin /api
        this.baseURL = `${window.location.origin}/api`;
      }
    } else {
      this.baseURL = "http://localhost:8000/api";
    }

    // Centralized SSE Connection Manager State
    this.eventSource = null;
    this.sseRetryCount = 0;
    this.sseMaxRetryInterval = 30000;
    this.sseReconnectTimer = null;
    this.sseConnectionEpoch = 0;
    this.sseExplicitStop = false;
    this.sseCallbacks = {};
    this.sseState = "DISCONNECTED";

    // Setup network online/offline listeners for resilient SSE management
    if (typeof window !== "undefined") {
      window.addEventListener("online", () => {
        console.log("[ALERTORA SSE] Browser back online. Resuming connection if needed...");
        if (this.sseState === "OFFLINE" || this.sseState === "RECONNECTING" || this.sseState === "DISCONNECTED") {
          this.sseRetryCount = 0;
          this.connectSSE();
        }
      });
      window.addEventListener("offline", () => {
        console.warn("[ALERTORA SSE] Browser is offline. Suspending active retry timers...");
        if (this.sseReconnectTimer) {
          clearTimeout(this.sseReconnectTimer);
          this.sseReconnectTimer = null;
        }
        if (this.eventSource) {
          this.eventSource.close();
          this.eventSource = null;
        }
        this.setSSEState("OFFLINE");
      });
    }
  }

  // ------------------------------------------------------------------------
  // Canonical Region Normalizer (Defensive Null-Safety Boundary)
  // ------------------------------------------------------------------------
  normalizeLocation(loc) {
    if (!loc || typeof loc !== "object") {
      return {
        id: "Grid-Default",
        name: "Grid-Default",
        region: "Grid-Default",
        currentRisk: "LOW",
        lat: 0,
        lng: 0,
        temp: 28.0,
        humidity: 75,
        windSpeed: 25,
        pressure: 1008.0,
        rainfallRate: 0,
        nextHazardETA: null,
        nextHazardType: "None",
        nowcast: []
      };
    }

    const id = loc.id || loc.region_id || loc.gridId || (loc.name ? loc.name.toLowerCase().replace(/[\s\/]+/g, "-") : "Grid-Default");
    const name = loc.name || loc.region || loc.district || loc.id || "Grid-Default";
    const region = loc.region || loc.region_id || loc.district || name;
    const currentRisk = (loc.currentRisk || loc.risk_level || loc.risk || "LOW").toUpperCase();
    const lat = typeof loc.lat === "number" ? loc.lat : (typeof loc.latitude === "number" ? loc.latitude : 0);
    const lng = typeof loc.lng === "number" ? loc.lng : (typeof loc.longitude === "number" ? loc.longitude : 0);

    return {
      ...loc,
      id: String(id),
      name: String(name),
      region: String(region),
      currentRisk: String(currentRisk),
      lat: Number(lat),
      lng: Number(lng),
      temp: typeof loc.temp === "number" ? loc.temp : 28.0,
      humidity: typeof loc.humidity === "number" ? loc.humidity : 75,
      windSpeed: typeof loc.windSpeed === "number" ? loc.windSpeed : 25,
      pressure: typeof loc.pressure === "number" ? loc.pressure : 1008.0,
      rainfallRate: typeof loc.rainfallRate === "number" ? loc.rainfallRate : 0,
      nextHazardETA: loc.nextHazardETA || null,
      nextHazardType: loc.nextHazardType || (currentRisk === "LOW" ? "Routine Monitoring" : "Convective Cell"),
      nowcast: Array.isArray(loc.nowcast) && loc.nowcast.length > 0 ? loc.nowcast : []
    };
  }

  // ------------------------------------------------------------------------
  // Fetch System Status
  // ------------------------------------------------------------------------
  async getSystemStatus() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(`${this.baseURL}/system-status`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        console.warn(
          "Live API unavailable, falling back to simulated system data.",
          err
        );
      }
    }

    return ALERTORA_DATA.system;
  }

  // ------------------------------------------------------------------------
  // Fetch All Locations (with Canonical Boundary Normalization)
  // ------------------------------------------------------------------------
  async getLocations() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(`${this.baseURL}/locations`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        if (Array.isArray(data) && data.length > 0) {
          return data.map(l => this.normalizeLocation(l));
        }
      } catch (err) {
        console.warn(
          "Live API locations unavailable, using simulated locations.",
          err
        );
      }
    }

    const fallbackLocs = (typeof ALERTORA_DATA !== "undefined" && Array.isArray(ALERTORA_DATA.locations))
      ? ALERTORA_DATA.locations
      : [];
    return fallbackLocs.map(l => this.normalizeLocation(l));
  }

  // ------------------------------------------------------------------------
  // Fetch Nowcast Timeline for Specific Location
  // ------------------------------------------------------------------------
  async getLocationNowcast(locationId) {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(
          `${this.baseURL}/prediction?location_id=${locationId}`
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        console.warn(
          "Live API forecast unavailable, using fallback.",
          err
        );
      }
    }

    const loc =
      ALERTORA_DATA.locations.find((l) => l.id === locationId) ||
      ALERTORA_DATA.locations[0];

    return loc;
  }

  // ------------------------------------------------------------------------
  // NEW — Fetch Current Risk
  // ------------------------------------------------------------------------
  async getCurrentRisk() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(`${this.baseURL}/current-risk`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        console.warn(
          "Live API current risk unavailable.",
          err
        );
      }
    }

    return null;
  }

  // ------------------------------------------------------------------------
  // NEW — Fetch 0–6 Hour Forecast
  // ------------------------------------------------------------------------
  async getForecast() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(`${this.baseURL}/forecast`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        console.warn(
          "Live API forecast unavailable.",
          err
        );
      }
    }

    return null;
  }

  // ------------------------------------------------------------------------
  // NEW — Fetch Storms and Trajectory
  // ------------------------------------------------------------------------
  async getStorms() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(`${this.baseURL}/storms`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        console.warn(
          "Live API storms unavailable.",
          err
        );
      }
    }

    return null;
  }

  // ------------------------------------------------------------------------
  // Fetch Major Hazard Cards Summary
  // ------------------------------------------------------------------------
  async getHazardsSummary() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(`${this.baseURL}/hazards-summary`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        console.warn("Live API hazards unavailable.", err);
      }
    }

    return ALERTORA_DATA.hazardsSummary;
  }

  // ------------------------------------------------------------------------
  // Fetch AI Safety Advisor Precautions
  // ------------------------------------------------------------------------
  async getSafetyPrecautions(hazardType = "THUNDERSTORM") {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(
          `${this.baseURL}/precautions?hazard=${hazardType}`
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        console.warn(
          "Live API precautions unavailable.",
          err
        );
      }
    }

    return (
      ALERTORA_DATA.precautionsDatabase[hazardType] ||
      ALERTORA_DATA.precautionsDatabase["THUNDERSTORM"]
    );
  }

  // ------------------------------------------------------------------------
  // Fetch Emergency Alerts Feed
  // ------------------------------------------------------------------------
  async getAlerts() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(`${this.baseURL}/alerts`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        console.warn(
          "Live API alerts unavailable.",
          err
        );
      }
    }

    return ALERTORA_DATA.alertsFeed;
  }

  // ------------------------------------------------------------------------
  // Fetch EOC Command Center District Grid
  // ------------------------------------------------------------------------
  async getEOCData() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(`${this.baseURL}/eoc`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        console.warn(
          "Live API EOC data unavailable.",
          err
        );
      }
    }

    return ALERTORA_DATA.eocDistricts;
  }

  // ------------------------------------------------------------------------
  // NEW — Fetch XAI Explainability
  // ------------------------------------------------------------------------
  async getExplainability() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(
          `${this.baseURL}/explainability`
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        console.warn(
          "Live API explainability unavailable.",
          err
        );
      }
    }

    return null;
  }

  // ------------------------------------------------------------------------
  // NEW — Fetch Geographic High-Risk Zones
  // ------------------------------------------------------------------------
  async getRiskZones() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(
          `${this.baseURL}/risk-zones`
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        console.warn(
          "Live API risk zones unavailable.",
          err
        );
      }
    }

    return null;
  }

  // ------------------------------------------------------------------------
  // Existing XAI fallback
  // ------------------------------------------------------------------------
  async getXAIFactors() {
    return ALERTORA_DATA.xaiFactors;
  }

  // ------------------------------------------------------------------------
  // Existing Fusion Logs
  // ------------------------------------------------------------------------
  async getFusionLogs() {
    return ALERTORA_DATA.fusionLogs;
  }

  // ------------------------------------------------------------------------
  // NEW — Fetch Historical Events
  // ------------------------------------------------------------------------
  async getHistoricalEvents() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(
          `${this.baseURL}/historical-events`
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        console.warn(
          "Live API historical events unavailable.",
          err
        );
      }
    }

    return null;
  }

  // ------------------------------------------------------------------------
  // NEW — Fetch Single Historical Event
  // ------------------------------------------------------------------------
  async getHistoricalEvent(eventId) {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(
          `${this.baseURL}/historical-events/${eventId}`
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        console.warn(
          "Live API historical event unavailable.",
          err
        );
      }
    }

    return null;
  }

  // ------------------------------------------------------------------------
  // Trigger Simulated Emergency Warning (Demo Action)
  // ------------------------------------------------------------------------
  async triggerPublicWarning(districtName) {
    console.log(
      `[ALERTORA API] Public Emergency Warning triggered for district: ${districtName}`
    );

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

  // ------------------------------------------------------------------------
  // Centralized Server-Sent Events (SSE) Manager (Bounded Backoff & Safe Lifecycle)
  // ------------------------------------------------------------------------
  setSSEState(newState) {
    this.sseState = newState;
    if (typeof this.sseCallbacks.onStateChange === "function") {
      try {
        this.sseCallbacks.onStateChange(newState);
      } catch (err) {
        console.warn("[ALERTORA SSE] Error in onStateChange callback:", err);
      }
    }
  }

  initSSEConnection(callbacks = {}) {
    this.sseCallbacks = callbacks;
    this.sseExplicitStop = false;
    this.sseRetryCount = 0;
    return this.connectSSE();
  }

  connectSSE() {
    if (this.sseExplicitStop) {
      return null;
    }

    // Check if network is known to be offline
    if (typeof window !== "undefined" && window.navigator && window.navigator.onLine === false) {
      this.setSSEState("OFFLINE");
      return null;
    }

    // Clear any pending retry timer before starting a new connection
    if (this.sseReconnectTimer) {
      clearTimeout(this.sseReconnectTimer);
      this.sseReconnectTimer = null;
    }

    // Close any previous EventSource instance to prevent duplicate connections
    if (this.eventSource) {
      try {
        this.eventSource.close();
      } catch (e) {
        // Safe ignore
      }
      this.eventSource = null;
    }

    // Increment epoch to invalidate callbacks from obsolete connections
    this.sseConnectionEpoch++;
    const currentEpoch = this.sseConnectionEpoch;

    const sseUrl = `${this.baseURL}/events/stream`;
    console.log(`[ALERTORA SSE] Establishing connection to ${sseUrl} (Epoch #${currentEpoch})...`);
    this.setSSEState("CONNECTING");

    try {
      const es = new EventSource(sseUrl);
      this.eventSource = es;

      es.onopen = (evt) => {
        if (this.sseConnectionEpoch !== currentEpoch) {
          try { es.close(); } catch (_) {}
          return;
        }
        console.log("[ALERTORA SSE] Real-time event stream connected.");
        this.sseRetryCount = 0; // Reset retry counter on successful connection
        this.setSSEState("CONNECTED");
      };

      es.onerror = (err) => {
        if (this.sseConnectionEpoch !== currentEpoch) {
          return;
        }

        console.warn("[ALERTORA SSE] Stream error or drop. Cleaning up connection...", err);
        try {
          es.close();
        } catch (_) {}
        this.eventSource = null;

        if (this.sseExplicitStop) {
          this.setSSEState("DISCONNECTED");
          return;
        }

        if (typeof window !== "undefined" && window.navigator && window.navigator.onLine === false) {
          this.setSSEState("OFFLINE");
          return;
        }

        this.setSSEState("RECONNECTING");

        // Bounded Exponential Backoff with Jitter (max 30 seconds)
        const baseDelay = Math.min(1000 * Math.pow(2, this.sseRetryCount), this.sseMaxRetryInterval);
        const jitter = Math.floor(Math.random() * 1000);
        const delay = Math.min(baseDelay + jitter, this.sseMaxRetryInterval);

        this.sseRetryCount = Math.min(this.sseRetryCount + 1, 10);
        console.log(`[ALERTORA SSE] Scheduling reconnect in ${delay}ms (attempt #${this.sseRetryCount})...`);

        this.sseReconnectTimer = setTimeout(() => {
          if (this.sseConnectionEpoch === currentEpoch && !this.sseExplicitStop) {
            this.connectSSE();
          }
        }, delay);
      };

      // Helper to register single protected listener per event
      const registerListener = (eventName, handler) => {
        es.addEventListener(eventName, (e) => {
          if (this.sseConnectionEpoch !== currentEpoch) {
            return; // Discard stale event from prior connection
          }
          if (typeof handler === "function") {
            try {
              const data = JSON.parse(e.data);
              handler(data);
            } catch (ex) {
              console.error(`[ALERTORA SSE] Error parsing ${eventName} payload:`, ex);
            }
          }
        });
      };

      registerListener("forecast_updated", this.sseCallbacks.onForecastUpdated);
      registerListener("risk_zones_updated", this.sseCallbacks.onRiskZonesUpdated);
      registerListener("storm_trajectory_updated", this.sseCallbacks.onStormTrajectoryUpdated);
      registerListener("alert_created", this.sseCallbacks.onAlertCreated);
      registerListener("system_status_updated", this.sseCallbacks.onSystemStatusUpdated);
      registerListener("heartbeat", this.sseCallbacks.onHeartbeat);

      return this.eventSource;
    } catch (e) {
      console.warn("[ALERTORA SSE] EventSource unavailable:", e);
      this.setSSEState("DISCONNECTED");
      return null;
    }
  }

  disconnectSSE() {
    console.log("[ALERTORA SSE] Explicitly disconnecting real-time stream...");
    this.sseExplicitStop = true;
    this.sseConnectionEpoch++;
    if (this.sseReconnectTimer) {
      clearTimeout(this.sseReconnectTimer);
      this.sseReconnectTimer = null;
    }
    if (this.eventSource) {
      try {
        this.eventSource.close();
      } catch (_) {}
      this.eventSource = null;
    }
    this.setSSEState("DISCONNECTED");
  }

  reconnectSSE() {
    this.sseExplicitStop = false;
    this.sseRetryCount = 0;
    return this.connectSSE();
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

  // Search and geocode locations for weather analysis
  async searchLocations(query) {
    try {
      const response = await fetch(`${this.baseURL}/location/search?q=${encodeURIComponent(query)}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return await response.json();
    } catch (err) {
      console.warn("[ALERTORA API] Location search failed:", err);
      return [];
    }
  }

  // Analyze location weather using existing trained ML model
  async analyzeLocation(payload) {
    try {
      const response = await fetch(`${this.baseURL}/location/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      return await response.json();
    } catch (err) {
      console.error("[ALERTORA API] Location analysis failed:", err);
      throw err;
    }
  }
}


// Global API instance
window.alertoraAPI = new AlertoraAPIService();


