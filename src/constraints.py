from __future__ import annotations

import pandas as pd


def flag_feasible(df: pd.DataFrame) -> pd.DataFrame:
    """
    Feasibility rules (v1):
    - do_nothing: always feasible
    - overtime: requires max_ot_hours > 0 and ot_units_per_hour > 0
    - temp_labor/reroute/outsource: requires cap >= 0
    """
    out = df.copy()
    out["feasible"] = True

    # Overtime
    mask = out["option"].eq("overtime")
    out.loc[mask, "feasible"] = (out.loc[mask, "max_ot_hours"] > 0) & (out.loc[mask, "ot_units_per_hour"] > 0)

    # Caps must be non-negative
    for opt, cap_col in [
        ("temp_labor", "max_temp_units"),
        ("reroute", "max_reroute_units"),
        ("outsource", "max_outsource_units"),
    ]:
        mask = out["option"].eq(opt)
        out.loc[mask, "feasible"] = out.loc[mask, cap_col] >= 0

    # Do nothing always feasible
    out.loc[out["option"].eq("do_nothing"), "feasible"] = True

    return out
