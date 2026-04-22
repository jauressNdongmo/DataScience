from __future__ import annotations

from dataclasses import dataclass

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


class YieldModelService:
    def __init__(self) -> None:
        self.state: ModelState | None = None

    @property
    def is_ready(self) -> bool:
        return self.state is not None

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

    def train(self, df: pd.DataFrame) -> dict:
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

        candidate_models = {
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

        results: dict[str, TrainedModelResult] = {}
        for name, model in candidate_models.items():
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
        self.state = ModelState(
            df=df,
            le_area=le_area,
            le_item=le_item,
            results=results,
            best_model_name=best_model_name,
        )

        return {
            "best_model": best_model_name,
            "r2": results[best_model_name].r2,
            "samples": int(len(df)),
            "models": {
                name: {
                    "MAE": result.mae,
                    "RMSE": result.rmse,
                    "R2": result.r2,
                }
                for name, result in results.items()
            },
        }

    def _require_state(self) -> ModelState:
        if self.state is None:
            raise RuntimeError("No model trained yet")
        return self.state

    def get_training_info(self) -> dict:
        state = self._require_state()
        best = state.results[state.best_model_name]
        return {
            "best_model": state.best_model_name,
            "r2": best.r2,
            "samples": int(len(state.df)),
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
