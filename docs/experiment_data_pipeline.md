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

### 2. Outcomes Table – `{experiment_name}_outcomes`

From the base table we derive a curated **outcomes table** for each experiment, for example:

```text
homepage_cta_test_outcomes
