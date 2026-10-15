/* ==========================================================================
   ALERTORA AI — Severe Weather Data & Mock API Data Engine
   ========================================================================== */

const ALERTORA_DATA = {
  // System Metadata
  system: {
    name: "ALERTORA AI",
    version: "2.4.0-HackathonPrototype",
    tagline: "Predict Early. Prepare Smart. Save Lives.",
    status: "AI SYSTEM ONLINE",
    confidence: 91,
    lastUpdate: "Just now (Live Sync)",
    sihProblem: "SIH26084 — Convective Scale Nowcasting (0-6 Hr)",
    sensors: {
      dopplerRadar: { name: "Chennai & Sriharikota DWR", status: "ONLINE", latency: "2 min" },
      insatSatellite: { name: "INSAT-3DR Multispectral", status: "ONLINE", latency: "5 min" },
      lightningNetwork: { name: "IITM Lightning Location Network", status: "ONLINE", latency: "1 min" },
      awsStations: { name: "IMD Ground AWS Grid (450+)", status: "ONLINE", latency: "3 min" },
      rainfallSensors: { name: "Automatic Rain Gauges (ARG)", status: "ONLINE", latency: "4 min" },
      nwpModels: { name: "NCUM & ERA5 Assimilation", status: "ONLINE", latency: "15 min" }
    }
  },

  // Target Locations List (Tamil Nadu Focus + Cities)
  locations: [
    {
      id: "chennai",
      name: "Chennai Metropolis",
      district: "Chennai",
      state: "Tamil Nadu",
      lat: 13.0827,
      lng: 80.2707,
      currentRisk: "HIGH",
      temp: 31.4,
      humidity: 88,
      windSpeed: 38,
      pressure: 1004.2,
      rainfallRate: 42, // mm/hr
      nextHazardETA: "01h 24m",
      nextHazardType: "Thunderstorm + Lightning",
      nowcast: [
        { hour: "NOW", time: "12:30", thunderstorm: 72, hail: 18, cloudburst: 34, lightning: 68, rainfall: 25, wind: 35 },
        { hour: "+1 HR", time: "13:30", thunderstorm: 87, hail: 32, cloudburst: 58, lightning: 89, rainfall: 52, wind: 48 },
        { hour: "+2 HR", time: "14:30", thunderstorm: 94, hail: 42, cloudburst: 76, lightning: 96, rainfall: 85, wind: 62 },
        { hour: "+3 HR", time: "15:30", thunderstorm: 89, hail: 41, cloudburst: 68, lightning: 83, rainfall: 60, wind: 52 },
        { hour: "+4 HR", time: "16:30", thunderstorm: 65, hail: 22, cloudburst: 42, lightning: 58, rainfall: 30, wind: 38 },
        { hour: "+5 HR", time: "17:30", thunderstorm: 42, hail: 10, cloudburst: 20, lightning: 35, rainfall: 15, wind: 24 },
        { hour: "+6 HR", time: "18:30", thunderstorm: 25, hail: 5, cloudburst: 8, lightning: 18, rainfall: 5, wind: 15 }
      ]
    },
    {
      id: "tiruvallur",
      name: "Tiruvallur / Gummidipundi",
      district: "Tiruvallur",
      state: "Tamil Nadu",
      lat: 13.1439,
      lng: 79.905,
      currentRisk: "EXTREME",
      temp: 29.8,
      humidity: 92,
      windSpeed: 52,
      pressure: 1002.8,
      rainfallRate: 78,
      nextHazardETA: "00h 25m",
      nextHazardType: "Cloudburst & Intense Lightning",
      nowcast: [
        { hour: "NOW", time: "12:30", thunderstorm: 88, hail: 45, cloudburst: 72, lightning: 94, rainfall: 65, wind: 55 },
        { hour: "+1 HR", time: "13:30", thunderstorm: 98, hail: 62, cloudburst: 91, lightning: 99, rainfall: 110, wind: 72 },
        { hour: "+2 HR", time: "14:30", thunderstorm: 92, hail: 50, cloudburst: 84, lightning: 91, rainfall: 90, wind: 65 },
        { hour: "+3 HR", time: "15:30", thunderstorm: 75, hail: 28, cloudburst: 52, lightning: 68, rainfall: 45, wind: 42 },
        { hour: "+4 HR", time: "16:30", thunderstorm: 48, hail: 14, cloudburst: 25, lightning: 40, rainfall: 20, wind: 30 },
        { hour: "+5 HR", time: "17:30", thunderstorm: 30, hail: 8, cloudburst: 12, lightning: 22, rainfall: 10, wind: 20 },
        { hour: "+6 HR", time: "18:30", thunderstorm: 18, hail: 2, cloudburst: 5, lightning: 12, rainfall: 4, wind: 12 }
      ]
    },
    {
      id: "kanchipuram",
      name: "Kanchipuram Urban",
      district: "Kanchipuram",
      state: "Tamil Nadu",
      lat: 12.8342,
      lng: 79.7036,
      currentRisk: "MODERATE",
      temp: 32.1,
      humidity: 82,
      windSpeed: 28,
      pressure: 1006.1,
      rainfallRate: 18,
      nextHazardETA: "02h 10m",
      nextHazardType: "Severe Thunderstorm",
      nowcast: [
        { hour: "NOW", time: "12:30", thunderstorm: 45, hail: 12, cloudburst: 18, lightning: 50, rainfall: 10, wind: 22 },
        { hour: "+1 HR", time: "13:30", thunderstorm: 68, hail: 22, cloudburst: 31, lightning: 74, rainfall: 28, wind: 36 },
        { hour: "+2 HR", time: "14:30", thunderstorm: 84, hail: 38, cloudburst: 55, lightning: 88, rainfall: 58, wind: 48 },
        { hour: "+3 HR", time: "15:30", thunderstorm: 78, hail: 30, cloudburst: 42, lightning: 79, rainfall: 42, wind: 40 },
        { hour: "+4 HR", time: "16:30", thunderstorm: 52, hail: 15, cloudburst: 22, lightning: 48, rainfall: 22, wind: 28 },
        { hour: "+5 HR", time: "17:30", thunderstorm: 32, hail: 6, cloudburst: 10, lightning: 26, rainfall: 8, wind: 18 },
        { hour: "+6 HR", time: "18:30", thunderstorm: 15, hail: 2, cloudburst: 4, lightning: 10, rainfall: 2, wind: 10 }
      ]
    },
    {
      id: "coimbatore",
      name: "Coimbatore Western Ghats",
      district: "Coimbatore",
      state: "Tamil Nadu",
      lat: 11.0168,
      lng: 76.9558,
      currentRisk: "HIGH",
      temp: 26.5,
      humidity: 94,
      windSpeed: 44,
      pressure: 1001.5,
      rainfallRate: 58,
      nextHazardETA: "01h 05m",
      nextHazardType: "Heavy Downburst & Cloudburst",
      nowcast: [
        { hour: "NOW", time: "12:30", thunderstorm: 80, hail: 25, cloudburst: 60, lightning: 75, rainfall: 40, wind: 45 },
        { hour: "+1 HR", time: "13:30", thunderstorm: 91, hail: 40, cloudburst: 82, lightning: 88, rainfall: 88, wind: 60 },
        { hour: "+2 HR", time: "14:30", thunderstorm: 86, hail: 34, cloudburst: 70, lightning: 82, rainfall: 65, wind: 50 },
        { hour: "+3 HR", time: "15:30", thunderstorm: 62, hail: 18, cloudburst: 40, lightning: 55, rainfall: 35, wind: 34 },
        { hour: "+4 HR", time: "16:30", thunderstorm: 40, hail: 8, cloudburst: 20, lightning: 32, rainfall: 18, wind: 22 },
        { hour: "+5 HR", time: "17:30", thunderstorm: 22, hail: 2, cloudburst: 8, lightning: 18, rainfall: 6, wind: 14 },
        { hour: "+6 HR", time: "18:30", thunderstorm: 10, hail: 0, cloudburst: 2, lightning: 8, rainfall: 2, wind: 10 }
      ]
    },
    {
      id: "madurai",
      name: "Madurai South",
      district: "Madurai",
      state: "Tamil Nadu",
      lat: 9.9252,
      lng: 78.1198,
      currentRisk: "LOW",
      temp: 34.2,
      humidity: 68,
      windSpeed: 18,
      pressure: 1008.4,
      rainfallRate: 4,
      nextHazardETA: "04h 30m",
      nextHazardType: "Light Thunderstorm",
      nowcast: [
        { hour: "NOW", time: "12:30", thunderstorm: 18, hail: 4, cloudburst: 5, lightning: 20, rainfall: 2, wind: 12 },
        { hour: "+1 HR", time: "13:30", thunderstorm: 25, hail: 6, cloudburst: 8, lightning: 28, rainfall: 5, wind: 15 },
        { hour: "+2 HR", time: "14:30", thunderstorm: 38, hail: 10, cloudburst: 12, lightning: 42, rainfall: 12, wind: 20 },
        { hour: "+3 HR", time: "15:30", thunderstorm: 54, hail: 16, cloudburst: 22, lightning: 60, rainfall: 24, wind: 28 },
        { hour: "+4 HR", time: "16:30", thunderstorm: 68, hail: 22, cloudburst: 30, lightning: 72, rainfall: 38, wind: 36 },
        { hour: "+5 HR", time: "17:30", thunderstorm: 50, hail: 12, cloudburst: 18, lightning: 50, rainfall: 20, wind: 24 },
        { hour: "+6 HR", time: "18:30", thunderstorm: 30, hail: 5, cloudburst: 8, lightning: 30, rainfall: 8, wind: 16 }
      ]
    }
  ],

  // 4 Major Severe Weather Hazard Cards
  hazardsSummary: [
    {
      id: "thunderstorm",
      icon: "⛈",
      title: "THUNDERSTORM",
      probability: 87,
      riskLevel: "HIGH",
      eta: "01h 25m",
      description: "Convective cell intensifying over coastal belt. Reflectivity > 52 dBZ.",
      color: "#f97316"
    },
    {
      id: "hail",
      icon: "🧊",
      title: "HAIL PROBABILITY",
      probability: 42,
      riskLevel: "MODERATE",
      eta: "02h 40m",
      description: "Freezing level at 4.2km with high VIL water content detected by Radar.",
      color: "#f59e0b"
    },
    {
      id: "cloudburst",
      icon: "🌧",
      title: "CLOUDBURST / EXTREME RAIN",
      probability: 76,
      riskLevel: "HIGH",
      eta: "00h 50m",
      expectedRainfall: "85 mm/hr",
      description: "Localized mesoscale convective complex causing flash rainfall.",
      color: "#f97316"
    },
    {
      id: "lightning",
      icon: "⚡",
      title: "LIGHTNING STRIKE DENSITY",
      probability: 91,
      riskLevel: "EXTREME",
      eta: "00h 25m",
      expectedDensity: "34 strikes/km²/hr",
      description: "Severe Cloud-to-Ground (CG) lightning pulse detected upstream.",
      color: "#ef4444"
    }
  ],

  // Active Next Event Countdown Focus
  activeCountdown: {
    eventName: "Severe Convective Thunderstorm & Cloudburst",
    locationName: "Tiruvallur & North Chennai Coastal Zone",
    riskLevel: "EXTREME",
    confidence: 94,
    targetEtaMinutes: 24, // 00:24:36
    actionRequired: "Immediate Shelter & High Ground Alert"
  },

  // AI Safety Advisor Precautions Dataset
  precautionsDatabase: {
    THUNDERSTORM: {
      hazard: "Severe Thunderstorm",
      government: [
        "Issue localized automated public broadcast warning via SMS and cell broadcast.",
        "Activate district Emergency Operations Centers (EOC) and first responder units.",
        "Monitor vulnerable low-lying infrastructure, power sub-stations, and transit hubs.",
        "Deploy municipal pumping teams to critical underpasses and drainage nodes.",
        "Coordinate with State Electricity Board to prevent grid damage from lightning surges.",
        "Restrict unsafe outdoor public gatherings and high-voltage maintenance work."
      ],
      public: [
        "Stay indoors in a soundly constructed building immediately.",
        "Keep away from windows, balconies, exterior walls, and glass panels.",
        "Unplug sensitive electronic appliances to protect against surge damage.",
        "Avoid open fields, park benches, and metallic boundary fences.",
        "Do NOT take shelter under isolated tall trees or temporary tin sheds.",
        "Ensure mobile devices are fully charged and keep emergency contact numbers ready."
      ]
    },
    LIGHTNING: {
      hazard: "Extreme Cloud-to-Ground Lightning",
      government: [
        "Trigger immediate outdoor lightning siren alerts in schools, ports, and construction sites.",
        "Warn agricultural authorities to evacuate farmers from open fields.",
        "Monitor high-risk lightning strike zones identified by IITM sensor network.",
        "Deploy standby medical ambulances equipped with cardiac resuscitation gear."
      ],
      public: [
        "Seek immediate indoors shelter; do NOT stay in open ground or water bodies.",
        "If trapped outdoors in the open, crouch down into the 'lightning safety position' with heels touching.",
        "Avoid using corded phones or wired electrical equipment during active strikes.",
        "Avoid touching metal pipes, faucets, or plumbing fixtures.",
        "Do NOT shelter under isolated trees, light poles, or transmission towers."
      ]
    },
    HAIL: {
      hazard: "Hailstorm & Ice Impact",
      government: [
        "Issue immediate crop advisory to District Agriculture Officers and farmer cooperatives.",
        "Warn solar panel installations, greenhouse structures, and fragile roof facilities.",
        "Prepare emergency livestock protection enclosures.",
        "Alert highway traffic police regarding slick hail-slicked road surfaces."
      ],
      public: [
        "Move inside a sturdy building immediately; hail can cause severe head injury.",
        "Move vehicles under covered garages or thick tarpaulin covers if safe to do so.",
        "Stay clear of skylights, windows, and glass roofs.",
        "Protect livestock and pets by securing them inside covered shelters."
      ]
    },
    CLOUDBURST: {
      hazard: "Cloudburst & Flash Flood (>80 mm/hr)",
      government: [
        "Issue immediate flash flood and evacuation alerts for riverbanks and low-lying slums.",
        "Pre-position NDRF / SDRF flood rescue boats and high-capacity dewatering pumps.",
        "Close flooded underpasses, subways, and vulnerable bridge crossings.",
        "Set up temporary emergency relief shelters with clean drinking water and medical supplies.",
        "Monitor dam release levels and upstream catchment runoff continuously."
      ],
      public: [
        "Evacuate low-lying areas and move to upper floors or designated high ground immediately.",
        "Never attempt to drive or walk through moving floodwaters ('Turn Around, Don't Drown').",
        "Keep a emergency survival kit ready (food, water, torch, first aid, medicine, documents).",
        "Disconnect main electrical switch if water enters your home premises."
      ]
    },
    DOWNBURST: {
      hazard: "Severe Microburst / Downburst Wind (>75 km/h)",
      government: [
        "Alert airport traffic control and maritime port operations of sudden severe wind shear.",
        "Inspect high-rise hoardings, construction cranes, and temporary scaffoldings.",
        "Prepare tree-clearing emergency quick-response teams to clear blocked roadways."
      ],
      public: [
        "Stay inside and away from windows or loose roof structures.",
        "Avoid standing or parking near large trees, advertising billboards, or power lines.",
        "Secure loose outdoor furniture, flower pots, and balcony items."
      ]
    }
  },

  // Emergency Alerts Feed
  alertsFeed: [
    {
      id: "ALERT-9041",
      severity: "RED",
      title: "EXTREME CLOUDBURST & LIGHTNING ADVISORY",
      location: "Tiruvallur / Gummidipundi Sector",
      timestamp: "12:28 PM",
      eta: "Next 25 Minutes",
      confidence: 94,
      rainfallExpected: "110 mm/hr",
      hazardTypes: ["Cloudburst", "Lightning", "Thunderstorm"],
      summary: "Severe convective cloud mass detected with reflectivity reaching 56 dBZ. High probability of sudden flash flooding and violent lightning strikes.",
      action: "Immediate shelter mandatory. Evacuate low-lying ground."
    },
    {
      id: "ALERT-9038",
      severity: "ORANGE",
      title: "SEVERE THUNDERSTORM & WIND SHEAR ALERT",
      location: "Chennai North & Coastal Belt",
      timestamp: "12:15 PM",
      eta: "Next 45 Minutes",
      confidence: 89,
      windSpeedExpected: "62 km/h",
      hazardTypes: ["Thunderstorm", "Downburst"],
      summary: "Rapid convective storm cell moving East-Northeast. Expect high gusty winds, heavy downpour, and reduced visibility.",
      action: "Move indoors. Avoid driving under open structures."
    },
    {
      id: "ALERT-9032",
      severity: "YELLOW",
      title: "HAILSTORM WATCH",
      location: "Kanchipuram & Ranipet Districts",
      timestamp: "11:50 AM",
      eta: "Next 2 Hours",
      confidence: 76,
      hailSizeExpected: "1.5 - 2.5 cm",
      hazardTypes: ["Hail"],
      summary: "Doppler radar shows strong core updraft capable of generating medium-sized hail.",
      action: "Cover vehicles and protect exposed agricultural produce."
    },
    {
      id: "ALERT-9015",
      severity: "GREEN",
      title: "MODERATE RAIN & CONVECTIVE MONITORING",
      location: "Madurai & Virudhunagar Region",
      timestamp: "10:30 AM",
      eta: "Next 4 Hours",
      confidence: 82,
      hazardTypes: ["Rainfall"],
      summary: "Isolated rain showers expected. AI models indicate low immediate severe convective risk.",
      action: "Standard weather advisory."
    }
  ],

  // Government EOC Command Matrix Data
  eocDistricts: [
    { district: "Tiruvallur", hazard: "Cloudburst + Lightning", risk: "EXTREME", eta: "25 min", confidence: "94%", populationAtRisk: "850,000", infraAtRisk: "12 Power Substations, 4 Highways", actionRequired: "Trigger Cell Broadcast Warning" },
    { district: "Chennai", hazard: "Thunderstorm + Heavy Rain", risk: "HIGH", eta: "45 min", confidence: "91%", populationAtRisk: "2,400,000", infraAtRisk: "Subway Tunnels, Coastal Ports", actionRequired: "Deploy Dewatering Pumps" },
    { district: "Kanchipuram", hazard: "Thunderstorm + Hail", risk: "MODERATE", eta: "2 hr", confidence: "84%", populationAtRisk: "420,000", infraAtRisk: "Agricultural Orchards", actionRequired: "Issue Agriculture Alert" },
    { district: "Coimbatore", hazard: "Downburst + Rainfall", risk: "HIGH", eta: "1 hr 05m", confidence: "88%", populationAtRisk: "950,000", infraAtRisk: "Ghats Highway, Power Lines", actionRequired: "Restrict Mountain Transit" },
    { district: "Cuddalore", hazard: "Coastal Squall", risk: "MODERATE", eta: "3 hr", confidence: "79%", populationAtRisk: "310,000", infraAtRisk: "Fishing Harbors", actionRequired: "Issue Fishermen Warning" },
    { district: "Madurai", hazard: "Light Convection", risk: "LOW", eta: "4 hr 30m", confidence: "82%", populationAtRisk: "120,000", infraAtRisk: "None", actionRequired: "Routine Monitoring" }
  ],

  // Explainable AI (XAI) Feature Contributions
  xaiFactors: [
    { factor: "Doppler Radar Reflectivity (>50 dBZ)", weight: 34, description: "Strong convective core updraft detected" },
    { factor: "INSAT Cloud-Top Brightness Temp Drop (-62°C)", weight: 22, description: "Rapid cloud vertical growth reaching tropopause" },
    { factor: "Lightning Flash Rate Surge (+45 strikes/min)", weight: 18, description: "Intense electrical charge separation" },
    { factor: "Convective Available Potential Energy (CAPE > 2800 J/kg)", weight: 14, description: "High atmospheric instability" },
    { factor: "Low-Level Moisture Convergence & Dewpoint Spike", weight: 12, description: "Rich boundary layer moisture influx" }
  ],

  // Prototype Evaluation Metrics (AI Nowcast Engine Validation)
  evaluationMetrics: {
    accuracy: "94.2%",
    precision: "91.5%",
    recall: "92.8%",
    f1Score: "92.1%",
    csi: "0.81", // Critical Success Index
    falseAlarmRate: "0.08",
    averageLeadTime: "48 min",
    benchmarkNote: "Evaluated on 1,200+ historical severe convective events (IMD Doppler Radar & INSAT dataset)."
  },

  // Sensor Fusion Live Logs Stream
  fusionLogs: [
    { timestamp: "12:37:12", source: "RADAR", message: "Chennai DWR scan 3.5° sweep completed. Core reflectivity 54.2 dBZ at Lat 13.12, Lng 80.18." },
    { timestamp: "12:37:05", source: "LIGHTNING", message: "IITM Sensor Grid: 48 Cloud-to-Ground strikes detected in Tiruvallur box." },
    { timestamp: "12:36:50", source: "INSAT-3DR", message: "Band 10 Channel: Cloud top temperature decreased by 4.2°K in 15 minutes." },
    { timestamp: "12:36:30", source: "AWS GRID", message: "Station #TN-409 (Gummidipundi) reports pressure drop of 2.8 hPa/hr." },
    { timestamp: "12:36:10", source: "AI MODEL", message: "Convective nowcasting weights calculated. Risk status escalated to EXTREME." }
  ],

  // Designated Emergency Relief Shelters Database (Verified Geographic Coordinates)
  shelters: [
    {
      id: "shelter-st-thomas",
      name: "St. Thomas Community Shelter #4",
      lat: 13.0034,
      lng: 80.1972,
      locationId: "chennai",
      district: "Chennai",
      state: "Tamil Nadu",
      status: "OPEN",
      capacity: "850 / 1,200 Persons",
      distance: "1.8 km (4 min drive)",
      facilities: "24/7 Power Generator, Clean Water, Medical Post, Sanitation.",
      verified: true
    },
    {
      id: "shelter-tiruvallur",
      name: "Tiruvallur Cyclone Relief Complex",
      lat: 13.1439,
      lng: 79.9050,
      locationId: "tiruvallur",
      district: "Tiruvallur",
      state: "Tamil Nadu",
      status: "OPEN",
      capacity: "1,100 / 1,500 Persons",
      distance: "2.4 km (6 min drive)",
      facilities: "Emergency Kitchen, First Aid Camp, High-Ground Ramp.",
      verified: true
    },
    {
      id: "shelter-coimbatore",
      name: "Coimbatore South Civil Defense Base",
      lat: 10.9980,
      lng: 76.9650,
      locationId: "coimbatore",
      district: "Coimbatore",
      state: "Tamil Nadu",
      status: "OPEN",
      capacity: "700 / 1,000 Persons",
      distance: "3.1 km (7 min drive)",
      facilities: "Diesel Generator, Trauma Ambulance Post, Drinking Water.",
      verified: true
    },
    {
      id: "shelter-madurai",
      name: "Madurai North Relief Center",
      lat: 9.9390,
      lng: 78.1217,
      locationId: "madurai",
      district: "Madurai",
      state: "Tamil Nadu",
      status: "OPEN",
      capacity: "600 / 800 Persons",
      distance: "2.0 km (5 min drive)",
      facilities: "Flood Relief Boats, Clean Water, Emergency Ration Store.",
      verified: true
    },
    {
      id: "shelter-nilgiris",
      name: "Ooty Mountain Disaster Rescue Shelter",
      lat: 11.4102,
      lng: 76.6950,
      locationId: "nilgiris",
      district: "Nilgiris",
      state: "Tamil Nadu",
      status: "OPEN",
      capacity: "450 / 600 Persons",
      distance: "1.5 km (4 min drive)",
      facilities: "Landslide Evac Gear, Warm Blankets, VHF Radio Station.",
      verified: true
    },
    {
      id: "shelter-gorakhpur",
      name: "Gorakhpur Flood Relief Center",
      lat: 26.7606,
      lng: 83.3732,
      locationId: "ml-forecast-region",
      district: "Gorakhpur",
      state: "Uttar Pradesh",
      status: "OPEN",
      capacity: "950 / 1,200 Persons",
      distance: "1.9 km (5 min drive)",
      facilities: "Flood Rescue Boats, Medical Post, Clean Water Tankers.",
      verified: true
    }
  ]
};
