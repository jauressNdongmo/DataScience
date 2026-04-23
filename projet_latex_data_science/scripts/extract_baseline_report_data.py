from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract model comparison and preprocessing statistics for the LaTeX report."
    )
    parser.add_argument(
        "--dataset",
        default="backend/ml-python/data/yield_df.csv",
        help="Path to the dataset CSV.",
    )
    parser.add_argument(
        "--registry",
        default="backend/ml-python/artifacts/registry.json",
        help="Path to the model registry JSON.",
    )
    parser.add_argument(
        "--output-dir",
        default="projet_latex_data_science/data_report",
        help="Directory where report assets (CSV/JSON) are written.",
    )
    return parser.parse_args()


def as_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def find_entry(registry: dict, model_version: str | None) -> dict | None:
    if not model_version:
        return None
    for row in registry.get("versions", []):
        if row.get("model_version") == model_version:
            return row
    return None


def select_report_baseline_entry(registry: dict) -> dict:
    versions = registry.get("versions", [])
    if not isinstance(versions, list) or not versions:
        raise RuntimeError("Registry does not contain any model versions")

    baseline_candidates = [row for row in versions if row.get("mode") == "baseline"]
    if not baseline_candidates:
        # fallback: active version, then latest version
        active = find_entry(registry, registry.get("active_model_version"))
        if active is not None:
            return active
        versions_sorted = sorted(versions, key=lambda row: str(row.get("created_at", "")), reverse=True)
        return versions_sorted[0]

    promoted = [row for row in baseline_candidates if bool(row.get("promoted"))]
    source = promoted or baseline_candidates

    # Primary key: best R2, secondary: latest created_at
    source_sorted = sorted(
        source,
        key=lambda row: (as_float(row.get("r2"), -1e9), str(row.get("created_at", ""))),
        reverse=True,
    )
    return source_sorted[0]


def compute_recommended_version(registry: dict) -> str | None:
    versions = registry.get("versions", [])
    if not versions:
        return None
    promoted_versions = [row for row in versions if row.get("promoted")]
    source = promoted_versions or versions
    source_sorted = sorted(
        source,
        key=lambda row: (as_float(row.get("r2"), -1e9), str(row.get("created_at", ""))),
        reverse=True,
    )
    return source_sorted[0].get("model_version")


def summarize_entry(entry: dict | None, dataset_summary: dict) -> dict | None:
    if entry is None:
        return None

    year_min = int(entry.get("year_min") or dataset_summary["year_min"])
    year_max = int(entry.get("year_max") or dataset_summary["year_max"])

    return {
        "model_version": entry.get("model_version"),
        "display_name": entry.get("display_name") or entry.get("model_version"),
        "mode": entry.get("mode"),
        "best_model": entry.get("best_model"),
        "r2": as_float(entry.get("r2"), 0.0),
        "samples": int(entry.get("samples") or dataset_summary["rows"]),
        "dataset_source": entry.get("dataset_source") or entry.get("source"),
        "dataset_hash": entry.get("dataset_hash") or "",
        "evaluation_strategy": entry.get("evaluation_strategy") or "unknown",
        "test_year_min": int(entry.get("test_year_min") or 0),
        "test_year_max": int(entry.get("test_year_max") or 0),
        "year_min": year_min,
        "year_max": year_max,
        "created_at": entry.get("created_at") or "",
    }


def write_model_metrics_csv(entry: dict | None, output_path: Path) -> None:
    rows = []
    models = entry.get("models", {}) if entry is not None else {}
    if isinstance(models, dict):
        for model_name, metrics in models.items():
            rows.append(
                {
                    "Model": str(model_name),
                    "MAE": as_float((metrics or {}).get("MAE"), 0.0),
                    "RMSE": as_float((metrics or {}).get("RMSE"), 0.0),
                    "R2": as_float((metrics or {}).get("R2"), 0.0),
                }
            )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("R2", ascending=False)
    df.to_csv(output_path, index=False)


def compute_test_years(df: pd.DataFrame, entry: dict | None) -> set[int]:
    if entry is None:
        return set()

    eval_strategy = str(entry.get("evaluation_strategy") or "").strip()
    if eval_strategy == "temporal_holdout":
        years = sorted(df["Year"].dropna().astype(int).unique().tolist())
        if not years:
            return set()
        n_test_years = max(1, int(round(len(years) * 0.2)))
        return set(years[-n_test_years:])

    test_year_min = int(entry.get("test_year_min") or 0)
    test_year_max = int(entry.get("test_year_max") or 0)
    if test_year_min > 0 and test_year_max >= test_year_min:
        return set(range(test_year_min, test_year_max + 1))

    return set()


def short_version(model_version: str | None) -> str:
    text = str(model_version or "").strip()
    if len(text) <= 20:
        return text
    return f"{text[:12]}...{text[-6:]}"


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]

    dataset_path = (root / args.dataset).resolve()
    registry_path = (root / args.registry).resolve()
    output_dir = (root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not dataset_path.exists():
        raise SystemExit(f"Dataset not found: {dataset_path}")
    if not registry_path.exists():
        raise SystemExit(f"Registry not found: {registry_path}")

    df = pd.read_csv(dataset_path)
    with registry_path.open("r", encoding="utf-8") as f:
        registry = json.load(f)

    required_numeric = [
        "Year",
        "average_rain_fall_mm_per_year",
        "pesticides_tonnes",
        "avg_temp",
        "hg/ha_yield",
    ]
    for col in required_numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    dataset_summary = {
        "rows": int(len(df)),
        "countries": int(df["Area"].nunique(dropna=True)),
        "crops": int(df["Item"].nunique(dropna=True)),
        "year_min": int(df["Year"].min()),
        "year_max": int(df["Year"].max()),
    }

    active_version = registry.get("active_model_version")
    canonical_baseline_version = registry.get("baseline_model_version")
    recommended_version = compute_recommended_version(registry)

    active_entry = find_entry(registry, active_version)
    canonical_baseline_entry = find_entry(registry, canonical_baseline_version)
    report_baseline_entry = select_report_baseline_entry(registry)

    active_summary = summarize_entry(active_entry, dataset_summary)
    canonical_baseline_summary = summarize_entry(canonical_baseline_entry, dataset_summary)
    report_baseline_summary = summarize_entry(report_baseline_entry, dataset_summary)

    summary_payload = {
        "dataset": dataset_summary,
        "report_baseline": report_baseline_summary,
        "active_model": active_summary,
        "canonical_baseline": canonical_baseline_summary,
        "registry_pointers": {
            "active_model_version": active_version,
            "baseline_model_version": canonical_baseline_version,
            "recommended_model_version": recommended_version,
        },
        "selection_rule": "report_baseline = meilleure version baseline selon R2 (puis date)",
    }
    (output_dir / "baseline_summary.json").write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    write_model_metrics_csv(report_baseline_entry, output_dir / "baseline_model_metrics.csv")
    write_model_metrics_csv(active_entry, output_dir / "active_model_metrics.csv")

    # Baseline versions comparison
    baseline_rows = []
    for row in registry.get("versions", []):
        if row.get("mode") != "baseline":
            continue
        version = str(row.get("model_version") or "")
        status_tokens = []
        if version == active_version:
            status_tokens.append("Actif")
        if version == canonical_baseline_version:
            status_tokens.append("Baseline")
        if version == recommended_version:
            status_tokens.append("Recommandé")
        status = " / ".join(status_tokens) if status_tokens else "Historique"

        baseline_rows.append(
            {
                "Version": version,
                "VersionShort": short_version(version),
                "BestModel": str(row.get("best_model") or ""),
                "R2": as_float(row.get("r2"), 0.0),
                "DatasetSource": str(row.get("dataset_source") or row.get("source") or ""),
                "EvalStrategy": str(row.get("evaluation_strategy") or "unknown").replace("_", "-"),
                "YearMin": int(row.get("year_min") or dataset_summary["year_min"]),
                "YearMax": int(row.get("year_max") or dataset_summary["year_max"]),
                "Status": status,
            }
        )

    baseline_versions_df = pd.DataFrame(baseline_rows)
    if not baseline_versions_df.empty:
        baseline_versions_df = baseline_versions_df.sort_values(["R2", "Version"], ascending=[False, False])
    baseline_versions_df.to_csv(output_dir / "baseline_versions.csv", index=False)

    # Registry overview (all versions)
    overview_rows = []
    for row in registry.get("versions", []):
        version = str(row.get("model_version") or "")
        overview_rows.append(
            {
                "Version": version,
                "VersionShort": short_version(version),
                "Mode": str(row.get("mode") or ""),
                "BestModel": str(row.get("best_model") or ""),
                "R2": as_float(row.get("r2"), 0.0),
                "Status": "Actif" if version == active_version else ("Baseline" if version == canonical_baseline_version else ""),
            }
        )
    overview_df = pd.DataFrame(overview_rows)
    if not overview_df.empty:
        overview_df = overview_df.sort_values(["R2", "Version"], ascending=[False, False])
    overview_df.to_csv(output_dir / "model_registry_overview.csv", index=False)

    # Yearly analysis for report baseline evaluation context
    test_years = compute_test_years(df, report_baseline_entry)
    if not test_years:
        test_years = compute_test_years(df, canonical_baseline_entry)
    yearly_df = (
        df.groupby("Year", as_index=False)
        .agg(
            Observations=("hg/ha_yield", "count"),
            MeanYield=("hg/ha_yield", "mean"),
            MeanRain=("average_rain_fall_mm_per_year", "mean"),
            MeanTemp=("avg_temp", "mean"),
        )
        .sort_values("Year")
    )
    yearly_df["Split"] = yearly_df["Year"].apply(lambda y: "Test" if int(y) in test_years else "Train")
    yearly_df.to_csv(output_dir / "baseline_yearly_analysis.csv", index=False)

    # Missing values diagnostics
    missing_rows = []
    for col in required_numeric:
        missing_before = int(df[col].isna().sum())
        filled = df[col].fillna(df[col].median())
        missing_after = int(filled.isna().sum())
        missing_rows.append(
            {
                "Feature": col,
                "MissingBefore": missing_before,
                "MissingAfter": missing_after,
            }
        )
    pd.DataFrame(missing_rows).to_csv(output_dir / "baseline_missing_values.csv", index=False)

    # Scaling diagnostics
    scale_features = ["Year", "average_rain_fall_mm_per_year", "pesticides_tonnes", "avg_temp"]
    scale_rows = []
    for col in scale_features:
        series = df[col].dropna()
        mean_raw = float(series.mean())
        std_raw = float(series.std(ddof=0))
        if std_raw > 0:
            z = (series - mean_raw) / std_raw
        else:
            z = series * 0.0
        scale_rows.append(
            {
                "Feature": col,
                "RawMean": mean_raw,
                "RawStd": std_raw,
                "RawMin": float(series.min()),
                "RawMax": float(series.max()),
                "ZMean": float(z.mean()),
                "ZStd": float(z.std(ddof=0)),
            }
        )
    pd.DataFrame(scale_rows).to_csv(output_dir / "baseline_scaling_diagnostics.csv", index=False)

    scale_plot_rows = []
    label_map = {
        "Year": "Year",
        "average_rain_fall_mm_per_year": "Rain",
        "pesticides_tonnes": "Pesticides",
        "avg_temp": "Temp",
    }
    for row in scale_rows:
        scale_plot_rows.append(
            {
                "Feature": label_map.get(row["Feature"], row["Feature"]),
                "RawStd": row["RawStd"],
                "ZStd": row["ZStd"],
            }
        )
    pd.DataFrame(scale_plot_rows).to_csv(output_dir / "baseline_scaling_plot.csv", index=False)

    # Crop-level analysis
    crop_df = (
        df.groupby("Item", as_index=False)
        .agg(
            Observations=("hg/ha_yield", "count"),
            MeanYield=("hg/ha_yield", "mean"),
            MeanRain=("average_rain_fall_mm_per_year", "mean"),
            MeanTemp=("avg_temp", "mean"),
        )
        .sort_values("MeanYield", ascending=False)
    )
    crop_df.to_csv(output_dir / "baseline_crop_analysis.csv", index=False)

    print("Report assets generated:")
    for path in sorted(output_dir.glob("*.csv")):
        print(f"- {path.relative_to(root)}")
    print(f"- {(output_dir / 'baseline_summary.json').relative_to(root)}")


if __name__ == "__main__":
    main()
