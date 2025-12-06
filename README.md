# experiment-data-platform-web-finance
Unified experimentation data platform with synthetic web + finance data, SQL pipeline, and frequentist/Bayesian analysis code.
# Experimentation Data Platform – Web + Finance

This repository mirrors a real project where I designed a **unified experimentation data pipeline** that connects web behavior with finance outcomes for a B2B SaaS product.

The goal: create a **single source of truth** for A/B tests and quasi-experiments so product, marketing, and finance teams can all answer the same questions with the same numbers:

- Did the experiment increase activations and conversions?
- What was the impact on new bookings and recurring revenue?
- How do results differ by region, package, or other key segments?

To do this, I:

- Defined shared **eligibility rules** for visitors, activations, conversions, and new bookings.
- Built **base, aggregated, and deep-dive experiment tables** that join web analytics with finance data. :contentReference[oaicite:1]{index=1}  
- Implemented **frequentist and Bayesian analysis code** to evaluate experiments from these tables.

> ⚠️ All data and numbers in this repository are **synthetic** and for demonstration only.  
> They do **not** represent real company data.

---

## Project Structure

- `docs/` – Written documentation of the data pipeline, table schemas, and metric definitions.
- `data/` – Synthetic CSV representing an experiment outcome table.
- `sql/` – Example SQL that builds base and aggregated experiment tables from raw/synthetic inputs.
- `python/` – Re-usable analysis code:
  - `frequentist_analysis.py` – z-tests for rates, t-tests for means, and a `run_experiment_analysis()` function.
  - `bayesian_analysis.py` – Bayesian proportion/continuous inference and `run_experiment_analysis_bayes()`.
- `notebooks/` – Jupyter notebook template showing interactive analysis on the synthetic data.
- `img/` – Pipeline diagram and dashboard mock for visual context.

---

## Skills Demonstrated

- Experimentation design & measurement
- Causal inference mindset (eligibility, contamination, quasi-experiments)
- Data modeling and pipeline design
- SQL for complex joins and aggregations
- Python for statistical analysis (frequentist & Bayesian)
- Communicating results to product, marketing, and finance stakeholders

---

## How to Use This Repo

1. Clone the repository and install Python dependencies (pandas, numpy, scipy, matplotlib, etc.).
2. Inspect `data/synthetic_experiment_outcomes.csv` to see the experiment outcome schema.
3. Review `sql/build_experiment_tables.sql` to understand how base and aggregated tables are built.
4. Run `python/frequentist_analysis.py` or `python/bayesian_analysis.py` on the synthetic dataset.
5. Open `notebooks/experiment_analysis_template.ipynb` for an end-to-end walkthrough.

---

## Notes

This project is based on an internal **web–finance experiment data pipeline** I built, generalized and anonymized for portfolio use. All names, tables, and numbers here are illustrative.
