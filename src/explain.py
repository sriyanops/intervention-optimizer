from __future__ import annotations

import pandas as pd


def build_explanations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a short, human-readable explanation for each intervention option.
    Presentation-only; does not affect scoring or ranking.
    """
    out = df.copy()

    def _explain(r: pd.Series) -> str:
        option = str(r.get("option", ""))

        recovered = int(round(float(r.get("recovered_units", 0.0))))
        unmet = int(round(float(r.get("unmet_units", 0.0))))

        if option == "do_nothing":
            return f"No action taken; {unmet} units unmet."

        if option == "overtime":
            hrs = round(float(r.get("ot_hours_used", 0.0)), 1)
            return f"Overtime recovers {recovered} units (~{hrs} OT hours)."

        if option == "temp_labor":
            return f"Temp labor recovers {recovered} units."

        if option == "reroute":
            return f"Rerouting recovers {recovered} units."

        if option == "outsource":
            return f"Outsourcing recovers {recovered} units."

        return "Intervention evaluated."

    out["explanation"] = out.apply(_explain, axis=1)
    return out

