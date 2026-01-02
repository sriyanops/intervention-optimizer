from __future__ import annotations

import pandas as pd
import pandas as pd


def load_inputs(path):
    """
    Load raw scenario inputs from CSV.
    This is intentionally thin: parsing & validation live elsewhere.
    """
    return pd.read_csv(path)


OPTIONS = ["do_nothing", "overtime", "temp_labor", "reroute", "outsource"]


def simulate_options(inputs: pd.DataFrame) -> pd.DataFrame:
    """
    Create one row per (scenario_id, option). Computes:
    - gap_units
    - max_allowed_unmet_units (based on SLA fill-rate target)
    - recovered_units per option
    - unmet_units
    """
    base = inputs.copy()

    # Derived fields
    base["gap_units"] = (base["forecast_demand_units"] - base["available_capacity_units"]).clip(lower=0)

    # SLA target is a fill-rate. Allowed unmet = demand * (1 - fill_rate)
    base["max_allowed_unmet_units"] = base["forecast_demand_units"] * (1.0 - base["sla_target_fill_rate"])

    # Expand by options
    expanded = base.loc[base.index.repeat(len(OPTIONS))].copy()
    expanded["option"] = OPTIONS * len(base)

    expanded["recovered_units"] = 0.0

    # Overtime recovery: min(gap, max_ot_hours * ot_units_per_hour)
    mask = expanded["option"].eq("overtime")
    max_ot_units = expanded.loc[mask, "max_ot_hours"] * expanded.loc[mask, "ot_units_per_hour"]
    expanded.loc[mask, "recovered_units"] = pd.concat(
        [expanded.loc[mask, "gap_units"], max_ot_units], axis=1
    ).min(axis=1)

    # Temp labor recovery: min(gap, max_temp_units)
    mask = expanded["option"].eq("temp_labor")
    expanded.loc[mask, "recovered_units"] = pd.concat(
        [expanded.loc[mask, "gap_units"], expanded.loc[mask, "max_temp_units"]], axis=1
    ).min(axis=1)

    # Reroute recovery: min(gap, max_reroute_units)
    mask = expanded["option"].eq("reroute")
    expanded.loc[mask, "recovered_units"] = pd.concat(
        [expanded.loc[mask, "gap_units"], expanded.loc[mask, "max_reroute_units"]], axis=1
    ).min(axis=1)

    # Outsource recovery: min(gap, max_outsource_units)
    mask = expanded["option"].eq("outsource")
    expanded.loc[mask, "recovered_units"] = pd.concat(
        [expanded.loc[mask, "gap_units"], expanded.loc[mask, "max_outsource_units"]], axis=1
    ).min(axis=1)

    # Unmet after intervention
    expanded["unmet_units"] = (expanded["gap_units"] - expanded["recovered_units"]).clip(lower=0)

    return expanded
