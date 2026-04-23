from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
import json
import os
import uuid

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBRegressor


FEATURES = [
    "Year",
    "average_rain_fall_mm_per_year",
    "pesticides_tonnes",
    "avg_temp",
    "Area_encoded",
    "Item_encoded",
]


@dataclass
class TrainedModelResult:
    model: object
    mae: float
    rmse: float
    r2: float
    feature_importance: pd.Series


@dataclass
class ModelState:
    df: pd.DataFrame
    le_area: LabelEncoder
    le_item: LabelEncoder
    results: dict[str, TrainedModelResult]
    best_model_name: str
    model_version: str
    created_at: str
    source: str
    mode: str


@dataclass
class RegistryVersion:
    model_version: str
    display_name: str
    artifact_path: str
    created_at: str
    source: str
    mode: str
    promoted: bool
    best_model: str
    r2: float
    samples: int
    models: dict[str, dict[str, float]]


class YieldModelService:
    def __init__(self, artifacts_dir: str | Path | None = None) -> None:
        base_dir = Path(artifacts_dir or os.getenv("MODEL_ARTIFACTS_DIR", "artifacts"))
        self.artifacts_dir = base_dir.resolve()
        self.models_dir = self.artifacts_dir / "models"
        self.registry_path = self.artifacts_dir / "registry.json"

        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.registry: dict = {"active_model_version": None, "baseline_model_version": None, "versions": []}
        self.state: ModelState | None = None

        self._load_registry()
        self._load_active_model()

    @property
    def is_ready(self) -> bool:
        return self.state is not None

    def _utc_now_iso(self) -> str:
        return datetime.now(UTC).isoformat()

    def _new_model_version(self) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return f"model-{timestamp}-{uuid.uuid4().hex[:8]}"

    def _default_display_name(self, model_version: str) -> str:
        return model_version

    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        if "Unnamed: 0" in df.columns:
            df = df.drop(columns=["Unnamed: 0"])

        required = {
            "Area",
            "Item",
            "Year",
            "average_rain_fall_mm_per_year",
            "pesticides_tonnes",
            "avg_temp",
            "hg/ha_yield",
        }
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

        df = df.copy()
        for col in [
            "Year",
            "average_rain_fall_mm_per_year",
            "pesticides_tonnes",
            "avg_temp",
            "hg/ha_yield",
        ]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        for col in df.select_dtypes(include=[np.number]).columns:
            df[col] = df[col].fillna(df[col].median())

        df["Year"] = df["Year"].astype(int)
        df["Area"] = df["Area"].astype(str)
        df["Item"] = df["Item"].astype(str)
        return df

    def _candidate_models(self) -> dict[str, object]:
        return {
            "Random Forest": RandomForestRegressor(
                n_estimators=200,
                max_depth=20,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1,
            ),
            "Gradient Boosting": GradientBoostingRegressor(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
            ),
            "XGBoost": XGBRegressor(
                n_estimators=300,
                max_depth=8,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
                n_jobs=-1,
                verbosity=0,
            ),
        }

    def _train_state(self, df: pd.DataFrame, source: str, mode: str) -> ModelState:
        df = self._prepare_dataframe(df)

        le_area = LabelEncoder()
        le_item = LabelEncoder()

        df_model = df.copy()
        df_model["Area_encoded"] = le_area.fit_transform(df_model["Area"])
        df_model["Item_encoded"] = le_item.fit_transform(df_model["Item"])

        X = df_model[FEATURES]
        y = df_model["hg/ha_yield"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        results: dict[str, TrainedModelResult] = {}
        for name, model in self._candidate_models().items():
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            feature_importance = getattr(model, "feature_importances_", np.zeros(len(FEATURES)))
            results[name] = TrainedModelResult(
                model=model,
                mae=float(mean_absolute_error(y_test, preds)),
                rmse=float(np.sqrt(mean_squared_error(y_test, preds))),
                r2=float(r2_score(y_test, preds)),
                feature_importance=pd.Series(feature_importance, index=FEATURES),
            )

        best_model_name = max(results, key=lambda model_name: results[model_name].r2)

        return ModelState(
            df=df,
            le_area=le_area,
            le_item=le_item,
            results=results,
            best_model_name=best_model_name,
            model_version=self._new_model_version(),
            created_at=self._utc_now_iso(),
            source=source,
            mode=mode,
        )

    def _state_summary(self, state: ModelState) -> dict:
        best = state.results[state.best_model_name]
        return {
            "best_model": state.best_model_name,
            "r2": float(best.r2),
            "samples": int(len(state.df)),
            "model_version": state.model_version,
            "created_at": state.created_at,
            "source": state.source,
            "mode": state.mode,
            "models": {
                name: {
                    "MAE": float(result.mae),
                    "RMSE": float(result.rmse),
                    "R2": float(result.r2),
                }
                for name, result in state.results.items()
            },
        }

    def _load_registry(self) -> None:
        if not self.registry_path.exists():
            return

        try:
            with self.registry_path.open("r", encoding="utf-8") as f:
                registry = json.load(f)
            if isinstance(registry, dict):
                self.registry = {
                    "active_model_version": registry.get("active_model_version"),
                    "baseline_model_version": registry.get("baseline_model_version"),
                    "versions": registry.get("versions", []),
                }
                if self._normalize_registry():
                    self._save_registry()
        except Exception:
            self.registry = {"active_model_version": None, "baseline_model_version": None, "versions": []}

    def _save_registry(self) -> None:
        payload = {
            "active_model_version": self.registry.get("active_model_version"),
            "baseline_model_version": self.registry.get("baseline_model_version"),
            "versions": self.registry.get("versions", []),
        }
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with self.registry_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _normalize_registry(self) -> bool:
        changed = False
        versions = self.registry.get("versions", [])
        if not isinstance(versions, list):
            versions = []
            changed = True

        normalized_versions: list[dict] = []
        known_versions: set[str] = set()
        for row in versions:
            if not isinstance(row, dict):
                changed = True
                continue
            model_version = str(row.get("model_version") or "").strip()
            if not model_version:
                changed = True
                continue
            if model_version in known_versions:
                changed = True
                continue
            known_versions.add(model_version)
            display_name = str(row.get("display_name") or "").strip() or self._default_display_name(model_version)
            if row.get("display_name") != display_name:
                changed = True
            row["display_name"] = display_name
            normalized_versions.append(row)

        self.registry["versions"] = normalized_versions

        active = self.registry.get("active_model_version")
        baseline = self.registry.get("baseline_model_version")
        if active and active not in known_versions:
            self.registry["active_model_version"] = None
            changed = True
        if baseline and baseline not in known_versions:
            self.registry["baseline_model_version"] = None
            changed = True

        if not self.registry.get("baseline_model_version"):
            baseline_candidates = [
                row
                for row in normalized_versions
                if row.get("mode") == "baseline" and row.get("promoted")
            ]
            if baseline_candidates:
                baseline_candidates.sort(key=lambda row: row.get("created_at", ""))
                self.registry["baseline_model_version"] = baseline_candidates[0].get("model_version")
                changed = True

        if not self.registry.get("active_model_version"):
            baseline_model_version = self.registry.get("baseline_model_version")
            if baseline_model_version:
                self.registry["active_model_version"] = baseline_model_version
                changed = True
        return changed

    def _find_registry_entry(self, model_version: str) -> dict | None:
        for version in self.registry.get("versions", []):
            if version.get("model_version") == model_version:
                return version
        return None

    def _persist_model_state(self, state: ModelState, promoted: bool) -> None:
        artifact_path = self.models_dir / f"{state.model_version}.joblib"
        joblib.dump(state, artifact_path)

        summary = self._state_summary(state)
        existing = self._find_registry_entry(state.model_version)
        display_name = (
            str(existing.get("display_name", "")).strip()
            if existing is not None
            else self._default_display_name(state.model_version)
        ) or self._default_display_name(state.model_version)
        version = RegistryVersion(
            model_version=state.model_version,
            display_name=display_name,
            artifact_path=str(artifact_path),
            created_at=state.created_at,
            source=state.source,
            mode=state.mode,
            promoted=promoted,
            best_model=summary["best_model"],
            r2=summary["r2"],
            samples=summary["samples"],
            models=summary["models"],
        )

        if existing:
            existing.update(asdict(version))
        else:
            self.registry["versions"].append(asdict(version))

        if promoted:
            self.registry["active_model_version"] = state.model_version
            if state.mode == "baseline":
                self.registry["baseline_model_version"] = state.model_version

        self._save_registry()

    def _load_active_model(self) -> None:
        active_model_version = self.registry.get("active_model_version")
        if not active_model_version:
            return

        entry = self._find_registry_entry(active_model_version)
        if not entry:
            return

        artifact = Path(entry.get("artifact_path", ""))
        if not artifact.exists():
            return

        try:
            loaded = joblib.load(artifact)
            if isinstance(loaded, ModelState):
                self.state = loaded
        except Exception:
            self.state = None

    def _get_recommended_model_version(self) -> str | None:
        versions = self.registry.get("versions", [])
        if not versions:
            return None

        promoted_versions = [row for row in versions if row.get("promoted")]
        source = promoted_versions or versions
        best = max(source, key=lambda row: float(row.get("r2", -1e9)))
        return best.get("model_version")

    def _load_state_for_version(self, model_version: str) -> ModelState:
        entry = self._find_registry_entry(model_version)
        if not entry:
            raise ValueError(f"Unknown model_version: {model_version}")

        artifact = Path(entry.get("artifact_path", ""))
        if not artifact.exists():
            raise ValueError(f"Artifact not found for model_version: {model_version}")

        loaded = joblib.load(artifact)
        if not isinstance(loaded, ModelState):
            raise ValueError(f"Invalid artifact payload for model_version: {model_version}")
        return loaded

    def activate_model(self, model_version: str) -> dict:
        chosen = self._load_state_for_version(model_version)
        self.state = chosen
        self.registry["active_model_version"] = model_version
        self._save_registry()
        return {
            "active_model_version": model_version,
            "training": self.get_training_info(),
        }

    def rename_model(self, model_version: str, display_name: str) -> dict:
        entry = self._find_registry_entry(model_version)
        if not entry:
            raise ValueError(f"Unknown model_version: {model_version}")

        clean_name = (display_name or "").strip()
        if not clean_name:
            raise ValueError("display_name cannot be empty")
        if len(clean_name) > 80:
            raise ValueError("display_name must be at most 80 characters")

        entry["display_name"] = clean_name
        self._save_registry()
        return {
            "model_version": model_version,
            "display_name": clean_name,
            "active_model_version": self.registry.get("active_model_version"),
            "baseline_model_version": self.registry.get("baseline_model_version"),
        }

    def delete_model(self, model_version: str) -> dict:
        baseline_model_version = self.registry.get("baseline_model_version")
        if baseline_model_version and model_version == baseline_model_version:
            raise ValueError("The baseline model cannot be deleted")

        entry = self._find_registry_entry(model_version)
        if not entry:
            raise ValueError(f"Unknown model_version: {model_version}")

        artifact = Path(entry.get("artifact_path", ""))
        self.registry["versions"] = [
            row for row in self.registry.get("versions", []) if row.get("model_version") != model_version
        ]

        if artifact.exists():
            artifact.unlink()

        was_active = self.registry.get("active_model_version") == model_version
        if was_active:
            fallback_model_version = self._get_recommended_model_version()
            if fallback_model_version:
                chosen = self._load_state_for_version(fallback_model_version)
                self.state = chosen
                self.registry["active_model_version"] = fallback_model_version
            else:
                self.state = None
                self.registry["active_model_version"] = None

        self._save_registry()
        payload = {
            "deleted_model_version": model_version,
            "active_model_version": self.registry.get("active_model_version"),
            "baseline_model_version": self.registry.get("baseline_model_version"),
            "registry_versions": len(self.registry.get("versions", [])),
        }
        if self.state is not None:
            payload["training"] = self.get_training_info()
        return payload

    def revert_to_baseline(self) -> dict:
        baseline_model_version = self.registry.get("baseline_model_version")
        if not baseline_model_version:
            versions = [
                row
                for row in self.registry.get("versions", [])
                if row.get("mode") == "baseline" and row.get("promoted")
            ]
            if not versions:
                raise ValueError("No baseline model available in registry")
            versions = sorted(versions, key=lambda row: row.get("created_at", ""))
            baseline_model_version = versions[0].get("model_version")
            self.registry["baseline_model_version"] = baseline_model_version

        result = self.activate_model(baseline_model_version)
        result["baseline_model_version"] = baseline_model_version
        return result

    def get_registry(self) -> dict:
        active = self.registry.get("active_model_version")
        baseline = self.registry.get("baseline_model_version")
        versions = sorted(
            self.registry.get("versions", []),
            key=lambda row: row.get("created_at", ""),
            reverse=True,
        )
        recommended = self._get_recommended_model_version()
        return {
            "active_model_version": active,
            "baseline_model_version": baseline,
            "recommended_model_version": recommended,
            "active": next((row for row in versions if row.get("model_version") == active), None),
            "baseline": next((row for row in versions if row.get("model_version") == baseline), None),
            "recommended": next((row for row in versions if row.get("model_version") == recommended), None),
            "versions": versions,
        }

    def train(
        self,
        df: pd.DataFrame,
        mode: str = "baseline",
        source: str = "manual",
        promote_if_better: bool = True,
        replace_dataset: bool = False,
    ) -> dict:
        mode = mode.strip().lower()
        if mode not in {"baseline", "finetune"}:
            raise ValueError("mode must be 'baseline' or 'finetune'")

        incoming_df = self._prepare_dataframe(df)

        if mode == "finetune" and self.state is not None and not replace_dataset:
            training_df = pd.concat([self.state.df, incoming_df], ignore_index=True)
            training_df = training_df.drop_duplicates(ignore_index=True)
        else:
            training_df = incoming_df

        current_state = self.state
        current_r2 = None
        if current_state is not None:
            current_r2 = current_state.results[current_state.best_model_name].r2

        candidate_state = self._train_state(training_df, source=source, mode=mode)
        candidate_summary = self._state_summary(candidate_state)

        promoted = True
        promotion_reason = "initial_model"
        if current_state is not None:
            promotion_reason = "improved_or_equal_metric"
            if promote_if_better and candidate_summary["r2"] < float(current_r2):
                promoted = False
                promotion_reason = "candidate_under_active_r2"

        self._persist_model_state(candidate_state, promoted=promoted)

        if promoted:
            self.state = candidate_state
            active_summary = candidate_summary
        else:
            self.state = current_state
            active_summary = self.get_training_info()

        return {
            "best_model": active_summary["best_model"],
            "r2": active_summary["r2"],
            "samples": active_summary["samples"],
            "model_version": active_summary.get("model_version"),
            "models": active_summary.get("models", {}),
            "promoted": promoted,
            "promotion_reason": promotion_reason,
            "candidate": {
                "best_model": candidate_summary["best_model"],
                "r2": candidate_summary["r2"],
                "samples": candidate_summary["samples"],
                "model_version": candidate_summary["model_version"],
                "created_at": candidate_summary["created_at"],
                "source": candidate_summary["source"],
                "mode": candidate_summary["mode"],
                "models": candidate_summary["models"],
            },
            "active_model_version": self.registry.get("active_model_version"),
            "registry_versions": len(self.registry.get("versions", [])),
        }

    def _require_state(self) -> ModelState:
        if self.state is None:
            raise RuntimeError("No model trained yet")
        return self.state

    def get_training_info(self) -> dict:
        state = self._require_state()
        summary = self._state_summary(state)
        entry = self._find_registry_entry(state.model_version)
        return {
            "best_model": summary["best_model"],
            "r2": summary["r2"],
            "samples": summary["samples"],
            "model_version": summary["model_version"],
            "display_name": (entry or {}).get("display_name", self._default_display_name(summary["model_version"])),
            "created_at": summary["created_at"],
            "source": summary["source"],
            "mode": summary["mode"],
            "models": summary["models"],
        }

    def get_countries(self) -> list[str]:
        state = self._require_state()
        return sorted(state.df["Area"].dropna().unique().tolist())

    def get_crops(self, country: str) -> list[str]:
        state = self._require_state()
        subset = state.df[state.df["Area"] == country]
        return sorted(subset["Item"].dropna().unique().tolist())

    def _get_subset(self, country: str, crop: str) -> pd.DataFrame:
        state = self._require_state()
        return state.df[(state.df["Area"] == country) & (state.df["Item"] == crop)]

    def _predict_scenario(
        self,
        country: str,
        crop: str,
        year: int,
        rain_mm_per_year: float,
        pesticides_tonnes: float,
        temperature_c: float,
        model_name: str | None = None,
    ) -> float | None:
        state = self._require_state()
        selected_model_name = model_name or state.best_model_name
        selected_model = state.results[selected_model_name].model

        try:
            area_encoded = state.le_area.transform([country])[0]
            item_encoded = state.le_item.transform([crop])[0]
        except ValueError:
            return None

        X_new = pd.DataFrame(
            [
                [
                    year,
                    rain_mm_per_year,
                    pesticides_tonnes,
                    temperature_c,
                    area_encoded,
                    item_encoded,
                ]
            ],
            columns=FEATURES,
        )
        return float(selected_model.predict(X_new)[0])

    def predict(
        self,
        country: str,
        crop: str,
        year: int,
        rain_mm_per_year: float,
        pesticides_tonnes: float,
        temperature_c: float,
    ) -> dict:
        state = self._require_state()
        prediction = self._predict_scenario(
            country=country,
            crop=crop,
            year=year,
            rain_mm_per_year=rain_mm_per_year,
            pesticides_tonnes=pesticides_tonnes,
            temperature_c=temperature_c,
        )
        if prediction is None:
            raise ValueError("Unknown country or crop for current trained model")

        return {
            "model": state.best_model_name,
            "model_version": state.model_version,
            "predicted_yield": prediction,
        }

    def get_overview_payload(self) -> dict:
        state = self._require_state()
        df = state.df

        metrics = {
            "observations": int(df.shape[0]),
            "countries": int(df["Area"].nunique()),
            "crops": int(df["Item"].nunique()),
            "year_min": int(df["Year"].min()),
            "year_max": int(df["Year"].max()),
        }

        trend_df = (
            df.groupby("Year", as_index=False)["hg/ha_yield"]
            .mean()
            .sort_values("Year")
        )
        crop_df = (
            df.groupby("Item", as_index=False)["hg/ha_yield"]
            .mean()
            .sort_values("hg/ha_yield", ascending=True)
        )

        return {
            "metrics": metrics,
            "trend": [
                {"year": int(row["Year"]), "yield": float(row["hg/ha_yield"])}
                for _, row in trend_df.iterrows()
            ],
            "yield_by_crop": [
                {"crop": str(row["Item"]), "yield": float(row["hg/ha_yield"])}
                for _, row in crop_df.iterrows()
            ],
            "training": self.get_training_info(),
        }

    def get_scenario_context(self, country: str, crop: str) -> dict:
        subset = self._get_subset(country, crop)
        if subset.empty:
            raise ValueError("Données historiques insuffisantes pour cette combinaison pays/culture")

        latest_year = int(subset["Year"].max())
        rain_base = float(subset["average_rain_fall_mm_per_year"].median())
        temp_base = float(subset["avg_temp"].median())
        pesticides_base = float(subset["pesticides_tonnes"].median())
        historical_mean = float(subset["hg/ha_yield"].mean())

        return {
            "country": country,
            "crop": crop,
            "latest_year": latest_year,
            "historical_mean": historical_mean,
            "rain_base": rain_base,
            "temp_base": temp_base,
            "pesticides_base": pesticides_base,
        }

    def simulate(
        self,
        country: str,
        crop: str,
        target_year: int,
        rain_variation_pct: float,
        temp_variation_c: float,
        pesticides_variation_pct: float,
    ) -> dict:
        context = self.get_scenario_context(country, crop)
        year = target_year if target_year > 0 else min(context["latest_year"] + 1, 2050)

        rain_base = context["rain_base"]
        temp_base = context["temp_base"]
        pesticides_base = context["pesticides_base"]

        rain_modified = rain_base * (1 + rain_variation_pct / 100)
        temp_modified = temp_base + temp_variation_c
        pesticides_modified = pesticides_base * (1 + pesticides_variation_pct / 100)

        base_prediction = self._predict_scenario(
            country,
            crop,
            year,
            rain_base,
            pesticides_base,
            temp_base,
        )
        scenario_prediction = self._predict_scenario(
            country,
            crop,
            year,
            rain_modified,
            pesticides_modified,
            temp_modified,
        )

        if base_prediction is None or scenario_prediction is None:
            raise ValueError("Impossible de calculer la projection pour ce scénario")

        variation_pct = 0.0
        if abs(base_prediction) > 1e-12:
            variation_pct = ((scenario_prediction - base_prediction) / base_prediction) * 100

        historical_mean = context["historical_mean"]

        comparison = [
            {"name": "Historique", "value": historical_mean, "color": "#8B5E3C"},
            {"name": f"Base {year}", "value": base_prediction, "color": "#2D6A2E"},
            {
                "name": f"Simulé {year}",
                "value": scenario_prediction,
                "color": "#C0392B" if variation_pct < -5 else "#E8820C" if variation_pct < 5 else "#27AE60",
            },
        ]

        sensitivity: list[dict] = []
        for vp in range(-40, 45, 5):
            p_rain = self._predict_scenario(
                country,
                crop,
                year,
                rain_base * (1 + vp / 100),
                pesticides_base,
                temp_base,
            )
            if p_rain is not None:
                sensitivity.append(
                    {
                        "variable": "Précipitations",
                        "variation_pct": float(vp),
                        "yield": float(p_rain),
                    }
                )

            p_inputs = self._predict_scenario(
                country,
                crop,
                year,
                rain_base,
                pesticides_base * (1 + vp / 100),
                temp_base,
            )
            if p_inputs is not None:
                sensitivity.append(
                    {
                        "variable": "Intrants",
                        "variation_pct": float(vp),
                        "yield": float(p_inputs),
                    }
                )

        for td in np.arange(-4, 4.5, 0.5):
            p_temp = self._predict_scenario(
                country,
                crop,
                year,
                rain_base,
                pesticides_base,
                temp_base + float(td),
            )
            if p_temp is not None:
                sensitivity.append(
                    {
                        "variable": "Température",
                        "variation_pct": float(td * 10),
                        "yield": float(p_temp),
                    }
                )

        stress_scenarios = {
            "Sécheresse critique": (-30, 2.0, 0),
            "Fortes précipitations/Inondation": (40, -1.0, -10),
            "Réchauffement sévère (+3°C)": (0, 3.0, 0),
            "Intensification agricole (Intrants x2)": (0, 0, 100),
            "Transition Biologique stricte": (0, 0, -100),
            "Combinaison pessimiste": (-40, 3.5, -20),
        }

        stress_table: list[dict] = []
        for scenario_name, (rain_var, temp_var, pest_var) in stress_scenarios.items():
            scenario_value = self._predict_scenario(
                country,
                crop,
                year,
                rain_base * (1 + rain_var / 100),
                pesticides_base * (1 + pest_var / 100),
                temp_base + temp_var,
            )
            if scenario_value is None:
                continue

            scenario_variation = 0.0
            if abs(base_prediction) > 1e-12:
                scenario_variation = ((scenario_value - base_prediction) / base_prediction) * 100

            state = "Normal" if scenario_variation > 5 else "Critique" if scenario_variation < -5 else "Stable"
            stress_table.append(
                {
                    "scenario": scenario_name,
                    "yield": float(scenario_value),
                    "variation_pct": float(scenario_variation),
                    "state": state,
                }
            )

        return {
            "context": {**context, "target_year": year},
            "input_variations": {
                "rain_variation_pct": rain_variation_pct,
                "temp_variation_c": temp_variation_c,
                "pesticides_variation_pct": pesticides_variation_pct,
                "rain_modified": rain_modified,
                "temp_modified": temp_modified,
                "pesticides_modified": pesticides_modified,
            },
            "metrics": {
                "historical_mean": historical_mean,
                "base_prediction": base_prediction,
                "scenario_prediction": scenario_prediction,
                "delta": scenario_prediction - base_prediction,
                "variation_pct": variation_pct,
            },
            "comparison": comparison,
            "sensitivity": sensitivity,
            "stress": stress_table,
        }

    def generate_alerts(
        self,
        country: str,
        crop: str,
        rain_variation_pct: float,
        temp_variation_c: float,
        pesticides_variation_pct: float,
    ) -> dict:
        context = self.get_scenario_context(country, crop)

        year = context["latest_year"] + 1
        rain_base = context["rain_base"]
        temp_base = context["temp_base"]
        pesticides_base = context["pesticides_base"]

        rain_modified = rain_base * (1 + rain_variation_pct / 100)
        temp_modified = temp_base + temp_variation_c
        pesticides_modified = pesticides_base * (1 + pesticides_variation_pct / 100)

        base_prediction = self._predict_scenario(
            country,
            crop,
            year,
            rain_base,
            pesticides_base,
            temp_base,
        )
        scenario_prediction = self._predict_scenario(
            country,
            crop,
            year,
            rain_modified,
            pesticides_modified,
            temp_modified,
        )

        if base_prediction is None or scenario_prediction is None:
            raise ValueError("Impossible de générer les alertes pour cette combinaison")

        variation_pct = 0.0
        if abs(base_prediction) > 1e-12:
            variation_pct = ((scenario_prediction - base_prediction) / base_prediction) * 100

        alerts: list[dict] = []
        recommendations: list[dict] = []

        if variation_pct < -20:
            alerts.append(
                {
                    "type": "danger",
                    "title": '<span class="icon">warning</span> ALERTE CRITIQUE',
                    "message": f"Déficit majeur anticipé : Baisse de {abs(variation_pct):.1f}% du rendement. Risque d'insécurité alimentaire pour {crop} dans {country}.",
                }
            )
        elif variation_pct < -10:
            alerts.append(
                {
                    "type": "warning",
                    "title": '<span class="icon">error_outline</span> VIGILANCE',
                    "message": f"Baisse estimée de {abs(variation_pct):.1f}%. Surveillance renforcée recommandée pour {crop}.",
                }
            )
        elif variation_pct > 15:
            alerts.append(
                {
                    "type": "success",
                    "title": '<span class="icon">trending_up</span> OPPORTUNITÉ',
                    "message": f"Hausse estimée de {variation_pct:.1f}%. Potentiel d'exportation ou de stockage pour {crop}.",
                }
            )

        if rain_variation_pct < -15:
            alerts.append(
                {
                    "type": "warning",
                    "title": '<span class="icon">water_drop</span> STRESS HYDRIQUE',
                    "message": f"La baisse de {abs(rain_variation_pct)}% des précipitations peut compromettre la croissance de {crop}.",
                }
            )

        if temp_variation_c > 2:
            alerts.append(
                {
                    "type": "warning",
                    "title": '<span class="icon">thermostat</span> STRESS THERMIQUE',
                    "message": f"L'augmentation de {temp_variation_c}°C expose {crop} à des risques de stress thermique sévère.",
                }
            )

        if variation_pct < -10:
            recommendations.append(
                {
                    "category": '<span class="icon">policy</span> Politiques publiques',
                    "actions": [
                        f"Activer les réserves alimentaires stratégiques pour {crop}.",
                        "Préparer un plan d'importation d'urgence si le déficit dépasse 25%.",
                        f"Débloquer des subventions ciblées pour les producteurs de {crop} dans {country}.",
                    ],
                }
            )
            recommendations.append(
                {
                    "category": '<span class="icon">eco</span> Réallocation des ressources',
                    "actions": [
                        "Ajuster l'apport en fertilisants pour compenser la baisse de rendement.",
                        "Prioriser l'irrigation sur les parcelles à plus fort potentiel.",
                        "Réorienter les traitements phytosanitaires vers les cultures les plus menacées.",
                    ],
                }
            )
            recommendations.append(
                {
                    "category": '<span class="icon">calendar_month</span> Planification agricole',
                    "actions": [
                        f"Envisager la transition vers des variétés de {crop} résistantes à la sécheresse.",
                        "Décaler les dates de semis pour s'adapter aux nouvelles conditions thermiques.",
                        "Diversifier les cultures de la région pour réduire la dépendance à une seule ressource.",
                    ],
                }
            )
        elif variation_pct > 10:
            recommendations.append(
                {
                    "category": '<span class="icon">inventory_2</span> Gestion du surplus',
                    "actions": [
                        f"Planifier le stockage stratégique du surplus de {crop}.",
                        "Négocier des contrats d'exportation de manière anticipée.",
                        "Investir dans la transformation agroalimentaire locale.",
                    ],
                }
            )
            recommendations.append(
                {
                    "category": '<span class="icon">savings</span> Optimisation économique',
                    "actions": [
                        "Réduire les intrants non essentiels pour optimiser les marges financières.",
                        "Réallouer les ressources humaines vers les cultures moins performantes.",
                        "Renforcer les infrastructures logistiques (transport et stockage).",
                    ],
                }
            )
        else:
            recommendations.append(
                {
                    "category": '<span class="icon">monitoring</span> Maintien & Surveillance',
                    "actions": [
                        "Maintenir les pratiques agricoles et itinéraires techniques actuels.",
                        "Surveiller l'évolution des conditions climatiques sur une base mensuelle.",
                        "Préparer des plans de contingence en cas de dégradation soudaine du climat.",
                    ],
                }
            )

        stats = {
            "pred_base": base_prediction,
            "pred_modifie": scenario_prediction,
            "variation_pct": variation_pct,
            "rend_historique": context["historical_mean"],
            "pluie_base": rain_base,
            "temp_base": temp_base,
            "pest_base": pesticides_base,
            "pluie_mod": rain_modified,
            "temp_mod": temp_modified,
            "pest_mod": pesticides_modified,
            "model_version": self._require_state().model_version,
        }

        return {
            "alerts": alerts,
            "recommendations": recommendations,
            "stats": stats,
        }

    def get_performance_payload(self) -> dict:
        state = self._require_state()
        best_model_name = state.best_model_name
        importance = state.results[best_model_name].feature_importance.sort_values()

        return {
            "best_model": best_model_name,
            "r2": state.results[best_model_name].r2,
            "model_version": state.model_version,
            "feature_importance": [
                {"feature": str(feature), "importance": float(value)}
                for feature, value in importance.items()
            ],
            "models": {
                name: {
                    "MAE": result.mae,
                    "RMSE": result.rmse,
                    "R2": result.r2,
                }
                for name, result in state.results.items()
            },
        }
