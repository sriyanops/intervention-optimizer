from __future__ import annotations

import numpy as np
import pandas as pd


def compute_costs_and_sla(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes:
    - sla_met
    - intervention_cost
    - service_cost (late cost + breach penalty)
    - total_cost
    """
    out = df.copy()

    # SLA met if unmet units <= allowed unmet units
    out["sla_met"] = out["unmet_units"] <= out["max_allowed_unmet_units"]

    # Intervention cost defaults
    out["intervention_cost"] = 0.0

    # Overtime: recovered_units / ot_units_per_hour * ot_cost_per_hour
    mask = out["option"].eq("overtime")
    denom = out.loc[mask, "ot_units_per_hour"].replace(0, np.nan)
    ot_hours_used = (out.loc[mask, "recovered_units"] / denom).fillna(0.0)
    out.loc[mask, "ot_hours_used"] = ot_hours_used
    out.loc[mask, "intervention_cost"] = ot_hours_used * out.loc[mask, "ot_cost_per_hour"]

    # Temp labor
    mask = out["option"].eq("temp_labor")
    out.loc[mask, "intervention_cost"] = out.loc[mask, "recovered_units"] * out.loc[mask, "temp_cost_per_unit"]

    # Reroute
    mask = out["option"].eq("reroute")
    out.loc[mask, "intervention_cost"] = out.loc[mask, "recovered_units"] * out.loc[mask, "reroute_cost_per_unit"]

    # Outsource
    mask = out["option"].eq("outsource")
    out.loc[mask, "intervention_cost"] = out.loc[mask, "recovered_units"] * out.loc[mask, "outsourcing_cost_per_unit"]

    # Service cost = unmet * late_cost + breach penalty if SLA not met
    out["service_cost"] = out["unmet_units"] * out["late_cost_per_unit"]
    out["service_cost"] = out["service_cost"] + np.where(out["sla_met"], 0.0, out["sla_breach_penalty"])

    out["total_cost"] = out["intervention_cost"] + out["service_cost"]

    # Fill ot_hours_used for non-overtime rows
    if "ot_hours_used" not in out.columns:
        out["ot_hours_used"] = 0.0
    out["ot_hours_used"] = out["ot_hours_used"].fillna(0.0)

    return out
