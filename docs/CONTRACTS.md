# API Contracts (V2)

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
    "Ajuster les intrants et intensifier le suivi meteo terrain.",
    "Surveiller les prix de marche et lisser les ventes sur plusieurs semaines."
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

### GET `/state`

Response:
```json
{
  "ready": true,
  "best_model": "XGBoost",
  "r2": 0.94,
  "samples": 28242,
  "model_version": "model-20260422T210001Z-abc12345"
}
```

### GET `/model/registry`

Response (extrait):
```json
{
  "active_model_version": "model-20260422T210001Z-abc12345",
  "baseline_model_version": "model-20260422T210001Z-abc12345",
  "recommended_model_version": "model-20260422T220220Z-1234abcd",
  "active": {
    "model_version": "model-20260422T210001Z-abc12345",
    "display_name": "Baseline global",
    "best_model": "XGBoost",
    "r2": 0.94,
    "promoted": true
  },
  "versions": [
    {
      "model_version": "model-20260422T210001Z-abc12345",
      "mode": "baseline",
      "source": "yield_df.csv",
      "promoted": true
    },
    {
      "model_version": "model-20260422T211115Z-def67890",
      "mode": "finetune",
      "source": "user_upload.csv",
      "promoted": false
    }
  ]
}
```

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
  "model": "XGBoost",
  "model_version": "model-20260422T210001Z-abc12345",
  "predicted_yield": 38150.42
}
```

### POST `/train`

Request:
```json
{
  "csv_path": "/app/data/yield_df.csv",
  "mode": "baseline",
  "promote_if_better": true,
  "replace_dataset": true,
  "source_name": "bootstrap"
}
```

### POST `/train/upload?mode=finetune&promote_if_better=true&replace_dataset=false`

Multipart form-data:
- `file`: CSV utilisateur

Response (extrait):
```json
{
  "status": "trained",
  "promoted": true,
  "promotion_reason": "improved_or_equal_metric",
  "best_model": "XGBoost",
  "r2": 0.95,
  "active_model_version": "model-20260422T220220Z-1234abcd",
  "candidate": {
    "model_version": "model-20260422T220220Z-1234abcd",
    "mode": "finetune",
    "source": "my_data.csv"
  }
}
```


### POST `/model/activate`

Request:
```json
{
  "model_version": "model-20260422T220220Z-1234abcd"
}
```

Response:
```json
{
  "status": "activated",
  "active_model_version": "model-20260422T220220Z-1234abcd",
  "training": {
    "best_model": "Random Forest",
    "r2": 0.95,
    "samples": 45729,
    "model_version": "model-20260422T220220Z-1234abcd"
  }
}
```

### POST `/model/revert-baseline`

Response:
```json
{
  "status": "baseline_activated",
  "baseline_model_version": "model-20260422T210001Z-abc12345",
  "active_model_version": "model-20260422T210001Z-abc12345",
  "training": {
    "best_model": "XGBoost",
    "r2": 0.94,
    "samples": 28242,
    "model_version": "model-20260422T210001Z-abc12345"
  }
}
```


### PATCH `/model/{model_version}/name`

Request:
```json
{
  "display_name": "Fine-tune Avril 2026"
}
```

Response:
```json
{
  "status": "renamed",
  "model_version": "model-20260422T220220Z-1234abcd",
  "display_name": "Fine-tune Avril 2026"
}
```

### DELETE `/model/{model_version}`

Règle: la suppression du `baseline_model_version` est refusée.

Response:
```json
{
  "status": "deleted",
  "deleted_model_version": "model-20260422T220220Z-1234abcd",
  "active_model_version": "model-20260422T210001Z-abc12345",
  "baseline_model_version": "model-20260422T210001Z-abc12345",
  "registry_versions": 3
}
```
