from pathlib import Path
import argparse

import pandas as pd

from scenarios import load_inputs
from model import evaluate_all_options, choose_recommendation
from report_pdf import build_intervention_brief


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--drilldown-id", type=str, default="SCN_002")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    data_path = root / "data" / "sample_inputs.csv"

    if not data_path.exists():
        raise FileNotFoundError(f"Missing input file: {data_path}")

    df = load_inputs(data_path)

    scored = evaluate_all_options(df)
    recommendations = choose_recommendation(scored)

    # Console output (kept intentionally)
    print("\n=== RECOMMENDATIONS (TOP OPTION PER SCENARIO) ===")
    print(recommendations.to_string(index=False))

    # CSV outputs
    out_dir = root / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    scored_path = out_dir / "intervention_option_results.csv"
    recs_path = out_dir / "recommendations.csv"
    pdf_path = out_dir / "intervention_brief.pdf"

    scored.to_csv(scored_path, index=False)
    recommendations.to_csv(recs_path, index=False)

    print(f"\nSaved: {scored_path}")
    print(f"Saved: {recs_path}")

    # PDF (2 pages)
    build_intervention_brief(
        pdf_path=pdf_path,
        recommendations=recommendations,
        scored=scored,
        drilldown_id=args.drilldown_id,
    )

    print(f"Saved: {pdf_path}")


if __name__ == "__main__":
    main()
