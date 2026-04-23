from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field

from app.model import YieldModelService

app = FastAPI(title="Agri ML Service", version="2.1.0")
model_service = YieldModelService()


@app.middleware("http")
async def compatibility_prefix_rewrite(request: Request, call_next):
    # Accept legacy forwarded paths (/ml/*) and unstripped paths (/api/ml/*).
    path = request.scope.get("path", "")
    for prefix in ("/api/ml", "/ml"):
        if path == prefix:
            request.scope["path"] = "/"
            break
        if path.startswith(f"{prefix}/"):
            request.scope["path"] = path[len(prefix) :]
            break
    return await call_next(request)


class TrainRequest(BaseModel):
    csv_path: str = Field(default="/app/data/yield_df.csv")
    mode: str = Field(default="baseline")
    promote_if_better: bool = Field(default=True)
    replace_dataset: bool | None = Field(default=None)
    source_name: str = Field(default="train-endpoint")


class ModelSelectionRequest(BaseModel):
    model_version: str


class ModelRenameRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)


class PredictRequest(BaseModel):
    country: str
    crop: str
    year: int
    rain_mm_per_year: float
    pesticides_tonnes: float
    temperature_c: float


class SimulateRequest(BaseModel):
    country: str
    crop: str
    target_year: int = Field(default=0)
    rain_variation_pct: float = Field(default=0)
    temp_variation_c: float = Field(default=0)
    pesticides_variation_pct: float = Field(default=0)


class AlertRequest(BaseModel):
    country: str
    crop: str
    rain_variation_pct: float = Field(default=-20)
    temp_variation_c: float = Field(default=1.5)
    pesticides_variation_pct: float = Field(default=0)


@app.get("/health")
def health() -> dict:
    return {"status": "up"}


@app.get("/state")
def state() -> dict:
    if not model_service.is_ready:
        return {"ready": False}
    return {"ready": True, **model_service.get_training_info()}


@app.get("/model/registry")
def model_registry() -> dict:
    return model_service.get_registry()


@app.post("/model/activate")
def model_activate(request: ModelSelectionRequest) -> dict:
    try:
        result = model_service.activate_model(request.model_version)
        return {"status": "activated", **result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/model/revert-baseline")
def model_revert_baseline() -> dict:
    try:
        result = model_service.revert_to_baseline()
        return {"status": "baseline_activated", **result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.patch("/model/{model_version}/name")
def model_rename(model_version: str, request: ModelRenameRequest) -> dict:
    try:
        result = model_service.rename_model(model_version=model_version, display_name=request.display_name)
        return {"status": "renamed", **result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/model/{model_version}")
def model_delete(model_version: str) -> dict:
    try:
        result = model_service.delete_model(model_version)
        return {"status": "deleted", **result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/train")
def train(request: TrainRequest) -> dict:
    csv_path = Path(request.csv_path)
    if not csv_path.exists():
        raise HTTPException(status_code=400, detail=f"CSV file not found: {csv_path}")

    try:
        mode = request.mode.strip().lower()
        replace_dataset = request.replace_dataset if request.replace_dataset is not None else (mode == "finetune")
        df = pd.read_csv(csv_path)
        result = model_service.train(
            df,
            mode=mode,
            source=request.source_name or str(csv_path),
            promote_if_better=request.promote_if_better,
            replace_dataset=replace_dataset,
        )
        status = "trained" if result.get("promoted") else "candidate_not_promoted"
        return {"status": status, **result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/train/upload")
def train_upload(
    file: UploadFile = File(...),
    mode: str = Query(default="finetune", pattern="^(baseline|finetune)$"),
    promote_if_better: bool = Query(default=True),
    replace_dataset: bool | None = Query(default=None),
) -> dict:
    try:
        effective_replace_dataset = replace_dataset if replace_dataset is not None else (mode == "finetune")
        df = pd.read_csv(file.file)
        result = model_service.train(
            df,
            mode=mode,
            source=file.filename or "upload.csv",
            promote_if_better=promote_if_better,
            replace_dataset=effective_replace_dataset,
        )
        status = "trained" if result.get("promoted") else "candidate_not_promoted"
        return {"status": status, **result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/predict")
def predict(request: PredictRequest) -> dict:
    try:
        return model_service.predict(
            country=request.country,
            crop=request.crop,
            year=request.year,
            rain_mm_per_year=request.rain_mm_per_year,
            pesticides_tonnes=request.pesticides_tonnes,
            temperature_c=request.temperature_c,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/overview")
def overview() -> dict:
    try:
        return model_service.get_overview_payload()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/options/countries")
def options_countries() -> dict:
    try:
        return {"countries": model_service.get_countries()}
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/options/crops")
def options_crops(country: str = Query(...)) -> dict:
    try:
        return {"country": country, "crops": model_service.get_crops(country)}
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/scenario/context")
def scenario_context(country: str = Query(...), crop: str = Query(...)) -> dict:
    try:
        return model_service.get_scenario_context(country, crop)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/scenario/simulate")
def scenario_simulate(request: SimulateRequest) -> dict:
    try:
        return model_service.simulate(
            country=request.country,
            crop=request.crop,
            target_year=request.target_year,
            rain_variation_pct=request.rain_variation_pct,
            temp_variation_c=request.temp_variation_c,
            pesticides_variation_pct=request.pesticides_variation_pct,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/alerts")
def alerts(request: AlertRequest) -> dict:
    try:
        return model_service.generate_alerts(
            country=request.country,
            crop=request.crop,
            rain_variation_pct=request.rain_variation_pct,
            temp_variation_c=request.temp_variation_c,
            pesticides_variation_pct=request.pesticides_variation_pct,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/performance")
def performance() -> dict:
    try:
        return model_service.get_performance_payload()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.on_event("startup")
def startup_train() -> None:
    auto_train = os.getenv("AUTO_TRAIN_ON_STARTUP", "false").strip().lower() == "true"
    if not auto_train or model_service.is_ready:
        return

    default_csv = Path(os.getenv("DATASET_PATH", "/app/data/yield_df.csv"))
    if default_csv.exists():
        df = pd.read_csv(default_csv)
        model_service.train(
            df,
            mode="baseline",
            source=str(default_csv),
            promote_if_better=True,
            replace_dataset=True,
        )
