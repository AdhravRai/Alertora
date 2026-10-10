# ALERTORA — ML Evidence

## Data
- Source: NCMRWF IMDAA
- Temporal resolution: hourly
- Spatial resolution: approximately 12 km
- Grid: 17 × 17
- Demonstration period: July 2020
- Demonstration case: 29 July 2020, 02:00 UTC

## ML Task
- Model: XGBoost
- Target: next-hour high-precipitation event risk
- Heavy-rain threshold: 2.2812 kg/m²
- Operating probability threshold: 0.25

## Held-out Test
- ROC-AUC: 0.8916
- Precision: 0.1854
- Recall: 0.6203
- F1: 0.2855

## Historical Demonstration
- Base time: 29 July 2020, 02:00 UTC
- Actual high-risk cells: 79
- XGBoost predicted cells: 105

## Spatial Fusion — Historical Event
- Fusion predicted cells: 71
- Precision: 0.7324
- Recall: 0.6582
- F1: 0.6933
- ROC-AUC: 0.8544

## Explainability

Top global model contributors:
1. Cloud water
2. Relative humidity
3. Relative humidity — 3h lag
4. U wind
5. Relative humidity — 1h lag

Example high-risk cell:
- Location: 27.00°N, 82.32°E
- Model probability: 89.64%

Top positive model contributors:
1. Cloud water: +0.246830
2. Relative humidity — 3h lag: +0.111693
3. Relative humidity: +0.106723
4. U wind: +0.076160
5. Surface pressure — 3h lag: +0.055771

## 0–6h Nowcast

The ML component predicts next-hour heavy-rain risk.

The 0–6h demonstration extends the available risk field using observed storm trajectory.

Therefore:
- It is a trajectory-based nowcast baseline.
- It is NOT an independently trained six-hour ML forecast.

## Important Limitations

- Historical demonstration, not a live operational forecast.
- IMDAA resolution is approximately 12 km.
- Current ML target is heavy-precipitation risk, not direct thunderstorm/hail classification.
- SHAP indicates model contribution, not physical causality.