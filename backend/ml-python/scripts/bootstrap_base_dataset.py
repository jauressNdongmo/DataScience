from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import re
from pathlib import Path
import unicodedata
import urllib.request
import zipfile

import pandas as pd


FAOSTAT_YIELD_URL = (
    "https://bulks-faostat.fao.org/production/"
    "Production_Crops_Livestock_E_All_Data_(Normalized).zip"
)
FAOSTAT_PESTICIDES_URL = (
    "https://bulks-faostat.fao.org/production/"
    "Inputs_Pesticides_Use_E_All_Data_(Normalized).zip"
)
FAOSTAT_TEMP_CHANGE_URL = (
    "https://bulks-faostat.fao.org/production/"
    "Environment_Temperature_change_E_All_Data_(Normalized).zip"
)
WB_PRECIP_INDICATOR = "AG.LND.PRCP.MM"
WB_PRECIP_URL = (
    "https://api.worldbank.org/v2/country/all/indicator/"
    f"{WB_PRECIP_INDICATOR}?format=json&per_page=20000"
)

CROP_MAP = {
    "Cassava, fresh": "Cassava",
    "Maize (corn)": "Maize",
    "Plantains and cooking bananas": "Plantains and others",
    "Potatoes": "Potatoes",
    "Rice": "Rice, paddy",
    "Sorghum": "Sorghum",
    "Soya beans": "Soybeans",
    "Sweet potatoes": "Sweet potatoes",
    "Wheat": "Wheat",
    "Yams": "Yams",
}

WB_NAME_OVERRIDES = {
    "bolivia plurinational state of": "bolivia",
    "china mainland": "china",
    "democratic peoples republic of korea": "korea dem peoples rep",
    "democratic republic of the congo": "congo dem rep",
    "iran islamic republic of": "iran islamic rep",
    "lao peoples democratic republic": "lao pdr",
    "micronesia federated states of": "micronesia fed sts",
    "occupied palestinian territory": "west bank and gaza",
    "republic of korea": "korea rep",
    "republic of moldova": "moldova",
    "syrian arab republic": "syrian arab republic",
    "the former yugoslav republic of macedonia": "north macedonia",
    "united republic of tanzania": "tanzania",
    "venezuela bolivarian republic of": "venezuela rb",
    "viet nam": "vietnam",
    "yemen": "yemen rep",
}


def normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[()'.,-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def download_file(url: str, destination: Path, force: bool = False) -> None:
    if destination.exists() and not force:
        print(f"[skip] {destination.name} existe deja")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    print(f"[download] {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "AgriDataBootstrap/1.0"})
    with urllib.request.urlopen(req, timeout=120) as response:
        data = response.read()
    destination.write_bytes(data)
    print(f"[ok] {destination} ({destination.stat().st_size / (1024 * 1024):.1f} MB)")


def get_csv_name_from_zip(zip_path: Path) -> str:
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.lower().endswith(".csv"):
                return name
    raise RuntimeError(f"Aucun CSV trouve dans {zip_path}")


def build_yield_dataframe(yield_zip: Path, min_year: int) -> pd.DataFrame:
    csv_name = get_csv_name_from_zip(yield_zip)
    filtered_parts: list[pd.DataFrame] = []

    with zipfile.ZipFile(yield_zip) as zf:
        with zf.open(csv_name) as csv_file:
            for chunk in pd.read_csv(
                csv_file,
                usecols=["Area", "Item", "Element", "Year", "Unit", "Value"],
                chunksize=350_000,
            ):
                part = chunk[
                    (chunk["Element"] == "Yield")
                    & (chunk["Unit"] == "kg/ha")
                    & (chunk["Item"].isin(CROP_MAP.keys()))
                    & (chunk["Year"] >= min_year)
                ].copy()

                if part.empty:
                    continue

                part["Item"] = part["Item"].map(CROP_MAP)
                part["Value"] = pd.to_numeric(part["Value"], errors="coerce") * 10.0
                part = part.rename(columns={"Value": "hg/ha_yield"})
                filtered_parts.append(part[["Area", "Item", "Year", "hg/ha_yield"]])

    if not filtered_parts:
        raise RuntimeError("Aucune ligne rendement extraite depuis FAOSTAT")

    df = pd.concat(filtered_parts, ignore_index=True)
    df = (
        df.groupby(["Area", "Item", "Year"], as_index=False)["hg/ha_yield"]
        .mean()
        .sort_values(["Area", "Item", "Year"])
    )
    return df


def build_pesticides_dataframe(pesticides_zip: Path, min_year: int) -> pd.DataFrame:
    csv_name = get_csv_name_from_zip(pesticides_zip)
    with zipfile.ZipFile(pesticides_zip) as zf:
        with zf.open(csv_name) as csv_file:
            df = pd.read_csv(
                csv_file,
                usecols=["Area", "Item", "Element", "Year", "Unit", "Value"],
            )

    df = df[
        (df["Item"] == "Pesticides (total)")
        & (df["Element"] == "Agricultural Use")
        & (df["Unit"] == "t")
        & (df["Year"] >= min_year)
    ].copy()

    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df = df.rename(columns={"Value": "pesticides_tonnes"})
    df = df[["Area", "Year", "pesticides_tonnes"]]
    df = df.groupby(["Area", "Year"], as_index=False)["pesticides_tonnes"].mean()
    return df


def build_temp_change_dataframe(temp_zip: Path, min_year: int) -> pd.DataFrame:
    csv_name = get_csv_name_from_zip(temp_zip)
    with zipfile.ZipFile(temp_zip) as zf:
        with zf.open(csv_name) as csv_file:
            df = pd.read_csv(
                csv_file,
                usecols=["Area", "Months", "Element", "Year", "Unit", "Value"],
            )

    df = df[
        (df["Months"] == "Meteorological year")
        & (df["Element"] == "Temperature change")
        & (df["Unit"] == "°C")
        & (df["Year"] >= min_year)
    ].copy()

    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df = df.rename(columns={"Value": "temp_change_c"})
    df = df[["Area", "Year", "temp_change_c"]]
    df = df.groupby(["Area", "Year"], as_index=False)["temp_change_c"].mean()
    return df


def download_worldbank_precip(raw_dir: Path, force: bool = False) -> Path:
    out = raw_dir / "worldbank_precipitation.json"
    if out.exists() and not force:
        print(f"[skip] {out.name} existe deja")
        return out

    print(f"[download] {WB_PRECIP_URL}")
    req = urllib.request.Request(WB_PRECIP_URL, headers={"User-Agent": "AgriDataBootstrap/1.0"})
    with urllib.request.urlopen(req, timeout=120) as response:
        payload = response.read().decode("utf-8")
    out.write_text(payload, encoding="utf-8")
    print(f"[ok] {out}")
    return out


def build_precipitation_dataframe(wb_json_path: Path) -> pd.DataFrame:
    payload = json.loads(wb_json_path.read_text(encoding="utf-8"))
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []

    records = []
    latest_year = 0
    for row in rows:
        try:
            year = int(row.get("date"))
            latest_year = max(latest_year, year)
        except Exception:
            continue

        value = row.get("value")
        if value is None:
            continue

        records.append(
            {
                "country": row.get("country", {}).get("value"),
                "year": year,
                "average_rain_fall_mm_per_year": float(value),
            }
        )

    if not records:
        raise RuntimeError("Aucune donnee precipitation World Bank exploitable")

    df = pd.DataFrame.from_records(records)
    df = df.dropna(subset=["country", "average_rain_fall_mm_per_year"])
    df = df.sort_values(["country", "year"])

    latest = (
        df.groupby("country", as_index=False)
        .tail(1)
        .rename(columns={"country": "Area"})[["Area", "average_rain_fall_mm_per_year"]]
    )
    latest.attrs["latest_year"] = latest_year
    return latest


def calibrate_absolute_temperature(
    temp_change_df: pd.DataFrame,
    legacy_df: pd.DataFrame,
) -> tuple[pd.DataFrame, float, int]:
    legacy_temp = (
        legacy_df.groupby(["Area", "Year"], as_index=False)["avg_temp"]
        .mean()
        .rename(columns={"avg_temp": "legacy_avg_temp"})
    )

    overlap = temp_change_df.merge(legacy_temp, on=["Area", "Year"], how="inner")
    overlap["offset"] = overlap["legacy_avg_temp"] - overlap["temp_change_c"]

    if overlap.empty:
        global_offset = float(legacy_df["avg_temp"].median())
        country_offsets = pd.DataFrame(columns=["Area", "offset"])
    else:
        country_offsets = (
            overlap.groupby("Area", as_index=False)["offset"].median()
        )
        global_offset = float(overlap["offset"].median())

    temp_abs = temp_change_df.merge(country_offsets, on="Area", how="left")
    temp_abs["offset"] = temp_abs["offset"].fillna(global_offset)
    temp_abs["avg_temp"] = temp_abs["temp_change_c"] + temp_abs["offset"]

    return temp_abs[["Area", "Year", "avg_temp"]], global_offset, int(len(overlap))


def map_precip_to_fao_areas(
    fao_areas: pd.Series,
    wb_precip: pd.DataFrame,
    legacy_df: pd.DataFrame,
) -> tuple[pd.DataFrame, int, list[str]]:
    wb_precip = wb_precip.copy()
    wb_precip["norm"] = wb_precip["Area"].map(normalize_name)
    wb_map = dict(zip(wb_precip["norm"], wb_precip["average_rain_fall_mm_per_year"]))

    legacy_rain = legacy_df.groupby("Area")["average_rain_fall_mm_per_year"].median().to_dict()
    global_rain = float(wb_precip["average_rain_fall_mm_per_year"].median())

    records = []
    unresolved = []
    wb_hits = 0

    for area in sorted(fao_areas.dropna().unique().tolist()):
        norm = normalize_name(area)
        mapped_norm = WB_NAME_OVERRIDES.get(norm, norm)

        rain = wb_map.get(mapped_norm)
        source = "worldbank"
        if rain is None:
            rain = legacy_rain.get(area)
            source = "legacy"
        if rain is None:
            rain = global_rain
            source = "global_median"

        if source == "worldbank":
            wb_hits += 1
        else:
            unresolved.append(area)

        records.append(
            {
                "Area": area,
                "average_rain_fall_mm_per_year": float(rain),
            }
        )

    return pd.DataFrame.from_records(records), wb_hits, unresolved


def build_dataset(
    raw_dir: Path,
    output_csv: Path,
    metadata_json: Path,
    min_year: int,
    max_year: int | None,
    force_download: bool,
) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)

    yield_zip = raw_dir / "faostat_yield.zip"
    pesticides_zip = raw_dir / "faostat_pesticides.zip"
    temp_zip = raw_dir / "faostat_temp_change.zip"

    download_file(FAOSTAT_YIELD_URL, yield_zip, force=force_download)
    download_file(FAOSTAT_PESTICIDES_URL, pesticides_zip, force=force_download)
    download_file(FAOSTAT_TEMP_CHANGE_URL, temp_zip, force=force_download)
    wb_json = download_worldbank_precip(raw_dir, force=force_download)

    legacy_path = output_csv
    if not legacy_path.exists():
        raise RuntimeError(
            f"Dataset legacy introuvable pour calibration temperature: {legacy_path}"
        )

    legacy_df = pd.read_csv(legacy_path)
    if "Unnamed: 0" in legacy_df.columns:
        legacy_df = legacy_df.drop(columns=["Unnamed: 0"])

    print("[build] extraction rendement")
    yield_df = build_yield_dataframe(yield_zip, min_year=min_year)
    print("[build] extraction pesticides")
    pesticides_df = build_pesticides_dataframe(pesticides_zip, min_year=min_year)
    print("[build] extraction temperature")
    temp_change_df = build_temp_change_dataframe(temp_zip, min_year=min_year)
    print("[build] extraction precipitation")
    wb_precip_df = build_precipitation_dataframe(wb_json)

    temp_abs_df, global_offset, overlap_rows = calibrate_absolute_temperature(temp_change_df, legacy_df)
    rain_df, wb_hits, unresolved_rain = map_precip_to_fao_areas(
        yield_df["Area"], wb_precip_df, legacy_df
    )

    dataset = yield_df.merge(pesticides_df, on=["Area", "Year"], how="left")
    dataset = dataset.merge(temp_abs_df, on=["Area", "Year"], how="left")
    dataset = dataset.merge(rain_df, on="Area", how="left")

    dataset = dataset.sort_values(["Area", "Item", "Year"]).reset_index(drop=True)

    dataset["pesticides_tonnes"] = (
        dataset.groupby("Area")["pesticides_tonnes"].transform(lambda s: s.ffill().bfill())
    )
    dataset["avg_temp"] = (
        dataset.groupby("Area")["avg_temp"].transform(lambda s: s.ffill().bfill())
    )

    dataset["Year"] = dataset["Year"].astype(int)

    if max_year is not None:
        dataset = dataset[dataset["Year"] <= max_year]

    required = [
        "Area",
        "Item",
        "Year",
        "hg/ha_yield",
        "average_rain_fall_mm_per_year",
        "pesticides_tonnes",
        "avg_temp",
    ]
    dataset = dataset[required].dropna().copy()

    dataset["hg/ha_yield"] = pd.to_numeric(dataset["hg/ha_yield"], errors="coerce")
    dataset["average_rain_fall_mm_per_year"] = pd.to_numeric(
        dataset["average_rain_fall_mm_per_year"], errors="coerce"
    )
    dataset["pesticides_tonnes"] = pd.to_numeric(dataset["pesticides_tonnes"], errors="coerce")
    dataset["avg_temp"] = pd.to_numeric(dataset["avg_temp"], errors="coerce")

    dataset = dataset.dropna().sort_values(["Area", "Item", "Year"]).reset_index(drop=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_path = output_csv.with_name(f"{output_csv.stem}.backup.{timestamp}.csv")
    if output_csv.exists():
        output_csv.replace(backup_path)
        print(f"[backup] {backup_path}")

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(output_csv, index=True)

    wb_payload = json.loads(wb_json.read_text(encoding="utf-8"))
    wb_rows = wb_payload[1] if isinstance(wb_payload, list) and len(wb_payload) > 1 else []
    wb_latest_year = max(
        (int(row.get("date")) for row in wb_rows if row.get("date") and str(row.get("date")).isdigit()),
        default=0,
    )

    metadata = {
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_path": str(output_csv),
        "rows": int(len(dataset)),
        "countries": int(dataset["Area"].nunique()),
        "crops": int(dataset["Item"].nunique()),
        "year_min": int(dataset["Year"].min()),
        "year_max": int(dataset["Year"].max()),
        "source_year_max": {
            "faostat_yield": int(yield_df["Year"].max()),
            "faostat_pesticides": int(pesticides_df["Year"].max()),
            "faostat_temperature_change": int(temp_change_df["Year"].max()),
            "worldbank_precip_latest_year": int(wb_latest_year),
        },
        "temperature_calibration": {
            "overlap_rows": overlap_rows,
            "global_offset_c": global_offset,
        },
        "precipitation_mapping": {
            "worldbank_direct_hits": wb_hits,
            "fallback_count": len(unresolved_rain),
            "fallback_areas_sample": unresolved_rain[:30],
        },
        "sources": {
            "faostat_yield": FAOSTAT_YIELD_URL,
            "faostat_pesticides": FAOSTAT_PESTICIDES_URL,
            "faostat_temperature_change": FAOSTAT_TEMP_CHANGE_URL,
            "worldbank_precipitation": WB_PRECIP_URL,
        },
    }

    metadata_json.parent.mkdir(parents=True, exist_ok=True)
    metadata_json.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        "[done] dataset="
        f"{output_csv} | rows={metadata['rows']} | countries={metadata['countries']} "
        f"| crops={metadata['crops']} | years={metadata['year_min']}-{metadata['year_max']}"
    )
    print(f"[done] metadata={metadata_json}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Telecharge et construit le dataset de base pour le modele agricole "
            "(compatible backend/ml-python/data/yield_df.csv)."
        )
    )
    parser.add_argument(
        "--raw-dir",
        default="backend/ml-python/data/raw",
        help="Dossier des fichiers telecharges",
    )
    parser.add_argument(
        "--output-csv",
        default="backend/ml-python/data/yield_df.csv",
        help="Chemin du dataset final",
    )
    parser.add_argument(
        "--metadata-json",
        default="backend/ml-python/data/metadata.json",
        help="Chemin du metadata de generation",
    )
    parser.add_argument("--min-year", type=int, default=1990)
    parser.add_argument("--max-year", type=int, default=None)
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Retelecharge meme si les fichiers existent",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_dataset(
        raw_dir=Path(args.raw_dir),
        output_csv=Path(args.output_csv),
        metadata_json=Path(args.metadata_json),
        min_year=args.min_year,
        max_year=args.max_year,
        force_download=args.force_download,
    )


if __name__ == "__main__":
    main()
