from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional, List

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


def _money(x: float) -> str:
    try:
        return f"${float(x):,.0f}"
    except Exception:
        return ""


def _num(x: float) -> str:
    try:
        return f"{int(round(float(x))):,}"
    except Exception:
        return ""


def build_intervention_brief(
    pdf_path: str | Path,
    recommendations: pd.DataFrame,
    scored: pd.DataFrame,
    drilldown_id: Optional[str] = "SCN_002",
) -> None:
    """
    PDF contents:
      Page 1 — Executive overview + decision rules + recommendations table
      Page 2 — Single-scenario drilldown (decision transparency)
    """
    pdf_path = Path(pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        spaceAfter=6,
        textColor=colors.HexColor("#111827"),
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        spaceBefore=8,
        spaceAfter=4,
        textColor=colors.HexColor("#111827"),
    )
    small = ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        spaceAfter=3,
        textColor=colors.HexColor("#374151"),
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        spaceAfter=5,
        textColor=colors.HexColor("#111827"),
    )

    # Table cell styles: wrap but do NOT split mid-word
    header_cell = ParagraphStyle(
        "HeaderCell",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
        splitLongWords=0,
        wordWrap="LTR",
    )
    cell = ParagraphStyle(
        "Cell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=10.5,
        textColor=colors.HexColor("#111827"),
        splitLongWords=0,
        wordWrap="LTR",
    )

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=landscape(letter),
        rightMargin=0.45 * inch,
        leftMargin=0.45 * inch,
        topMargin=0.45 * inch,
        bottomMargin=0.45 * inch,
        title="Intervention Recommendation Brief",
    )

    story: List[object] = []

    # =========================================================
    # PAGE 1 — OVERVIEW
    # =========================================================
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    story.append(Paragraph("Intervention Recommendation Brief", title))
    story.append(Paragraph(f"Generated: {now_str}", small))
    story.append(Paragraph("Input: data/sample_inputs.csv", small))
    story.append(Spacer(1, 4))

    # --- Executive Summary (NEW) ---
    story.append(Paragraph("Executive Summary", h2))

    rec = recommendations.copy()
    n = int(rec["scenario_id"].nunique()) if "scenario_id" in rec.columns else len(rec)
    sla_met = int(rec["sla_met"].sum()) if "sla_met" in rec.columns else 0
    sla_miss = n - sla_met
    total_cost = float(rec["total_cost"].sum()) if "total_cost" in rec.columns else 0.0

    # short “what happened” bullets
    bullets = [
        f"Scenarios evaluated: {n}",
        f"SLA outcomes: {sla_met} met, {sla_miss} missed",
        f"Projected total cost (recommended actions): {_money(total_cost)}",
    ]

    # add top recommendations (compact)
    try:
        top_lines = []
        for _, r in rec.iterrows():
            top_lines.append(f"{r['scenario_id']} ({r['site_id']}): {r['option']} — {_money(r['total_cost'])}")
        bullets.append("Recommended actions: " + "; ".join(top_lines))
    except Exception:
        pass

    story.append(Paragraph("<br/>".join([f"• {b}" for b in bullets]), body))

    # Decision rules
    story.append(Paragraph("Decision Rules", h2))
    rules = [
        "If any feasible option meets SLA, select the lowest total-cost SLA-met option.",
        "If no option can meet SLA, allow a controlled premium over the cheapest option.",
        "Within that premium window, minimize unmet units; tie-break by total cost.",
        "Total cost includes intervention cost, late cost, and SLA breach penalties.",
    ]
    story.append(Paragraph("<br/>".join([f"• {r}" for r in rules]), body))

    # Recommendations table
    story.append(Paragraph("Recommended Actions (Overview)", h2))

    headers = ["Scenario", "Site", "Action", "Gap", "Recov", "Unmet", "SLA", "Base", "Cap", "Total", "Rationale"]
    table_data: List[List[object]] = [[Paragraph(h, header_cell) for h in headers]]

    for _, r in rec.iterrows():
        sla_txt = "MET" if bool(r.get("sla_met", False)) else "MISS"
        table_data.append(
            [
                Paragraph(str(r.get("scenario_id", "")), cell),
                Paragraph(str(r.get("site_id", "")), cell),
                Paragraph(str(r.get("option", "")), cell),
                Paragraph(_num(r.get("gap_units", 0)), cell),
                Paragraph(_num(r.get("recovered_units", 0)), cell),
                Paragraph(_num(r.get("unmet_units", 0)), cell),
                Paragraph(sla_txt, cell),
                Paragraph(_money(r.get("baseline_total_cost", 0)), cell),
                Paragraph(_money(r.get("premium_cap_total_cost", 0)), cell),
                Paragraph(_money(r.get("total_cost", 0)), cell),
                Paragraph(str(r.get("explanation", "")), cell),
            ]
        )

    # Dynamic widths: must sum to doc.width to prevent clipping
    W = doc.width
    fracs = [0.08, 0.07, 0.10, 0.06, 0.06, 0.06, 0.05, 0.07, 0.07, 0.07]
    fixed = [W * f for f in fracs]
    col_widths = fixed + [W - sum(fixed)]

    overview = Table(table_data, colWidths=col_widths, repeatRows=1)
    overview.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ALIGN", (3, 1), (9, -1), "RIGHT"),
                ("ALIGN", (6, 1), (6, -1), "CENTER"),
            ]
        )
    )
    story.append(overview)
    story.append(Spacer(1, 4))
    story.append(Paragraph("Legend: Recov = recovered units; Base = baseline total cost; Cap = premium cap; costs in USD.", small))

    # =========================================================
    # PAGE 2 — DRILLDOWN
    # =========================================================
    if drilldown_id:
        story.append(PageBreak())
        story.append(Paragraph(f"Scenario Drilldown: {drilldown_id}", title))

        sd = scored[scored["scenario_id"] == drilldown_id].copy()
        if sd.empty:
            story.append(Paragraph("No data available for this scenario.", body))
        else:
            # Which option was chosen?
            chosen_row = rec[rec["scenario_id"] == drilldown_id]
            chosen = chosen_row.iloc[0]["option"] if not chosen_row.empty else None

            # Display order consistent with SERVICE-FIRST policy:
            # - If any SLA met: cheapest SLA-met wins
            # - Else: minimize unmet (within cap), tie-break by total cost
            if sd["sla_met"].any():
                sd = sd.sort_values(["sla_met", "total_cost"], ascending=[False, True])
            else:
                sd = sd.sort_values(["unmet_units", "total_cost"], ascending=[True, True])

            story.append(Paragraph("Option Comparison", h2))

            headers2 = ["Option", "Recovered", "Unmet", "SLA", "Within Cap", "Intervention", "Service", "Total"]
            table2_data: List[List[object]] = [[Paragraph(h, header_cell) for h in headers2]]

            for _, r in sd.iterrows():
                is_chosen = (chosen is not None) and (r.get("option") == chosen)
                mark = "★ " if is_chosen else ""
                within_cap = bool(r.get("total_cost", 0) <= r.get("premium_cap_total_cost", float("inf")))
                table2_data.append(
                    [
                        Paragraph(mark + str(r.get("option", "")), cell),
                        Paragraph(_num(r.get("recovered_units", 0)), cell),
                        Paragraph(_num(r.get("unmet_units", 0)), cell),
                        Paragraph("MET" if bool(r.get("sla_met", False)) else "MISS", cell),
                        Paragraph("YES" if within_cap else "NO", cell),
                        Paragraph(_money(r.get("intervention_cost", 0)), cell),
                        Paragraph(_money(r.get("service_cost", 0)), cell),
                        Paragraph(_money(r.get("total_cost", 0)), cell),
                    ]
                )

            w2 = doc.width
            # widths sum to 1.0
            col2 = [0.18, 0.10, 0.10, 0.07, 0.10, 0.15, 0.15, 0.15]
            drill = Table(table2_data, colWidths=[w2 * c for c in col2], repeatRows=1)
            drill.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                        ("ALIGN", (3, 1), (4, -1), "CENTER"),
                    ]
                )
            )

            story.append(drill)
            story.append(Spacer(1, 6))
            story.append(Paragraph("★ indicates the recommended option.", small))

    doc.build(story)
