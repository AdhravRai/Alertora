/* ==========================================================================
   ALERTORA AI — Backend Ready API Service Layer
   Abstracts data fetching between simulated local mock data & FastAPI backend.
   ========================================================================== */

class AlertoraAPIService {
  constructor() {
    // FastAPI backend is active for development integration
    this.useLiveBackend = true;
    this.baseURL = "http://localhost:8000/api";
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
}

// Global API instance
window.alertoraAPI = new AlertoraAPIService();
