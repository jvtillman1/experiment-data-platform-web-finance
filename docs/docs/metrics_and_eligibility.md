# Metrics & Eligibility Rules

This document defines how users are counted at each stage of the experiment funnel in the synthetic dataset.  
The goal is to make experiment readouts consistent across web, product, and finance views.

---

## Core Funnel Stages

### Visitor

A **visitor** is a user who:

- Has a first exposure to the experiment between the configured experiment start and end dates.
- Does not have disqualifying prior activity (for example, a conversion long before the experiment that would make them ineligible for the test).

Visitors form the base of the experiment funnel.

---

### Activation

An **activation** is a visitor who meets a product-specific engagement condition.

Examples of activation logic:

- Web-only users: activation occurs on or after the first exposure date.
- Hybrid / in-app users: activation can occur within a window prior to exposure (for example, up to 90 days) but must still be logically consistent with the experiment.

If a user converts *before* they are exposed to the experiment, they are **not** counted as an activation for that test, even if they technically meet the product threshold.

---

### Conversion

A **conversion** is an activation that completes a key business action, such as starting a paid plan.

Rules:

- The user must be an eligible activation.
- Conversion must occur:
  - On or after the activation date
  - On or after the first exposure date
  - Before the experiment end date

This prevents double-counting and ensures causal ordering (exposure → activation → conversion).

---

### New Booking / New MRR

A **new booking** is a conversion that results in new recurring revenue.

- Booking date must be on or after the conversion date.
- Only first-time bookings within the experiment context are counted as “new.”
- The `nb_mrr` field represents new-booking MRR attributed to that user for this experiment.

---

## Additional Events (Optional)

Depending on the experiment, we can also track internal funnel steps such as:

- **Onboarding start / onboarding complete**
- **Checkout start / checkout complete**

Each of these:

- Requires a valid activation.
- Must follow a sensible sequence (start → complete).
- Must occur before the experiment end date.

If timestamps for intermediate steps are missing but completion is clearly within the window, we treat the completion event as valid and leave the missing intermediate step as null.

---

## Contamination & Duplication

Real user data can be messy:

- The same person may show up under multiple IDs.
- A user might accidentally be exposed to both control and treatment.

To handle this, the experiment tables include:

- `duplication_rank`
  - Ranks multiple rows per user and experiment.
  - `1` is the primary row used for analysis.

- `contamination_flag`
  - `'Not Contaminated'` – user appears in a single variant.
  - Other values indicate some form of cross-bucket exposure.

**Recommended “clean” cohort for analysis:**

- `duplication_rank = 1`
- `contamination_flag = 'Not Contaminated'`

---

## Metric Naming Conventions (Synthetic Dataset)

Example column names used in this repo:

- `is_eligible_visitor`
- `is_activated`
- `is_converted`
- `new_booking_flag`
- `nb_mrr`
- `total_revenue`
- `contamination_flag`
- `duplication_rank`

These conventions make it easier for the SQL and Python code to:

- Filter to the right users
- Compute conversion rates and lifts
- Aggregate financial impact by variant and segment
