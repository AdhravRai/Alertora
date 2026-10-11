/* ==========================================================================
   ALERTORA AI — Backend Ready API Service Layer
   Abstracts data fetching between simulated local mock data & FastAPI backend.
   ========================================================================== */

class AlertoraAPIService {
  constructor() {
    // FastAPI backend is active for development integration
    this.useLiveBackend = true;
    const host = (typeof window !== "undefined" && window.location && window.location.hostname && window.location.hostname !== "")
      ? window.location.hostname
      : "localhost";
    this.baseURL = `http://${host}:8000/api`;
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
  // Fetch All Locations
  // ------------------------------------------------------------------------
  async getLocations() {
    if (this.useLiveBackend) {
      try {
        const response = await fetch(`${this.baseURL}/locations`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        console.warn(
          "Live API locations unavailable, using simulated locations.",
          err
        );
      }
    }

    return ALERTORA_DATA.locations;
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


