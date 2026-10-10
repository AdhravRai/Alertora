/* ==========================================================================
   ALERTORA AI — Master Application Controller & UI Renderer
   ========================================================================== */

document.addEventListener("DOMContentLoaded", async () => {
  // Application State
  const state = {
    currentView: "landing", // landing, dashboard, map, predictions, alerts, precautions, eoc, mysafety, analytics, fusion, about
    selectedLocationId: "chennai",
    selectedHazard: "THUNDERSTORM",
    selectedTimelineHourIndex: 0,
    activeMapLayer: "radar",
    map: null,
    radarOverlay: null,
    riskPolygons: [],
    stormSimulationActive: false,
    stormSimulationInterval: null,
    countdownSeconds: 5076, // 01:24:36
    countdownInterval: null,
    notificationsEnabled: {
      severe: true,
      lightning: true,
      hail: true,
      cloudburst: true,
      sms: true,
      app: true
    },
    analyticsCharts: {},
    gpsLocationData: null,
    userLocationMarker: null
  };

  // DOM Cache
  const views = {
    landing: document.getElementById("view-landing"),
    dashboard: document.getElementById("view-dashboard"),
    map: document.getElementById("view-map"),
    alerts: document.getElementById("view-alerts"),
    precautions: document.getElementById("view-precautions"),
    eoc: document.getElementById("view-eoc"),
    analytics: document.getElementById("view-analytics")
  };

  // Initialize Landing Canvas Radar Animation
  initRadarCanvas();

  // Navigation Setup
  setupNavigation();

  // Load Data & Initial Setup
  const locations = await window.alertoraAPI.getLocations();
  populateLocationSelector(locations);
  startCountdownTimer();
  renderNotificationDropdown();
  startHeaderClock();
  initMySafetyEventListeners();

  // Button Listeners
  document.getElementById("btn-launch-dashboard").addEventListener("click", () => switchView("dashboard"));
  const btnExploreHow = document.getElementById("btn-explore-how");
  const btnSimStorm = document.getElementById("btn-sim-storm");
  if (btnSimStorm) btnSimStorm.addEventListener("click", toggleStormSimulation);
  document.getElementById("btn-notif-modal").addEventListener("click", toggleNotificationModal);
  
  const btnCloseNotif = document.getElementById("btn-close-notif");
  if (btnCloseNotif) btnCloseNotif.addEventListener("click", toggleNotificationModal);

  const btnCloseDropdown = document.getElementById("btn-close-notif-dropdown");
  if (btnCloseDropdown) {
    btnCloseDropdown.addEventListener("click", () => {
      const dropdown = document.getElementById("notif-dropdown");
      if (dropdown) dropdown.classList.add("hidden");
    });
  }

  // Click outside listener for notification dropdown
  document.addEventListener("click", (e) => {
    const dropdown = document.getElementById("notif-dropdown");
    const bellBtn = document.getElementById("btn-notif-modal");
    if (dropdown && !dropdown.classList.contains("hidden")) {
      if (!dropdown.contains(e.target) && !bellBtn.contains(e.target)) {
        dropdown.classList.add("hidden");
      }
    }
  });

  // Mobile menu toggle listener
  const mobileToggle = document.getElementById("btn-mobile-menu-toggle");
  if (mobileToggle) {
    mobileToggle.addEventListener("click", () => {
      const mobileMenu = document.getElementById("header-mobile-menu");
      if (mobileMenu) mobileMenu.classList.toggle("hidden");
    });
  }

  const btnLandingGps = document.getElementById("btn-landing-gps");
  if (btnLandingGps) {
    btnLandingGps.addEventListener("click", () => {
      detectUserLocation();
    });
  }

  const btnUseGps = document.getElementById("btn-use-gps");
  if (btnUseGps) btnUseGps.addEventListener("click", detectUserLocation);

  // Landing Page Feature Cards Action Buttons & Card Navigation
  document.querySelectorAll(".card-action-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const action = btn.dataset.action;
      const hazardKey = btn.dataset.hazardFeature;
      if (!hazardKey) return;

      if (action === "prediction") {
        state.selectedHazard = hazardKey;
        state.activeMapLayer = hazardKey.toLowerCase();

        // Switch directly to Live GIS Prediction Map view
        switchView("map");

        // Sync active map layer button state if present
        const layerBtn = document.querySelector(`.map-layer-btn[data-layer="${hazardKey.toLowerCase()}"]`);
        if (layerBtn) {
          document.querySelectorAll(".map-layer-btn").forEach(b => b.classList.remove("map-layer-btn-active"));
          layerBtn.classList.add("map-layer-btn-active");
        }

        showToast("GIS PREDICTION MAP", `Opened ${hazardKey} Live GIS Prediction Map`, "CYAN");
      } else if (action === "precaution") {
        state.selectedHazard = hazardKey;

        // Switch directly to AI Safety Advisor & Precautions view for that hazard
        switchView("precautions");
        renderPrecautionsView(hazardKey);

        showToast("SAFETY ADVISOR", `Opened ${hazardKey} AI Precautions & Action Plan`, "CYAN");
      }
    });
  });

  document.querySelectorAll(".landing-feature-card").forEach(card => {
    card.addEventListener("click", (e) => {
      if (e.target.closest(".card-action-btn")) return;
      const hazardKey = card.dataset.hazardFeature;
      if (!hazardKey) return;
      state.selectedHazard = hazardKey;
      state.activeMapLayer = hazardKey.toLowerCase();

      switchView("map");
      showToast("HAZARD PREDICTION", `Opened ${hazardKey} Live GIS Prediction Map`, "CYAN");
    });
  });

  // Initialize Map on tab switch or dashboard load
  let mapInitialized = false;

  // View Switcher Function
  function switchView(targetView) {
    state.currentView = targetView;
    window.currentView = targetView;

    // Toggle Landing vs Dashboard Layout
    if (targetView === "landing") {
      document.getElementById("app-header").classList.add("hidden");
      document.getElementById("app-main-container").classList.add("hidden");
      views.landing.classList.remove("hidden");
      return;
    }

    document.getElementById("app-header").classList.remove("hidden");
    document.getElementById("app-main-container").classList.remove("hidden");
    views.landing.classList.add("hidden");

    // Hide all main views
    Object.keys(views).forEach(k => {
      if (k !== "landing" && views[k]) {
        views[k].classList.add("hidden");
      }
    });

    // Show active target view
    if (views[targetView]) {
      views[targetView].classList.remove("hidden");
    }

    // Active Tab Highlight in Header
    document.querySelectorAll(".nav-link").forEach(link => {
      if (link.dataset.view === targetView) {
        link.classList.add("text-cyan-400", "border-b-2", "border-cyan-400", "font-semibold");
        link.classList.remove("text-gray-400");
      } else {
        link.classList.remove("text-cyan-400", "border-b-2", "border-cyan-400", "font-semibold");
        link.classList.add("text-gray-400");
      }
    });

    // Initialize components based on view
    if ((targetView === "dashboard" || targetView === "map") && !mapInitialized) {
      setTimeout(() => {
        initGISMap();
        mapInitialized = true;
      }, 100);
    } else if (targetView === "map" && state.map) {
      setTimeout(() => state.map.invalidateSize(), 150);
    }

    if (targetView === "analytics") {
      renderAnalyticsCharts();
    }
    if (targetView === "precautions") {
      renderPrecautionsView(state.selectedHazard);
    }
    if (targetView === "eoc") {
      renderEOCView();
    }
    if (targetView === "alerts") {
      renderAlertsView();
    }
    if (targetView === "mysafety") {
      renderMySafetyView();
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  window.switchAppView = switchView;

  // Populate Location Dropdown
  function populateLocationSelector(locList) {
    const sel = document.getElementById("location-selector");
    sel.innerHTML = "";
    locList.forEach(l => {
      const opt = document.createElement("option");
      opt.value = l.id;
      opt.textContent = `${l.name} (${l.currentRisk})`;
      sel.appendChild(opt);
    });
    sel.value = state.selectedLocationId;
    updateDashboardForLocation(state.selectedLocationId);
  }

  // Handle Location Change
  async function handleLocationChange(locId) {
    state.selectedLocationId = locId;

    if (locId === "gps-current") {
      if (state.gpsLocationData) {
        updateDashboardForGps(state.gpsLocationData);
        if (state.map) {
          state.map.setView([state.gpsLocationData.lat, state.gpsLocationData.lng], 11);
        }
      } else {
        detectUserLocation();
      }
      return;
    }

    // Hide GPS status badge and coordinates display when selecting predefined city
    const statusBadge = document.getElementById("gps-status-badge");
    if (statusBadge) statusBadge.classList.add("hidden");

    const coordsDisplay = document.getElementById("gps-coords-display");
    if (coordsDisplay) coordsDisplay.classList.add("hidden");

    updateDashboardForLocation(locId);

    // Pan map if initialized
    const loc = ALERTORA_DATA.locations.find(l => l.id === locId);
    if (loc && state.map) {
      state.map.flyTo([loc.lat, loc.lng], 10, { animate: true, duration: 1.2 });
    }
  }

  // Reverse Geocoding Helper to resolve Place Name
  async function getPlaceNameFromCoords(lat, lng) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=10`, {
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      if (res.ok) {
        const data = await res.json();
        const addr = data.address || {};
        const place = addr.city || addr.town || addr.village || addr.suburb || addr.county || addr.district || data.name;
        const stateName = addr.state || addr.country;
        if (place && stateName) return `${place}, ${stateName}`;
        if (place) return place;
      }
    } catch (e) {
      console.log("Reverse geocode fallback.");
    }

    if (Math.abs(lat - 13.08) < 0.3 && Math.abs(lng - 80.27) < 0.3) return "Chennai, Tamil Nadu";
    if (Math.abs(lat - 13.14) < 0.4 && Math.abs(lng - 79.90) < 0.4) return "Tiruvallur, Tamil Nadu";
    if (Math.abs(lat - 12.83) < 0.4 && Math.abs(lng - 79.70) < 0.4) return "Kanchipuram, Tamil Nadu";
    if (Math.abs(lat - 11.01) < 0.5 && Math.abs(lng - 76.95) < 0.5) return "Coimbatore, Tamil Nadu";
    if (Math.abs(lat - 9.92) < 0.5 && Math.abs(lng - 78.11) < 0.5) return "Madurai, Tamil Nadu";

    return `Detected Region (${lat.toFixed(2)}°N, ${lng.toFixed(2)}°E)`;
  }

  // Detect User GPS Location
  function detectUserLocation() {
    if (!navigator.geolocation) {
      showToast("Location Unsupported", "Your browser does not support location detection.", "RED");
      return;
    }

    const btnHeader = document.getElementById("btn-gps-text");
    const btnLanding = document.getElementById("btn-landing-gps-text");

    const setButtonText = (htmlText) => {
      if (btnHeader) btnHeader.innerHTML = htmlText;
      if (btnLanding) btnLanding.innerHTML = htmlText;
    };

    // Step 1: Loading state: ⌖ Detecting...
    setButtonText(`<span class="inline-block w-2 h-2 rounded-full bg-cyan-400 mr-1 animate-ping"></span><span>Detecting...</span>`);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;

        setButtonText(`<span class="inline-block w-2 h-2 rounded-full bg-blue-400 mr-1 animate-ping"></span><span>Loading...</span>`);

        try {
          // Resolve place name from coordinates
          const placeName = await getPlaceNameFromCoords(lat, lng);

          // Generate/Fetch weather predictions for coordinates
          const gpsLocObj = generateGpsLocationObject(lat, lng, placeName);
          state.gpsLocationData = gpsLocObj;
          state.selectedLocationId = "gps-current";

          // Populate/update GPS option in location selector dropdown
          const sel = document.getElementById("location-selector");
          let gpsOpt = sel.querySelector('option[value="gps-current"]');
          if (!gpsOpt) {
            gpsOpt = document.createElement("option");
            gpsOpt.value = "gps-current";
            sel.insertBefore(gpsOpt, sel.firstChild);
          }
          gpsOpt.textContent = `⌖ ${placeName} (${lat.toFixed(2)}°, ${lng.toFixed(2)}°)`;
          sel.value = "gps-current";

          // Update Dashboard UI with detected location info & lat/lng
          updateDashboardForGps(gpsLocObj);

          // Move Leaflet map and add/update single GPS marker
          updateLeafletMapForGps(lat, lng, placeName);

          // Step 3: Success state: ✓ Location Found
          setButtonText(`✓ Location Found`);
          showToast("⌖ LOCATION DETECTED", `${placeName} (${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E)`, "CYAN");

          setTimeout(() => {
            setButtonText(`<svg class="w-3.5 h-3.5 text-cyan-400 fill-current inline-block mr-1" viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg><span>My Location</span>`);
          }, 3500);

        } catch (err) {
          console.error("GPS Weather data error:", err);
          setButtonText(`<svg class="w-3.5 h-3.5 text-cyan-400 fill-current inline-block mr-1" viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg><span>Use My Current Location</span>`);
          showToast("Weather API Error", "Location detected, but weather data could not be loaded.", "RED");
        }
      },
      (error) => {
        setButtonText(`<svg class="w-3.5 h-3.5 text-cyan-400 fill-current inline-block mr-1" viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg><span>Use My Current Location</span>`);
        let msg = "Unable to detect your current location. Please try again.";
        if (error.code === error.PERMISSION_DENIED) {
          msg = "Location permission denied. Please allow location access to use this feature.";
        } else if (error.code === error.POSITION_UNAVAILABLE) {
          msg = "Unable to detect your current location. Please try again.";
        } else if (error.code === error.TIMEOUT) {
          msg = "Location request timed out. Please try again.";
        }
        showToast("Location Error", msg, "RED");
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
    );
  }

  // Generate Weather & Predictions for Detected Coordinates
  function generateGpsLocationObject(lat, lng, placeName = "Detected Location") {
    const latStr = lat.toFixed(4);
    const lngStr = lng.toFixed(4);

    const seed = Math.abs(Math.sin(lat * 100 + lng * 50));
    const thunderstormProb = Math.floor(65 + seed * 30);
    const hailProb = Math.floor(20 + seed * 25);
    const cloudburstProb = Math.floor(45 + seed * 35);
    const lightningProb = Math.floor(70 + seed * 25);

    const riskLevel = thunderstormProb > 85 ? "EXTREME" : (thunderstormProb > 70 ? "HIGH" : "MODERATE");

    return {
      id: "gps-current",
      name: `⌖ ${placeName}`,
      placeName: placeName,
      district: `${placeName} (${latStr}° N, ${lngStr}° E)`,
      state: placeName,
      lat: lat,
      lng: lng,
      currentRisk: riskLevel,
      temp: Number((28.5 + seed * 5).toFixed(1)),
      humidity: Math.floor(78 + seed * 18),
      windSpeed: Math.floor(28 + seed * 22),
      pressure: 1003.8,
      rainfallRate: Math.floor(35 + seed * 45),
      nextHazardETA: "00h 35m",
      nextHazardType: "Convective Cell & Rain",
      nowcast: [
        { hour: "NOW", time: "NOW", thunderstorm: thunderstormProb, hail: hailProb, cloudburst: cloudburstProb, lightning: lightningProb, rainfall: Math.floor(35 + seed * 45), wind: Math.floor(28 + seed * 22) },
        { hour: "+1 HR", time: "+1H", thunderstorm: Math.min(100, thunderstormProb + 8), hail: Math.min(100, hailProb + 12), cloudburst: Math.min(100, cloudburstProb + 10), lightning: Math.min(100, lightningProb + 6), rainfall: Math.floor(55 + seed * 45), wind: Math.floor(38 + seed * 22) },
        { hour: "+2 HR", time: "+2H", thunderstorm: Math.max(20, thunderstormProb - 10), hail: Math.max(10, hailProb - 10), cloudburst: Math.max(15, cloudburstProb - 15), lightning: Math.max(20, lightningProb - 15), rainfall: 30, wind: 25 },
        { hour: "+3 HR", time: "+3H", thunderstorm: Math.max(15, thunderstormProb - 30), hail: 10, cloudburst: 15, lightning: 30, rainfall: 15, wind: 20 },
        { hour: "+4 HR", time: "+4H", thunderstorm: 30, hail: 5, cloudburst: 10, lightning: 20, rainfall: 10, wind: 15 },
        { hour: "+5 HR", time: "+5H", thunderstorm: 20, hail: 2, cloudburst: 5, lightning: 15, rainfall: 5, wind: 12 },
        { hour: "+6 HR", time: "+6H", thunderstorm: 12, hail: 0, cloudburst: 2, lightning: 8, rainfall: 2, wind: 10 }
      ]
    };
  }

  // Update Dashboard UI Elements for GPS Location
  function updateDashboardForGps(gpsLoc) {
    document.getElementById("location-name-display").textContent = gpsLoc.name;
    document.getElementById("metric-temp").textContent = `${gpsLoc.temp}°C`;
    document.getElementById("metric-humidity").textContent = `${gpsLoc.humidity}%`;
    document.getElementById("metric-wind").textContent = `${gpsLoc.windSpeed} km/h`;
    document.getElementById("metric-rain").textContent = `${gpsLoc.rainfallRate} mm/h`;

    const riskBadge = document.getElementById("metric-risk-badge");
    riskBadge.textContent = gpsLoc.currentRisk;
    riskBadge.className = `px-3 py-1 rounded-full text-xs font-bold font-mono uppercase border ${getRiskBadgeClass(gpsLoc.currentRisk)}`;

    document.getElementById("countdown-location").textContent = `⌖ ${gpsLoc.placeName} (${gpsLoc.lat.toFixed(4)}° N, ${gpsLoc.lng.toFixed(4)}° E)`;
    document.getElementById("countdown-hazard-type").textContent = gpsLoc.nextHazardType;

    // Show GPS status badge and coordinates display
    const statusBadge = document.getElementById("gps-status-badge");
    if (statusBadge) statusBadge.classList.remove("hidden");

    const coordsDisplay = document.getElementById("gps-coords-display");
    if (coordsDisplay) {
      coordsDisplay.classList.remove("hidden");
      const placeEl = document.getElementById("gps-place-name");
      if (placeEl) placeEl.textContent = gpsLoc.placeName;
      document.getElementById("gps-lat").textContent = gpsLoc.lat.toFixed(4);
      document.getElementById("gps-lng").textContent = gpsLoc.lng.toFixed(4);
    }

    // Populate Landing Page Front Page GPS Info Card
    const landingGpsCard = document.getElementById("landing-gps-info");
    if (landingGpsCard) {
      landingGpsCard.classList.remove("hidden");
      const placeLanding = document.getElementById("landing-gps-place");
      if (placeLanding) placeLanding.textContent = gpsLoc.placeName;

      const latLanding = document.getElementById("landing-gps-lat");
      if (latLanding) latLanding.textContent = gpsLoc.lat.toFixed(4);

      const lngLanding = document.getElementById("landing-gps-lng");
      if (lngLanding) lngLanding.textContent = gpsLoc.lng.toFixed(4);

      const riskLanding = document.getElementById("landing-gps-risk");
      if (riskLanding) {
        riskLanding.textContent = `${gpsLoc.currentRisk} RISK`;
        riskLanding.className = `px-2 py-0.5 rounded text-[10px] font-bold font-mono ${getRiskBadgeClass(gpsLoc.currentRisk)}`;
      }

      const stormLanding = document.getElementById("landing-gps-thunderstorm");
      if (stormLanding) stormLanding.textContent = `${gpsLoc.nowcast[0].thunderstorm}%`;

      const cloudLanding = document.getElementById("landing-gps-cloudburst");
      if (cloudLanding) cloudLanding.textContent = `${gpsLoc.nowcast[0].cloudburst}%`;
    }

    renderNowcastTimeline(gpsLoc.nowcast);
    renderHazardCards(gpsLoc);
    renderXAIPanel();
    updateHeaderNowcastData(gpsLoc);

    if (state.currentView === "mysafety") {
      renderMySafetyView();
    }
  }

  // Update Leaflet Map for GPS Position
  function updateLeafletMapForGps(lat, lng, placeName = "Your Current Location") {
    if (!state.map) return;

    // Move existing Leaflet map to user's coordinates (zoom level 11 per requirement)
    state.map.setView([lat, lng], 11, { animate: true });

    // Single Marker logic: Do NOT create duplicate markers on multiple clicks!
    if (state.userLocationMarker) {
      state.userLocationMarker.setLatLng([lat, lng]);
    } else {
      const gpsIcon = L.divIcon({
        className: 'custom-user-gps-marker',
        html: `<div class="relative flex items-center justify-center">
                <span class="animate-ping absolute inline-flex h-8 w-8 rounded-full bg-cyan-400 opacity-75"></span>
                <div style="background-color:#06b6d4; width:20px; height:20px; border-radius:50%; border:3px solid white; box-shadow:0 0 15px #06b6d4" class="relative"></div>
               </div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });

      state.userLocationMarker = L.marker([lat, lng], { icon: gpsIcon }).addTo(state.map);
    }

    state.userLocationMarker.bindPopup(`
      <div class="p-2 min-w-[200px] font-mono">
        <div class="font-bold text-sm text-cyan-400 border-b border-slate-700 pb-1 mb-1">⌖ ${placeName}</div>
        <div class="text-xs text-gray-300">Latitude: ${lat.toFixed(4)}° N<br>Longitude: ${lng.toFixed(4)}° E</div>
        <div class="text-[10px] text-emerald-400 font-bold mt-1.5">✓ Live GPS Position Active</div>
      </div>
    `).openPopup();
  }

  // Update UI Elements with Selected Location Data
  function updateDashboardForLocation(locId) {
    const loc = ALERTORA_DATA.locations.find(l => l.id === locId) || ALERTORA_DATA.locations[0];

    // Current metrics
    document.getElementById("location-name-display").textContent = loc.name;
    document.getElementById("metric-temp").textContent = `${loc.temp}°C`;
    document.getElementById("metric-humidity").textContent = `${loc.humidity}%`;
    document.getElementById("metric-wind").textContent = `${loc.windSpeed} km/h`;
    document.getElementById("metric-rain").textContent = `${loc.rainfallRate} mm/h`;
    
    // Risk Badge
    const riskBadge = document.getElementById("metric-risk-badge");
    riskBadge.textContent = loc.currentRisk;
    riskBadge.className = `px-3 py-1 rounded-full text-xs font-bold font-mono uppercase border ${getRiskBadgeClass(loc.currentRisk)}`;

    // ETA & Next Event
    document.getElementById("countdown-location").textContent = loc.name;
    document.getElementById("countdown-hazard-type").textContent = loc.nextHazardType;

    // Render AI Nowcast Timeline
    renderNowcastTimeline(loc.nowcast);

    // Render Hazards Summary Cards
    renderHazardCards(loc);

    // Render XAI Panel
    renderXAIPanel();

    // Update Header Live Nowcast Strip
    updateHeaderNowcastData(loc);

    // If MySafety view is active, update it
    if (state.currentView === "mysafety") {
      renderMySafetyView();
    }
  }

  // Helper for Risk Badge Classes
  function getRiskBadgeClass(risk) {
    switch (risk) {
      case "EXTREME": return "bg-red-950/60 text-red-400 border-red-500/50 animate-pulse-red";
      case "HIGH": return "bg-orange-950/60 text-orange-400 border-orange-500/50";
      case "MODERATE": return "bg-yellow-950/60 text-yellow-400 border-yellow-500/50";
      default: return "bg-emerald-950/60 text-emerald-400 border-emerald-500/50";
    }
  }

  // Render AI Nowcast Timeline (0-6 Hours)
  function renderNowcastTimeline(nowcastData) {
    const timelineContainer = document.getElementById("nowcast-timeline-bars");
    const hourSelectorContainer = document.getElementById("nowcast-hour-buttons");

    if (!timelineContainer || !hourSelectorContainer) return;

    hourSelectorContainer.innerHTML = "";
    nowcastData.forEach((item, idx) => {
      const btn = document.createElement("button");
      btn.className = `px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
        idx === state.selectedTimelineHourIndex
          ? "bg-cyan-500 text-black shadow-lg shadow-cyan-500/30"
          : "bg-slate-800/80 text-gray-300 hover:bg-slate-700"
      }`;
      btn.innerHTML = `<span class="block text-[10px] opacity-75">${item.time}</span>${item.hour}`;
      btn.addEventListener("click", () => {
        state.selectedTimelineHourIndex = idx;
        renderNowcastTimeline(nowcastData);
      });
      hourSelectorContainer.appendChild(btn);
    });

    const activeItem = nowcastData[state.selectedTimelineHourIndex] || nowcastData[0];

    timelineContainer.innerHTML = `
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div class="glass-panel p-3 rounded-lg border-slate-800">
          <div class="text-xs text-gray-400">Thunderstorm</div>
          <div class="text-2xl font-bold font-mono text-cyan-400 mt-1">${activeItem.thunderstorm}%</div>
          <div class="w-full bg-slate-800 rounded-full h-1.5 mt-2">
            <div class="bg-cyan-400 h-1.5 rounded-full" style="width: ${activeItem.thunderstorm}%"></div>
          </div>
        </div>

        <div class="glass-panel p-3 rounded-lg border-slate-800">
          <div class="text-xs text-gray-400">Hail Prob.</div>
          <div class="text-2xl font-bold font-mono text-amber-400 mt-1">${activeItem.hail}%</div>
          <div class="w-full bg-slate-800 rounded-full h-1.5 mt-2">
            <div class="bg-amber-400 h-1.5 rounded-full" style="width: ${activeItem.hail}%"></div>
          </div>
        </div>

        <div class="glass-panel p-3 rounded-lg border-slate-800">
          <div class="text-xs text-gray-400">Cloudburst Risk</div>
          <div class="text-2xl font-bold font-mono text-orange-400 mt-1">${activeItem.cloudburst}%</div>
          <div class="w-full bg-slate-800 rounded-full h-1.5 mt-2">
            <div class="bg-orange-400 h-1.5 rounded-full" style="width: ${activeItem.cloudburst}%"></div>
          </div>
        </div>

        <div class="glass-panel p-3 rounded-lg border-slate-800">
          <div class="text-xs text-gray-400">Lightning Strikes</div>
          <div class="text-2xl font-bold font-mono text-red-400 mt-1">${activeItem.lightning}%</div>
          <div class="w-full bg-slate-800 rounded-full h-1.5 mt-2">
            <div class="bg-red-400 h-1.5 rounded-full" style="width: ${activeItem.lightning}%"></div>
          </div>
        </div>

        <div class="glass-panel p-3 rounded-lg border-slate-800">
          <div class="text-xs text-gray-400">Rain Intensity</div>
          <div class="text-2xl font-bold font-mono text-blue-400 mt-1">${activeItem.rainfall} <span class="text-xs font-normal">mm/h</span></div>
          <div class="w-full bg-slate-800 rounded-full h-1.5 mt-2">
            <div class="bg-blue-400 h-1.5 rounded-full" style="width: ${Math.min(100, activeItem.rainfall)}%"></div>
          </div>
        </div>

        <div class="glass-panel p-3 rounded-lg border-slate-800">
          <div class="text-xs text-gray-400">Downburst Wind</div>
          <div class="text-2xl font-bold font-mono text-indigo-400 mt-1">${activeItem.wind} <span class="text-xs font-normal">km/h</span></div>
          <div class="w-full bg-slate-800 rounded-full h-1.5 mt-2">
            <div class="bg-indigo-400 h-1.5 rounded-full" style="width: ${Math.min(100, activeItem.wind * 1.2)}%"></div>
          </div>
        </div>
      </div>
    `;
  }

  // Render 4 Hazard Cards
  function renderHazardCards(loc) {
    const container = document.getElementById("severe-hazard-cards");
    if (!container) return;

    const hazards = ALERTORA_DATA.hazardsSummary;
    container.innerHTML = "";

    hazards.forEach(h => {
      const card = document.createElement("div");
      card.className = "glass-panel p-4 rounded-xl glass-card-interactive flex flex-col justify-between cursor-pointer border-slate-800 hover:border-cyan-500/40";
      card.addEventListener("click", () => {
        state.selectedHazard = h.id.toUpperCase();
        switchView("precautions");
      });

      card.innerHTML = `
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-2xl">${h.icon}</span>
            <span class="px-2 py-0.5 rounded text-[11px] font-bold font-mono uppercase ${getRiskBadgeClass(h.riskLevel)}">${h.riskLevel}</span>
          </div>
          <h4 class="text-sm font-bold text-gray-200 tracking-wide uppercase font-mono">${h.title}</h4>
          <p class="text-xs text-gray-400 mt-1">${h.description}</p>
        </div>

        <div class="mt-4 pt-3 border-t border-slate-800/80 flex items-end justify-between">
          <div>
            <div class="text-[10px] text-gray-400 uppercase font-mono">AI Probability</div>
            <div class="text-2xl font-bold font-mono glow-cyan" style="color: ${h.color}">${h.probability}%</div>
          </div>
          <div class="text-right">
            <div class="text-[10px] text-gray-400 uppercase font-mono">Expected ETA</div>
            <div class="text-sm font-semibold font-mono text-gray-200">${h.eta}</div>
          </div>
        </div>
      `;
      container.appendChild(card);
    });
  }

  // Render Explainable AI Factor Contributions
  function renderXAIPanel() {
    const container = document.getElementById("xai-factors-container");
    if (!container) return;

    container.innerHTML = "";
    ALERTORA_DATA.xaiFactors.forEach(f => {
      const row = document.createElement("div");
      row.className = "mb-3";
      row.innerHTML = `
        <div class="flex justify-between text-xs mb-1">
          <span class="text-gray-300 font-medium">${f.factor}</span>
          <span class="font-mono text-cyan-400 font-bold">+${f.weight}% Contribution</span>
        </div>
        <div class="w-full bg-slate-800 rounded-full h-2">
          <div class="bg-gradient-to-r from-cyan-500 to-blue-500 h-2 rounded-full" style="width: ${f.weight * 2.5}%"></div>
        </div>
        <div class="text-[10px] text-gray-400 mt-0.5">${f.description}</div>
      `;
      container.appendChild(row);
    });
  }

  // Initialize GIS Interactive Map (Leaflet)
  function initGISMap() {
    const mapElement = document.getElementById("gis-map-container");
    if (!mapElement || state.map) return;

    // Create Leaflet Map centered on Chennai / Tamil Nadu
    state.map = L.map("gis-map-container", {
      center: [13.0827, 80.2707],
      zoom: 9,
      zoomControl: true
    });

    // Dark Map Tile Layer (CartoDB Dark Matter)
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?key=cb1_2yvu_1_f62f658f13e311deee9199e7", {
      attribution: '&copy; OpenStreetMap, &copy; CARTO',
      subdomains: "abcd",
      maxZoom: 20
    }).addTo(state.map);

    // Render Location Markers & Risk Polygons
    renderMapOverlays();

    // Map Click Listener to pick custom coordinates
    state.map.on("click", (e) => {
      const { lat, lng } = e.latlng;
      openCustomLocationModal(lat.toFixed(4), lng.toFixed(4));
    });

    // Layer Controls Event Listeners (All 4 Buttons get glowing lighting effect when active)
    document.querySelectorAll(".map-layer-btn").forEach(btn => {
      btn.addEventListener("click", (e) => {
        document.querySelectorAll(".map-layer-btn").forEach(b => {
          b.classList.remove("map-layer-btn-active");
        });
        btn.classList.add("map-layer-btn-active");
        state.activeMapLayer = btn.dataset.layer;
        updateMapLayers();
      });
    });
  }

  // Render Map Overlays & Risk Polygons
  function renderMapOverlays() {
    if (!state.map) return;

    // Simulated Storm Radar Circle Overlay
    state.radarOverlay = L.circle([13.12, 80.18], {
      color: "#ef4444",
      fillColor: "#ef4444",
      fillOpacity: 0.35,
      radius: 28000
    }).addTo(state.map);
    state.radarOverlay.bindTooltip("<b>Storm Core Active</b><br>Reflectivity: 54.2 dBZ", { permanent: false, direction: "top" });

    // Secondary Moderate Risk Polygon
    const polygon = L.polygon([
      [13.25, 79.85],
      [13.40, 80.15],
      [13.10, 80.35],
      [12.90, 80.05]
    ], {
      color: "#f97316",
      fillColor: "#f97316",
      fillOpacity: 0.2
    }).addTo(state.map);
    polygon.bindTooltip("<b>High Convective Risk Zone</b><br>0-6 Hr Forecast Area", { permanent: false });

    // Markers for all Tamil Nadu locations
    ALERTORA_DATA.locations.forEach(loc => {
      const markerColor = loc.currentRisk === "EXTREME" ? "#ef4444" : (loc.currentRisk === "HIGH" ? "#f97316" : "#f59e0b");
      
      const customIcon = L.divIcon({
        className: 'custom-map-pin',
        html: `<div style="background-color:${markerColor}; width:16px; height:16px; border-radius:50%; border:2px solid white; box-shadow:0 0 10px ${markerColor}"></div>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8]
      });

      const marker = L.marker([loc.lat, loc.lng], { icon: customIcon }).addTo(state.map);

      const popupContent = `
        <div class="p-2 min-w-[200px]">
          <div class="flex items-center justify-between border-b border-slate-700 pb-1 mb-2">
            <span class="font-bold text-sm text-cyan-400 font-mono">${loc.name}</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${getRiskBadgeClass(loc.currentRisk)}">${loc.currentRisk}</span>
          </div>
          <div class="text-xs space-y-1 text-gray-300">
            <div><b>Temp:</b> ${loc.temp}°C | <b>Humidity:</b> ${loc.humidity}%</div>
            <div><b>Rain Intensity:</b> ${loc.rainfallRate} mm/hr</div>
            <div><b>Next Storm ETA:</b> <span class="text-amber-400 font-mono font-bold">${loc.nextHazardETA}</span></div>
          </div>
          <button onclick="window.selectLocationFromMap('${loc.id}')" class="mt-3 w-full bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-bold py-1 px-2 rounded transition">
            View Full Nowcast & Precautions
          </button>
        </div>
      `;

      marker.bindPopup(popupContent);
    });
  }

  // Global Map Selection Helper
  window.selectLocationFromMap = function(locId) {
    document.getElementById("location-selector").value = locId;
    handleLocationChange(locId);
    switchView("dashboard");
  };

  // Update Layer Filter Effects
  function updateMapLayers() {
    if (!state.radarOverlay) return;
    const layer = state.activeMapLayer;

    if (layer === "lightning") {
      state.radarOverlay.setStyle({ fillColor: "#3b82f6", color: "#3b82f6", fillOpacity: 0.45 });
      state.radarOverlay.unbindTooltip();
      state.radarOverlay.bindTooltip("<b>⚡ High Lightning Density Zone</b><br>34 Strikes / km² / hr", { permanent: false, direction: "top" });
    } else if (layer === "cloudburst") {
      state.radarOverlay.setStyle({ fillColor: "#ef4444", color: "#ef4444", fillOpacity: 0.5 });
      state.radarOverlay.unbindTooltip();
      state.radarOverlay.bindTooltip("<b>🌧 Extreme Cloudburst Cell</b><br>Rainfall Rate: 85 mm/hr", { permanent: false, direction: "top" });
    } else if (layer === "hail") {
      state.radarOverlay.setStyle({ fillColor: "#f59e0b", color: "#f59e0b", fillOpacity: 0.45 });
      state.radarOverlay.unbindTooltip();
      state.radarOverlay.bindTooltip("<b>🧊 Hailstorm Core Active</b><br>Freezing Height: 4.2km", { permanent: false, direction: "top" });
    } else {
      state.radarOverlay.setStyle({ fillColor: "#06b6d4", color: "#06b6d4", fillOpacity: 0.35 });
      state.radarOverlay.unbindTooltip();
      state.radarOverlay.bindTooltip("<b>📡 Doppler Weather Radar Core</b><br>Reflectivity: 54.2 dBZ", { permanent: false, direction: "top" });
    }
  }

  // Open Custom Coordinate Location Drawer
  function openCustomLocationModal(lat, lng) {
    const modal = document.getElementById("location-profile-modal");
    if (!modal) return;

    document.getElementById("modal-coords").textContent = `Lat: ${lat}°N, Lng: ${lng}°E`;
    document.getElementById("modal-sim-temp").textContent = `${(28 + Math.random() * 5).toFixed(1)}°C`;
    document.getElementById("modal-sim-humidity").textContent = `${Math.floor(75 + Math.random() * 20)}%`;
    document.getElementById("modal-sim-prob").textContent = `${Math.floor(65 + Math.random() * 30)}%`;
    modal.classList.remove("hidden");

    document.getElementById("btn-close-loc-modal").onclick = () => modal.classList.add("hidden");
  }

  // Start Live Ticking Storm Countdown Timer
  function startCountdownTimer() {
    if (state.countdownInterval) clearInterval(state.countdownInterval);

    state.countdownInterval = setInterval(() => {
      if (state.countdownSeconds <= 0) {
        state.countdownSeconds = 7200; // Reset loop
      }
      state.countdownSeconds--;

      const hrs = Math.floor(state.countdownSeconds / 3600);
      const mins = Math.floor((state.countdownSeconds % 3600) / 60);
      const secs = state.countdownSeconds % 60;

      const pad = (n) => String(n).padStart(2, '0');
      document.getElementById("timer-hours").textContent = pad(hrs);
      document.getElementById("timer-minutes").textContent = pad(mins);
      document.getElementById("timer-seconds").textContent = pad(secs);

      // Simple mode countdown
      const timerSimple = document.getElementById("timer-simple-display");
      if (timerSimple) {
        timerSimple.textContent = `${pad(hrs)}:${pad(mins)}:${pad(secs)}`;
      }
    }, 1000);
  }

  // Interactive Demo Storm Simulation Loop
  function toggleStormSimulation() {
    const btn = document.getElementById("btn-sim-storm");
    const statusBadge = document.getElementById("header-status-badge");
    const statusText = document.getElementById("header-status-text");
    const simIndicator = document.getElementById("strip-sim-indicator");

    if (state.stormSimulationActive) {
      clearInterval(state.stormSimulationInterval);
      state.stormSimulationActive = false;

      if (btn) {
        btn.innerHTML = `<span>DEMO MODE</span>`;
        btn.className = "bg-slate-900/90 hover:bg-slate-800 text-cyan-300 border border-cyan-500/40 text-xs font-bold font-mono px-3 py-1.5 rounded-lg transition flex items-center shadow-sm shadow-cyan-500/10";
      }

      if (statusBadge) {
        statusBadge.className = "px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-950/90 text-emerald-400 border border-emerald-500/40 flex items-center shadow-sm shadow-emerald-500/20";
        if (statusText) statusText.textContent = "SYSTEM ONLINE";
      }
      if (simIndicator) simIndicator.classList.add("hidden");

      showToast("Simulation Paused", "Storm trajectory simulation has been paused.");
    } else {
      state.stormSimulationActive = true;

      if (btn) {
        btn.innerHTML = `<span>STOP SIMULATION</span>`;
        btn.className = "bg-amber-950/90 text-amber-300 border border-amber-500/50 text-xs font-bold font-mono px-3 py-1.5 rounded-lg transition flex items-center shadow-lg shadow-amber-500/20 animate-pulse";
      }

      if (statusBadge) {
        statusBadge.className = "px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950/90 text-amber-400 border border-amber-500/50 flex items-center shadow-sm shadow-amber-500/20";
        if (statusText) statusText.textContent = "DEMO / SIMULATED";
      }
      if (simIndicator) simIndicator.classList.remove("hidden");

      showToast("⛈ STORM SIMULATION RUNNING", "Simulating storm movement across Tamil Nadu over 6 hours.");

      let simStep = 0;
      state.stormSimulationInterval = setInterval(() => {
        simStep++;
        
        // Move storm circle overlay
        if (state.radarOverlay && state.map) {
          const currentCenter = state.radarOverlay.getLatLng();
          state.radarOverlay.setLatLng([currentCenter.lat + 0.005, currentCenter.lng + 0.008]);
          state.radarOverlay.setRadius(28000 + (simStep * 1500));
        }

        // Dynamically update nowcast hazard values
        const currentLoc = (state.selectedLocationId === "gps-current" && state.gpsLocationData) 
          ? state.gpsLocationData 
          : ALERTORA_DATA.locations.find(l => l.id === state.selectedLocationId);

        if (currentLoc && currentLoc.nowcast) {
          currentLoc.nowcast.forEach(item => {
            item.thunderstorm = Math.min(100, item.thunderstorm + Math.floor(Math.random() * 5));
            item.lightning = Math.min(100, item.lightning + Math.floor(Math.random() * 6));
          });
          renderNowcastTimeline(currentLoc.nowcast);
          updateHeaderNowcastData(currentLoc);
        }

        // Show live warning notification at step 3
        if (simStep === 3) {
          showToast("🔴 EMERGENCY ALERT GENERATED", "Tiruvallur District: Hail & Lightning strike density exceeded threshold!", "RED");
          playAlertTone();
        }
      }, 2500);
    }
  }

  // Audio Warning Feedback Generator
  function playAlertTone() {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(880, audioCtx.currentTime); // A5
      gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.4);
    } catch (e) {
      console.log("Audio play blocked by browser policy.");
    }
  }

  // Render AI Safety Precautions View
  function renderPrecautionsView(hazardKey) {
    const hazardData = ALERTORA_DATA.precautionsDatabase[hazardKey] || ALERTORA_DATA.precautionsDatabase["THUNDERSTORM"];

    // Update buttons active state
    document.querySelectorAll(".precaution-hazard-btn").forEach(btn => {
      if (btn.dataset.hazard === hazardKey) {
        btn.classList.add("bg-cyan-500", "text-black", "font-bold");
        btn.classList.remove("bg-slate-800", "text-gray-300");
      } else {
        btn.classList.remove("bg-cyan-500", "text-black", "font-bold");
        btn.classList.add("bg-slate-800", "text-gray-300");
      }
    });

    document.getElementById("precaution-hazard-title").textContent = hazardData.hazard;

    // Render Govt Precautions
    const govtContainer = document.getElementById("precautions-govt-list");
    govtContainer.innerHTML = "";
    hazardData.government.forEach((item, i) => {
      const li = document.createElement("li");
      li.className = "flex items-start space-x-3 text-sm text-gray-300";
      li.innerHTML = `
        <span class="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-950 border border-cyan-500/40 text-cyan-400 font-bold text-xs flex items-center justify-center font-mono">${i + 1}</span>
        <span>${item}</span>
      `;
      govtContainer.appendChild(li);
    });

    // Render Public Precautions
    const publicContainer = document.getElementById("precautions-public-list");
    publicContainer.innerHTML = "";
    hazardData.public.forEach((item, i) => {
      const li = document.createElement("li");
      li.className = "flex items-start space-x-3 text-sm text-gray-300";
      li.innerHTML = `
        <span class="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-950 border border-emerald-500/40 text-emerald-400 font-bold text-xs flex items-center justify-center font-mono">✓</span>
        <span>${item}</span>
      `;
      publicContainer.appendChild(li);
    });
  }

  // Render Emergency Alerts View
  function renderAlertsView() {
    const container = document.getElementById("alerts-feed-container");
    if (!container) return;

    container.innerHTML = "";
    ALERTORA_DATA.alertsFeed.forEach(alert => {
      const alertCard = document.createElement("div");
      const borderClass = alert.severity === "RED" ? "border-red-500/60 bg-red-950/20" : (alert.severity === "ORANGE" ? "border-orange-500/50 bg-orange-950/20" : "border-yellow-500/40 bg-yellow-950/20");
      
      alertCard.className = `glass-panel p-5 rounded-xl border-l-4 ${borderClass} mb-4`;
      alertCard.innerHTML = `
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-3">
          <div class="flex items-center space-x-3">
            <span class="px-2.5 py-1 rounded text-xs font-bold font-mono uppercase ${getRiskBadgeClass(alert.severity)}">${alert.severity} ALERT</span>
            <h3 class="text-base font-bold text-white font-mono">${alert.title}</h3>
          </div>
          <div class="text-xs text-gray-400 font-mono">${alert.timestamp} | Confidence: ${alert.confidence}%</div>
        </div>

        <div class="text-sm text-gray-300 mb-4">${alert.summary}</div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-900/60 p-3 rounded-lg text-xs mb-4">
          <div><span class="text-gray-500 block">Target Location</span><span class="font-bold text-gray-200 font-mono">${alert.location}</span></div>
          <div><span class="text-gray-500 block">Expected Arrival</span><span class="font-bold text-amber-400 font-mono">${alert.eta}</span></div>
          <div><span class="text-gray-500 block">Hazard Types</span><span class="font-bold text-cyan-400 font-mono">${alert.hazardTypes.join(", ")}</span></div>
          <div><span class="text-gray-500 block">Required Action</span><span class="font-bold text-red-400 font-mono">${alert.action}</span></div>
        </div>

        <div class="flex justify-end space-x-3">
          <button onclick="window.alertoraAPI.triggerPublicWarning('${alert.location}').then(r => alert(r.message))" class="bg-red-600 hover:bg-red-500 text-white text-xs font-bold px-4 py-2 rounded-lg transition font-mono">
            BroadCast Public Warning
          </button>
          <button onclick="window.switchAppView('precautions')" class="bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-cyan-500/30 text-xs font-bold px-4 py-2 rounded-lg transition font-mono">
            View Precautions
          </button>
        </div>
      `;
      container.appendChild(alertCard);
    });
  }

  /* ==========================================================================
     PUBLIC SAFETY EMERGENCY HUB LOGIC ("MY SAFETY")
     ========================================================================== */
  const MY_SAFETY_PROTOCOLS = {
    THUNDERSTORM: {
      title: "🌩️ Thunderstorm & Lightning Emergency Protocol",
      immediate: [
        "Apply the 30/30 Rule: If thunder sounds within 30 seconds of lightning, seek sturdy indoor shelter immediately.",
        "Stay indoors inside a concrete building or fully enclosed metal vehicle.",
        "Stay away from windows, exterior doors, and electrical appliances."
      ],
      indoors: [
        "Unplug TVs, computers, and major electrical appliances before storm hits.",
        "Avoid using corded phones; mobile phones and cordless phones are safe.",
        "Do not take showers, baths, or use plumbing during active lightning."
      ],
      outdoors: [
        "If trapped in open field, adopt Lightning Crouch: squat low on balls of feet with heels touching, head down, ears covered.",
        "Never shelter under isolated tall trees, open sheds, or metal fences.",
        "Immediately exit swimming pools, rivers, lakes, and open bodies of water."
      ]
    },
    CLOUDBURST: {
      title: "🌊 Cloudburst & Flash Flood Emergency Protocol",
      immediate: [
        "Move immediately to higher ground or upper floors of concrete buildings.",
        "Never walk, swim, or drive through moving flood waters ('Turn Around, Don't Drown').",
        "Just 15 cm (6 inches) of moving water can knock an adult off their feet."
      ],
      indoors: [
        "Move valuable documents, electronics, and food supplies to higher shelves.",
        "If flood water enters building, shut off main electrical circuit breaker and gas valve.",
        "Monitor local government emergency broadcasts for evacuation alerts."
      ],
      outdoors: [
        "If vehicle stalls in rising water, abandon car immediately and climb to high ground.",
        "Avoid storm drains, riverbanks, drainage ditches, and flooded underpasses.",
        "Stay away from submerged power lines and electrical transformers."
      ]
    },
    HAILSTORM: {
      title: "🧊 Hailstorm & Impact Protection Protocol",
      immediate: [
        "Seek immediate cover under a solid roof or inside an enclosed vehicle.",
        "Keep clear of glass windows, skylights, and glass doors.",
        "Protect your head and face with arms, a bag, or heavy blanket if caught outside."
      ],
      indoors: [
        "Close window blinds and curtains to block flying glass fragments.",
        "Bring pets and farm animals indoors to covered shelters.",
        "Remain sheltered inside until hail completely ceases."
      ],
      outdoors: [
        "If driving, pull over under an overpass or gas station canopy.",
        "Stay inside car with seatbelts fastened, facing away from windows.",
        "Cover head with a coat, towel, or blanket to prevent glass injuries."
      ]
    },
    HIGHWIND: {
      title: "🌬️ High Winds & Severe Squall Protocol",
      immediate: [
        "Shelter in an interior windowless room (hallway, closet, or bathroom).",
        "Stay away from glass windows and exterior walls.",
        "Beware of airborne debris, fallen tree limbs, and unanchored roof sheets."
      ],
      indoors: [
        "Secure and latch all windows and exterior doors firmly.",
        "Clear balcony of outdoor chairs, potted plants, and loose objects.",
        "Keep flashlight ready in case overhead power lines are damaged."
      ],
      outdoors: [
        "Watch out for fallen electrical wires, billboards, and weak structures.",
        "If driving high-profile vehicles, pull over and wait out high wind gusts.",
        "Never touch downed wires or metal fences near fallen cables."
      ]
    }
  };

  let currentMySafetyHazard = "THUNDERSTORM";

  function renderMySafetyView() {
    const locId = state.selectedLocationId;
    const loc = locId === "gps-current" && state.gpsLocationData
      ? state.gpsLocationData
      : (ALERTORA_DATA.locations.find(l => l.id === locId) || ALERTORA_DATA.locations[0]);

    const locNameEl = document.getElementById("mysafety-loc-name");
    if (locNameEl) locNameEl.textContent = loc.placeName || loc.name;

    const riskText = document.getElementById("mysafety-risk-text");
    if (riskText) {
      riskText.textContent = `⚠️ ${loc.currentRisk || "HIGH"} THUNDERSTORM RISK`;
    }

    renderMySafetyProtocolBox(currentMySafetyHazard);
  }

  function renderMySafetyProtocolBox(hazardKey) {
    currentMySafetyHazard = hazardKey;
    const data = MY_SAFETY_PROTOCOLS[hazardKey] || MY_SAFETY_PROTOCOLS["THUNDERSTORM"];
    const box = document.getElementById("mysafety-protocol-box");
    if (!box) return;

    // Update active tab buttons
    document.querySelectorAll(".mysafety-tab-btn").forEach(btn => {
      if (btn.dataset.mysafetyHazard === hazardKey) {
        btn.className = "mysafety-tab-btn px-3 py-2 rounded-lg bg-cyan-500 text-black font-bold border border-cyan-400 transition text-center cursor-pointer";
      } else {
        btn.className = "mysafety-tab-btn px-3 py-2 rounded-lg bg-slate-900 text-gray-300 hover:text-cyan-400 border border-slate-800 transition text-center cursor-pointer";
      }
    });

    box.innerHTML = `
      <div class="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4">
        <h4 class="text-sm font-bold text-cyan-300 font-mono uppercase flex items-center">
          <span>${data.title}</span>
        </h4>

        <div class="space-y-3 text-xs font-mono">
          <!-- Immediate Action -->
          <div class="p-3.5 rounded-lg bg-red-950/25 border border-red-500/35">
            <div class="font-bold text-red-400 uppercase mb-2 flex items-center">
              <span class="w-2 h-2 rounded-full bg-red-500 animate-ping mr-2"></span>
              IMMEDIATE SURVIVAL ACTION (FIRST 5 MINUTES)
            </div>
            <ul class="space-y-1.5 text-gray-200">
              ${data.immediate.map(item => `<li class="flex items-start space-x-2"><span class="text-red-400 font-bold">•</span><span>${item}</span></li>`).join("")}
            </ul>
          </div>

          <!-- Indoor Protocol -->
          <div class="p-3.5 rounded-lg bg-cyan-950/25 border border-cyan-500/35">
            <div class="font-bold text-cyan-400 uppercase mb-2 flex items-center">
              <span class="mr-2">🏠</span>
              IF YOU ARE INDOORS
            </div>
            <ul class="space-y-1.5 text-gray-200">
              ${data.indoors.map(item => `<li class="flex items-start space-x-2"><span class="text-cyan-400 font-bold">•</span><span>${item}</span></li>`).join("")}
            </ul>
          </div>

          <!-- Outdoor Protocol -->
          <div class="p-3.5 rounded-lg bg-amber-950/25 border border-amber-500/35">
            <div class="font-bold text-amber-400 uppercase mb-2 flex items-center">
              <span class="mr-2">🚗</span>
              IF YOU ARE OUTDOORS / DRIVING
            </div>
            <ul class="space-y-1.5 text-gray-200">
              ${data.outdoors.map(item => `<li class="flex items-start space-x-2"><span class="text-amber-400 font-bold">•</span><span>${item}</span></li>`).join("")}
            </ul>
          </div>
        </div>
      </div>
    `;
  }

  function initMySafetyEventListeners() {
    document.querySelectorAll(".mysafety-tab-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const hazardKey = btn.dataset.mysafetyHazard;
        if (hazardKey) renderMySafetyProtocolBox(hazardKey);
      });
    });

    const checkboxes = document.querySelectorAll(".gobag-checkbox");
    const countEl = document.getElementById("gobag-count");
    const progressEl = document.getElementById("gobag-progress-bar");

    const updateChecklist = () => {
      const checked = document.querySelectorAll(".gobag-checkbox:checked").length;
      const total = checkboxes.length;
      const pct = Math.round((checked / total) * 100);

      if (countEl) countEl.textContent = `${checked} / ${total} Packed (${pct}%)`;
      if (progressEl) progressEl.style.width = `${pct}%`;
    };

    checkboxes.forEach(cb => {
      cb.addEventListener("change", updateChecklist);
    });

    const btnShelter = document.getElementById("btn-shelter-navigate");
    if (btnShelter) {
      btnShelter.addEventListener("click", () => {
        switchView("map");
        showToast("RELIEF SHELTER NAVIGATOR", "Opened Live GIS Map centered on St. Thomas Community Shelter #4", "CYAN");
      });
    }
  }

  // Render Government EOC Command Center View
  function renderEOCView() {
    const tbody = document.getElementById("eoc-district-table-body");
    if (!tbody) return;

    tbody.innerHTML = "";
    ALERTORA_DATA.eocDistricts.forEach(row => {
      const tr = document.createElement("tr");
      tr.className = "border-b border-slate-800 hover:bg-slate-800/40 transition";
      tr.innerHTML = `
        <td class="p-3 font-bold font-mono text-cyan-400">${row.district}</td>
        <td class="p-3 text-gray-300 text-xs font-mono">${row.hazard}</td>
        <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold font-mono ${getRiskBadgeClass(row.risk)}">${row.risk}</span></td>
        <td class="p-3 text-amber-400 font-mono text-xs font-bold">${row.eta}</td>
        <td class="p-3 text-gray-300 font-mono text-xs">${row.confidence}</td>
        <td class="p-3 text-gray-300 text-xs">${row.populationAtRisk}</td>
        <td class="p-3 text-gray-400 text-xs">${row.infraAtRisk}</td>
        <td class="p-3">
          <button onclick="window.alertoraAPI.triggerPublicWarning('${row.district}').then(r => alert(r.message))" class="bg-cyan-500/20 hover:bg-cyan-500 text-cyan-400 hover:text-black border border-cyan-500/40 text-[11px] font-bold px-2.5 py-1 rounded transition font-mono">
            ${row.actionRequired}
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  // Render Public Safety Mode ("My Safety")
  function renderMySafetyView() {
    const loc = ALERTORA_DATA.locations.find(l => l.id === state.selectedLocationId) || ALERTORA_DATA.locations[0];

    document.getElementById("mysafety-loc-name").textContent = loc.name;
    document.getElementById("mysafety-risk-banner").className = `p-4 rounded-xl border mb-6 flex items-center justify-between ${getRiskBadgeClass(loc.currentRisk)}`;
    document.getElementById("mysafety-risk-text").textContent = `⚠️ ${loc.currentRisk} ${loc.nextHazardType.toUpperCase()} ALERT`;
  }



  // Render Analytics Page Charts using Chart.js
  function renderAnalyticsCharts() {
    if (typeof Chart === "undefined") return;

    // Chart 1: 6-Hour Hazard Probabilities
    const ctx1 = document.getElementById("chart-hazard-timeline");
    if (ctx1 && !state.analyticsCharts.hazardTimeline) {
      state.analyticsCharts.hazardTimeline = new Chart(ctx1, {
        type: 'line',
        data: {
          labels: ['NOW', '+1 HR', '+2 HR', '+3 HR', '+4 HR', '+5 HR', '+6 HR'],
          datasets: [
            { label: 'Thunderstorm %', data: [72, 87, 94, 89, 65, 42, 25], borderColor: '#06b6d4', backgroundColor: 'rgba(6,182,212,0.1)', fill: true, tension: 0.4 },
            { label: 'Cloudburst Risk %', data: [34, 58, 76, 68, 42, 20, 8], borderColor: '#f97316', backgroundColor: 'rgba(249,115,22,0.1)', fill: true, tension: 0.4 },
            { label: 'Lightning Strike %', data: [68, 89, 96, 83, 58, 35, 18], borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.1)', fill: true, tension: 0.4 }
          ]
        },
        options: {
          responsive: true,
          plugins: { legend: { labels: { color: '#cbd5e1' } } },
          scales: {
            x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(51, 65, 85, 0.4)' } },
            y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(51, 65, 85, 0.4)' }, max: 100 }
          }
        }
      });
    }

    // Chart 2: Rainfall Intensity Curve
    const ctx2 = document.getElementById("chart-rainfall-intensity");
    if (ctx2 && !state.analyticsCharts.rainfall) {
      state.analyticsCharts.rainfall = new Chart(ctx2, {
        type: 'bar',
        data: {
          labels: ['NOW', '+1 HR', '+2 HR', '+3 HR', '+4 HR', '+5 HR', '+6 HR'],
          datasets: [{
            label: 'Predicted Rainfall (mm/hr)',
            data: [25, 52, 85, 60, 30, 15, 5],
            backgroundColor: '#3b82f6',
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { labels: { color: '#cbd5e1' } } },
          scales: {
            x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(51, 65, 85, 0.4)' } },
            y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(51, 65, 85, 0.4)' } }
          }
        }
      });
    }
  }

  // Setup Navigation Clicks
  function setupNavigation() {
    document.querySelectorAll(".nav-link").forEach(link => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const targetView = link.dataset.view;
        switchView(targetView);
      });
    });

    document.querySelectorAll(".precaution-hazard-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        state.selectedHazard = btn.dataset.hazard;
        renderPrecautionsView(state.selectedHazard);
      });
    });

    window.switchAppView = switchView;
  }

  // Notification Dropdown Drawer Toggle
  function toggleNotificationModal() {
    const dropdown = document.getElementById("notif-dropdown");
    if (dropdown) {
      dropdown.classList.toggle("hidden");
      if (!dropdown.classList.contains("hidden")) {
        renderNotificationDropdown();
      }
    }
  }

  // Render Glassmorphism Notification Dropdown List & Alert Count Badge
  function renderNotificationDropdown() {
    const listContainer = document.getElementById("notif-dropdown-list");
    const badgeCount = document.getElementById("notif-count-badge");
    const dropdownCount = document.getElementById("dropdown-notif-count");
    if (!listContainer) return;

    const alerts = ALERTORA_DATA.alertsFeed || [];
    if (badgeCount) badgeCount.textContent = alerts.length;
    if (dropdownCount) dropdownCount.textContent = `${alerts.length} Active`;

    listContainer.innerHTML = "";
    alerts.forEach(alert => {
      const item = document.createElement("div");
      const severityColor = alert.severity === "RED" 
        ? "border-red-500/50 bg-red-950/30 text-red-300" 
        : (alert.severity === "ORANGE" ? "border-orange-500/50 bg-orange-950/30 text-orange-300" : "border-yellow-500/40 bg-yellow-950/30 text-yellow-300");
      
      item.className = `p-2.5 rounded-lg border ${severityColor} transition hover:bg-slate-800/80 cursor-pointer`;
      item.onclick = () => {
        switchView("alerts");
        const d = document.getElementById("notif-dropdown");
        if (d) d.classList.add("hidden");
      };

      item.innerHTML = `
        <div class="flex items-center justify-between text-[10px] font-bold mb-1">
          <span class="px-1.5 py-0.2 rounded bg-black/40 border border-slate-700 font-mono">${alert.severity} SEVERITY</span>
          <span class="text-gray-400">${alert.timestamp}</span>
        </div>
        <div class="font-bold text-white text-[11px] leading-snug mb-1 font-mono">${alert.title}</div>
        <div class="text-[10px] text-gray-300">⌖ ${alert.location}</div>
        <div class="text-[10px] text-cyan-400 mt-1"><b>ETA:</b> ${alert.eta}</div>
      `;
      listContainer.appendChild(item);
    });
  }

  // Update Header Live Nowcast Strip & Dynamic Header Controls
  function updateHeaderNowcastData(loc) {
    if (!loc) return;

    // Location name
    const stripLocEl = document.getElementById("strip-loc-name");
    if (stripLocEl) stripLocEl.textContent = loc.name || loc.placeName || "Selected Location";

    // Risk Badges
    const riskBadgeClass = getRiskBadgeClass(loc.currentRisk);
    const headerRiskEl = document.getElementById("header-location-risk-badge");
    if (headerRiskEl) {
      headerRiskEl.textContent = `${loc.currentRisk} RISK`;
      headerRiskEl.className = `px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${riskBadgeClass}`;
    }

    const stripRiskEl = document.getElementById("strip-risk-badge");
    if (stripRiskEl) {
      stripRiskEl.textContent = `${loc.currentRisk} RISK`;
      stripRiskEl.className = `px-1.5 py-0.2 rounded text-[10px] font-bold uppercase ${riskBadgeClass}`;
    }

    // Dynamic metrics from nowcast[0]
    const currentNowcast = (loc.nowcast && loc.nowcast.length > 0) ? loc.nowcast[0] : null;
    if (currentNowcast) {
      const stormEl = document.getElementById("strip-thunderstorm");
      if (stormEl) stormEl.textContent = `${currentNowcast.thunderstorm}%`;

      const lightEl = document.getElementById("strip-lightning");
      if (lightEl) lightEl.textContent = `${currentNowcast.lightning}%`;

      const cloudEl = document.getElementById("strip-cloudburst");
      if (cloudEl) cloudEl.textContent = `${currentNowcast.cloudburst}%`;

      const hailEl = document.getElementById("strip-hail");
      if (hailEl) hailEl.textContent = `${currentNowcast.hail}%`;

      const windEl = document.getElementById("strip-wind");
      if (windEl) windEl.textContent = `${currentNowcast.wind || loc.windSpeed || 38} km/h`;
    }

    // Visually responsive risk state on Header border
    const appHeader = document.getElementById("app-header");
    if (appHeader) {
      appHeader.classList.remove("border-cyan-500/30", "border-emerald-500/40", "border-yellow-500/40", "border-orange-500/50", "border-red-500/60", "box-glow-red");
      if (loc.currentRisk === "EXTREME") {
        appHeader.classList.add("border-b", "border-red-500/60", "box-glow-red");
      } else if (loc.currentRisk === "HIGH") {
        appHeader.classList.add("border-b", "border-orange-500/50");
      } else if (loc.currentRisk === "MODERATE") {
        appHeader.classList.add("border-b", "border-yellow-500/40");
      } else {
        appHeader.classList.add("border-b", "border-emerald-500/40");
      }
    }
  }

  // Live Timestamp Clock for Header Strip
  function startHeaderClock() {
    const clockEl = document.getElementById("strip-update-clock");
    if (!clockEl) return;

    let seconds = 0;
    setInterval(() => {
      seconds++;
      if (seconds < 60) {
        clockEl.textContent = `LAST UPDATE: ${seconds} sec ago`;
      } else {
        const mins = Math.floor(seconds / 60);
        clockEl.textContent = `LAST UPDATE: ${mins} min ago`;
      }
    }, 1000);
  }

  // Toast Generator
  function showToast(title, message, severity = "CYAN") {
    const toastContainer = document.getElementById("toast-container");
    if (!toastContainer) return;

    const toast = document.createElement("div");
    const borderColor = severity === "RED" ? "border-red-500" : "border-cyan-500";
    toast.className = `glass-panel p-4 rounded-xl border-l-4 ${borderColor} text-white shadow-2xl transition-all duration-500 max-w-sm font-mono`;
    toast.innerHTML = `
      <div class="font-bold text-xs ${severity === "RED" ? "text-red-400" : "text-cyan-400"} uppercase">${title}</div>
      <div class="text-xs text-gray-300 mt-1">${message}</div>
    `;

    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.classList.add("opacity-0", "translate-x-full");
      setTimeout(() => toast.remove(), 500);
    }, 4500);
  }

  // Initialize Canvas Animated Radar Sweep on Landing Page
  function initRadarCanvas() {
    const canvas = document.getElementById("radar-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    function resize() {
      canvas.width = canvas.parentElement.clientWidth;
      canvas.height = canvas.parentElement.clientHeight;
    }
    resize();
    window.addEventListener("resize", resize);

    let angle = 0;
    function draw() {
      ctx.fillStyle = "rgba(7, 11, 20, 0.25)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const maxRadius = Math.min(centerX, centerY) * 0.85;

      // Draw concentric radar rings
      ctx.strokeStyle = "rgba(6, 182, 212, 0.15)";
      ctx.lineWidth = 1.5;
      for (let r = 0.2; r <= 1.0; r += 0.2) {
        ctx.beginPath();
        ctx.arc(centerX, centerY, maxRadius * r, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Draw crosshairs
      ctx.beginPath();
      ctx.moveTo(centerX - maxRadius, centerY);
      ctx.lineTo(centerX + maxRadius, centerY);
      ctx.moveTo(centerX, centerY - maxRadius);
      ctx.lineTo(centerX, centerY + maxRadius);
      ctx.stroke();

      // Radar Sweep Line
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate(angle);

      const gradient = ctx.createConicGradient(0, 0, 0);
      gradient.addColorStop(0, "rgba(6, 182, 212, 0.4)");
      gradient.addColorStop(0.2, "rgba(6, 182, 212, 0.05)");
      gradient.addColorStop(1, "transparent");

      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(0, 0, maxRadius, 0, Math.PI / 2);
      ctx.lineTo(0, 0);
      ctx.fill();

      ctx.restore();

      angle += 0.02;
      requestAnimationFrame(draw);
    }
    draw();
  }

  // Set default view
  switchView("landing");
});
