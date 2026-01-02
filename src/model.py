from __future__ import annotations

import pandas as pd

from scenarios import simulate_options
from constraints import flag_feasible
from costs import compute_costs_and_sla
from explain import build_explanations


def evaluate_all_options(inputs: pd.DataFrame) -> pd.DataFrame:
    """
    Decision rules (v1c):
    1) Drop infeasible options
    2) If ANY option meets SLA:
         - keep only SLA-met
         - rank by total_cost
       Else (NONE meet SLA):
         - baseline = cheapest total_cost
         - keep options within baseline * service_premium_cap
         - rank by unmet_units, then total_cost

    Adds transparency columns:
    - baseline_total_cost
    - premium_cap_total_cost
    """
    options = simulate_options(inputs)
    options = flag_feasible(options)
    options = compute_costs_and_sla(options)

    feasible = options[options["feasible"]].copy()

    # SLA-achievable flag per scenario
    feasible["sla_any"] = feasible.groupby("scenario_id")["sla_met"].transform("any")

    # premium cap input (default 1.15)
    if "service_premium_cap" not in feasible.columns:
        feasible["service_premium_cap"] = 1.15
    feasible["service_premium_cap"] = feasible["service_premium_cap"].fillna(1.15)

    # Baseline + cap values per scenario (computed on feasible set)
    feasible["baseline_total_cost"] = feasible.groupby("scenario_id")["total_cost"].transform("min")
    feasible["premium_cap_total_cost"] = feasible["baseline_total_cost"] * feasible["service_premium_cap"]

    # A) SLA achievable -> keep only SLA-met, rank by total_cost
    with_sla = feasible[feasible["sla_any"]].copy()
    with_sla = with_sla[with_sla["sla_met"]].copy()
    with_sla = with_sla.sort_values(["scenario_id", "total_cost"], ascending=[True, True])
    with_sla["rank"] = with_sla.groupby("scenario_id").cumcount() + 1

    # B) SLA not achievable -> apply cap window then rank by unmet then cost
    no_sla = feasible[~feasible["sla_any"]].copy()

    if not no_sla.empty:
        no_sla = no_sla[no_sla["total_cost"] <= no_sla["premium_cap_total_cost"]].copy()

        # Edge-case fallback: if cap filters everything (should be rare), keep baseline-cheapest only
        if no_sla.empty:
            fallback = feasible[~feasible["sla_any"]].copy()
            baseline = fallback.groupby("scenario_id")["total_cost"].transform("min")
            no_sla = fallback[fallback["total_cost"] == baseline].copy()

        no_sla = no_sla.sort_values(
            ["scenario_id", "unmet_units", "total_cost"],
            ascending=[True, True, True],
        )
        no_sla["rank"] = no_sla.groupby("scenario_id").cumcount() + 1

    out = pd.concat([with_sla, no_sla], ignore_index=True)

    # Clean helper column
    out = out.drop(columns=["sla_any"], errors="ignore")

    out = build_explanations(out)
    return out


def choose_recommendation(scored: pd.DataFrame) -> pd.DataFrame:
    return (
        scored.sort_values(["scenario_id", "rank"])
        .groupby("scenario_id", as_index=False)
        .head(1)
    )




