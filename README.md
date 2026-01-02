# Operations Intervention Optimizer

A Python-based operations decision-support tool for evaluating short-term capacity intervention options under cost, service, and SLA constraints.  The system compares feasible operational actions, quantifies tradeoffs between cost and service outcomes, and recommends the optimal intervention with full decision transparency.

This project is designed for operations analysts, operations managers, and reviewers evaluating decision logic under imperfect conditions. It reflects how internal operations decision-support tools are typically structured in enterprise environments — with an emphasis on explainability, auditability, and disciplined tradeoff handling.


## What This Tool Does

### Problem This Tool Solves

Operational teams frequently face short-term capacity gaps where **no option cleanly meets demand or SLA requirements**. Available interventions often involve unavoidable tradeoffs:

- Lower-cost actions may leave significant unmet volume.
- Higher-cost actions may reduce service risk but increase spend.
- In some scenarios, **meeting SLA is impossible regardless of intervention**.

Without a structured decision framework, teams risk making inconsistent or ad-hoc decisions that are difficult to justify or audit after the fact.

This tool formalizes that decision process by:
- evaluating all feasible intervention options,
- quantifying cost and service impact for each option,
- and applying a consistent decision policy to select the best action per scenario.

The system ingests scenario-level operational inputs and produces:

- Option-level recovery and unmet volume estimates  
- SLA feasibility assessment  
- Intervention, service, and total cost calculations  
- Rule-based intervention selection  
- Human-readable justification for each recommendation  

The outputs are designed to support:
- Operations decision reviews  
- Capacity planning discussions  
- Cost vs. service tradeoff evaluation  
- Auditability and post-decision analysis  


## Tech Stack

- **Python** — core language  
- **Pandas** — option evaluation and aggregation  
- **NumPy** — numerical operations  
- **ReportLab** — executive PDF report generation  


## Inputs

### Scenario Input Data

**`data/sample_inputs.csv`**

Each row represents a capacity-gap scenario requiring intervention.

Key inputs include:
- Scenario and site identifiers  
- Capacity gap (units)  
- Option-specific recovery assumptions  
- Intervention cost parameters  
- Service cost and SLA penalty parameters  

> **DISCLAIMER:**  
> The included dataset is 100% synthetic and exists solely to demonstrate system logic and structure.  


## Decision Logic (High-Level)

For each scenario, the tool applies the following rules:

1. **If at least one option can meet SLA**  
   → Select the **lowest total-cost SLA-met option**.

2. **If no option can meet SLA**  
   → Allow a **controlled premium** above the cheapest option, then:
   - minimize **unmet units** (service-first),
   - tie-break by **total cost**.

This mirrors real-world operations practice: when SLA failure is unavoidable, reducing downstream service impact often outweighs marginal cost savings.

---

## Key Outputs

### 1. Executive PDF Report (Primary Artifact)

**`outputs/intervention_brief.pdf`**

The PDF is designed to be readable by non-technical stakeholders while preserving full decision transparency.

**Page 1 — Executive Overview**
- Executive summary
- Decision rules
- Final recommended intervention per scenario

**Page 2 — Scenario Drilldown**
- Full option comparison for a selected scenario
- Costs, unmet units, and SLA outcomes
- Recommended option clearly marked (★)

---

### 2. CSV Outputs (Analyst / Audit Trail)

- **`outputs/recommendations.csv`**  
  Final recommended intervention per scenario.

- **`outputs/intervention_option_results.csv`**  
  Full evaluation of every option across all scenarios, including:
  - recovered units
  - unmet units
  - SLA feasibility
  - intervention cost
  - service cost
  - total cost

These outputs provide a complete audit trail and support deeper analysis if required.

---

### 3. Console Output (Development Validation)

During development, the tool can optionally print intermediate option evaluations to the console to verify that the decision logic is being applied correctly.  

This output:
- does **not** affect recommendations,
- exists solely for internal validation,
- and is not intended as a user-facing feature.

---

## Project Structure

```text
ops_intervention_optimizer/
├── data/
│   └── sample_inputs.csv
├── outputs/
│   ├── intervention_brief.pdf
│   ├── recommendations.csv
│   └── intervention_option_results.csv
├── src/
│   ├── scenarios.py      # Input loading and scenario definitions
│   ├── constraints.py    # Feasibility rules
│   ├── costs.py          # Cost calculations
│   ├── model.py          # Option evaluation and decision logic
│   ├── explain.py        # Human-readable explanations
│   ├── report_pdf.py     # Executive PDF generation
│   └── main.py           # Orchestration entry point
├── requirements.txt
└── README.md
```
## How to Run
> Note: Commands should be run from the repository root.

### Install dependencies
```python -m pip install -r requirements.txt```

### Run the tool and generate outputs
```python src/main.py```


### Optional scenario drilldown selection for the PDF:

```python src/main.py --drilldown-id SCN_001```

## Design Choices

### Rule-Based Decision Logic

Rule-based logic was chosen for transparency, explainability, and auditability.
This approach aligns with operational and regulated environments where decisions must be traceable and defensible.

### Synthetic Data

Synthetic data is used to demonstrate logic and structure without exposing real operational data.
The focus is on decision flow and tradeoff handling, not the data source itself.

### Separation of Concerns

Input handling, cost modeling, decision logic, explanation generation, and reporting are fully decoupled.
This allows future extensions without modifying the core decision engine.

### Limitations

Thresholds and cost parameters are illustrative and would require calibration with real operational data.

The system is deterministic and rule-based, not predictive.

External factors (e.g., weather, labor availability, supplier disruption) are not explicitly modeled.

## Summary

This project demonstrates how structured decision logic can be applied to operational intervention planning, balancing cost efficiency with service outcomes under constrained conditions.

It reflects real-world practices used in operations, logistics, and capacity management teams.
