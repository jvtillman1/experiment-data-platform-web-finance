This is the full text.  I don't like how the output looks

# Experiment Data Pipeline Overview

This document describes the high-level data flow and table design for an experimentation platform that connects web behavior with finance outcomes using synthetic data.

---

## Goals

- Provide **gold-source tables** for experiment user outcomes that can be used for:
  - Statistical testing (frequentist & Bayesian)
  - Financial impact analysis
  - Deep-dive behavior and retention analysis
- Document data assumptions, flows, and metric definitions so that web, product, and finance teams all use the same logic.
- Make it easy to spin up consistent dashboards for any new experiment.

---

## Raw Data Sources (Conceptual)

For the real project this mirrors, experiment data came from several systems.  
Here we represent them in generic form:

- **Web events**
  - Page views, visits, and experiment exposures
  - Device type, region, traffic source

- **Experiment assignment**
  - User / pseudo-user ID
  - Experiment name and variant
  - First exposure date

- **Users / accounts**
  - Prospect vs existing customer
  - Region, plan/package info, tenure

- **Finance / bookings**
  - Activation and conversion events
  - New bookings and monthly recurring revenue (MRR)
  - Retention / churn flags

All data in this repository is synthetic and for demonstration only.

---

## Pipeline Stages

### 1. Base Web–Finance Join

First, raw web, experiment, user, and finance tables are joined into a **base experiment table**.

Each row represents a unique user (or pseudo-user) with:

- Experiment name and variant
- First exposure date
- Region, device type, traffic source
- Key dates: activation, conversion, new booking
- Revenue fields (e.g., new booking MRR)
- Flags for contamination / duplication

### 2. Outcomes Table – `homepage_cta_test_outcomes`

From the base table we derive a curated **outcomes table** for each experiment, for example:

```text
homepage_cta_test_outcomes
```

This table:

- Filters to **eligible visitors** (based on consistent rules)
- Ensures event order is logical (exposure → activation → conversion → booking)
- Includes one row per valid user per experiment with:
  - Status flags (visitor, activated, converted, new booking)
  - Financial metrics (MRR, total revenue)
  - Fraud/closure flags and contamination flags

### 3. Aggregated Table – `{experiment_name}_aggregated`

The outcomes table is then aggregated by key dimensions, e.g.:

- Experiment name
- Variant
- Region / country
- Package or price group
- List size group or segment

Example fields:

- `users`
- `activations`
- `conversions`
- `new_bookings`
- `total_new_mrr`

These tables feed summary dashboards and statistical analysis scripts.

### 4. Deep-Dive Table – `{experiment_name}_details`

For experiments that need richer analysis, a **details** table is created with:

- Tenure and cohort information
- Retention outcomes (M1/M2 retention flags)
- Promo type
- Product usage / engagement metrics (e.g., emails sent, logins, feature adoption)

This table powers segmentation analysis and root-cause investigations when topline metrics move.

---

## Dashboards

Two main dashboard types sit on top of these tables:

### Experiment Summary Dashboard

- High-level KPIs by variant
- Activation, conversion, new booking, and revenue metrics
- Filters for region, device, package, and other key splits

### Deep-Dive / Diagnostics Dashboard

- Retention curves and cohort views
- Segment-level performance by tenure, promo, or usage
- Tools for slicing into outliers and understanding *why* metrics changed

---

## Relationship to the Code in This Repo

- `sql/build_experiment_tables.sql` will show how base and aggregated tables are built from raw-style inputs.
- `data/synthetic_experiment_outcomes.csv` is an example of an outcomes table.
- `python/` scripts and the notebook use these tables to perform frequentist and Bayesian experiment analysis.

This pipeline design is generalized and anonymized from a production system I built in industry.
