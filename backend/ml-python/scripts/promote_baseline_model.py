from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from app.model import YieldModelService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Entraine et promeut explicitement le modele baseline sans lancer l'API FastAPI."
    )
    parser.add_argument(
        "--csv",
        default="backend/ml-python/data/yield_df.csv",
        help="Chemin du dataset baseline",
    )
    parser.add_argument(
        "--artifacts-dir",
        default="backend/ml-python/artifacts",
        help="Dossier des artefacts modele",
    )
    parser.add_argument(
        "--source",
        default="manual-baseline-cli",
        help="Tag source pour le registry",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"Dataset introuvable: {csv_path}")

    df = pd.read_csv(csv_path)
    service = YieldModelService(artifacts_dir=args.artifacts_dir)

    result = service.train(
        df,
        mode="baseline",
        source=args.source,
        promote_if_better=False,
        replace_dataset=True,
    )

    print("Baseline actif mis a jour:")
    print(f"- best_model: {result['best_model']}")
    print(f"- r2: {result['r2']:.4f}")
    print(f"- samples: {result['samples']}")
    print(f"- active_model_version: {result['active_model_version']}")


if __name__ == "__main__":
    main()
