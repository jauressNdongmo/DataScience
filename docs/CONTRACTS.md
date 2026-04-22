# API Contracts (V1)

## 1) Decision Service

### POST `/decision/analysis`

Request:
```json
{
  "country": "Cameroon",
  "crop": "Maize",
  "year": 2026,
  "rainMmPerYear": 1600,
  "pesticidesTonnes": 150,
  "avgTemp": 25
}
```

Response:
```json
{
  "country": "Cameroon",
  "crop": "Maize",
  "year": 2026,
  "predictedYield": 38150.42,
  "weatherRisk": 0.66,
  "marketIndex": 1.01,
  "ndviIndex": 0.44,
  "riskLevel": "MEDIUM",
  "recommendations": [
    "Ajuster les intrants et intensifier le suivi météo terrain.",
    "Surveiller les prix de marché et lisser les ventes sur plusieurs semaines."
  ]
}
```

## 2) Integration Service

### GET `/integration/signals/realtime?country={country}&crop={crop}`

Response:
```json
{
  "country": "Cameroon",
  "crop": "Maize",
  "weatherRiskScore": 0.66,
  "marketPriceIndex": 1.01,
  "ndviIndex": 0.44
}
```

## 3) ML Python Service

### POST `/predict`

Request:
```json
{
  "country": "Cameroon",
  "crop": "Maize",
  "year": 2026,
  "rain_mm_per_year": 1600,
  "pesticides_tonnes": 150,
  "temperature_c": 25
}
```

Response:
```json
{
  "model": "GradientBoosting",
  "predicted_yield": 38150.42
}
```

### POST `/train`

Request:
```json
{
  "csv_path": "/app/data/yield_df.csv"
}
```

Response:
```json
{
  "status": "trained",
  "model": "GradientBoosting",
  "r2": 0.91,
  "samples": 28242
}
```
