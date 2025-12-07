"""
experiment_analysis.py

Frequentist-style experiment analysis on the synthetic dataset in
data/synthetic_experiment_outcomes.csv.

- Cleans the cohort (eligible visitors, non-contaminated users)
- Aggregates metrics by variant
- Runs:
    * Two-proportion z-tests for activation, conversion, and new booking
    * Welch's t-test for average new-booking MRR per user
"""

import math
import pandas as pd
from scipy.stats import norm, t


# ------------------------------------------------------------
# 1. Statistical test helpers
# ------------------------------------------------------------

def two_proportion_ztest(n1, x1, n2, x2):
    """
    Two-proportion z-test on aggregated counts.

    n1, x1: sample size and successes for control
    n2, x2: sample size and successes for treatment
    Returns (z_stat, p_value) or (None, None) if invalid.
    """
    n1, x1, n2, x2 = map(float, (n1, x1, n2, x2))
    if n1 == 0 or n2 == 0:
        return None, None

    p1, p2 = x1 / n1, x2 / n2
    pooled = (x1 + x2) / (n1 + n2)
    if pooled in (0, 1):
        return None, None

    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    if se == 0:
        return None, None

    z = (p2 - p1) / se
    p = 2 * (1 - norm.cdf(abs(z)))
    return z, p


def two_sample_ttest(m1, s1, n1, m2, s2, n2):
    """
    Welch’s two-sample t-test from summary stats.

    m*: means, s*: standard deviations, n*: sample sizes
    Returns (t_stat, p_value) or (None, None) if invalid.
    """
    m1, s1, n1 = float(m1), float(s1), float(n1)
    m2, s2, n2 = float(m2), float(s2), float(n2)

    if n1 <= 1 or n2 <= 1:
        return None, None

    se = math.sqrt(s1**2 / n1 + s2**2 / n2)
    if se == 0:
        return None, None

    tstat = (m2 - m1) / se
    df_num = (s1**2 / n1 + s2**2 / n2) ** 2
    df_den = (s1**4 / (n1**2 * (n1 - 1))) + (s2**4 / (n2**2 * (n2 - 1)))
    if df_den == 0:
        return None, None

    dfree = df_num / df_den
    pval = 2 * (1 - t.cdf(abs(tstat), dfree))
    return tstat, pval


# ------------------------------------------------------------
# 2. Aggregation helpers
# ------------------------------------------------------------

def aggregate_for_experiment(df, experiment_name="homepage_cta_test"):
    """
    Filter to a clean cohort and aggregate metrics by variant.

    Returns a DataFrame with:
    - users, activations, conversions, new_bookings
    - total_new_mrr, total_revenue
    - avg_nb_mrr, sd_nb_mrr, n_nb_mrr (for t-test)
    """
    clean = df[
        (df["experiment_name"] == experiment_name)
        & (df["is_eligible_visitor"] == 1)
        & (df["contamination_flag"] == "Not Contaminated")
        & (df["duplication_rank"] == 1)
    ]

    agg = (
        clean.groupby("variant")
        .agg(
            users=("user_id", "nunique"),
            activations=("is_activated", "sum"),
            conversions=("is_converted", "sum"),
            new_bookings=("new_booking_flag", "sum"),
            total_new_mrr=("nb_mrr", "sum"),
            total_revenue=("total_revenue", "sum"),
            avg_nb_mrr=("nb_mrr", "mean"),
            sd_nb_mrr=("nb_mrr", "std"),
            n_nb_mrr=("nb_mrr", "size"),
        )
        .reset_index()
    )

    return agg


# ------------------------------------------------------------
# 3. Main analysis function
# ------------------------------------------------------------

def run_experiment_analysis_from_user_level(df, experiment_name="homepage_cta_test"):
    """
    Run a small suite of tests comparing each treatment variant to control.
    Returns a DataFrame where each row is a (variant, metric) pair.
    """
    agg = aggregate_for_experiment(df, experiment_name)

    if "control" not in set(agg["variant"]):
        raise ValueError("No 'control' variant found in the aggregated data.")

    control = agg[agg["variant"] == "control"].iloc[0]
    rows = []

    for _, tr in agg.iterrows():
        if tr["variant"] == "control":
            continue

        n1, n2 = control["users"], tr["users"]

        # Proportion metrics: activation, conversion, new booking
        for metric_name, count_col in [
            ("activation_rate", "activations"),
            ("conversion_rate", "conversions"),
            ("new_booking_rate", "new_bookings"),
        ]:
            x1, x2 = control[count_col], tr[count_col]
            z, p = two_proportion_ztest(n1, x1, n2, x2)
            if z is None:
                continue

            rows.append(
                {
                    "experiment_name": experiment_name,
                    "variant": tr["variant"],
                    "metric": metric_name,
                    "test": "two-proportion z-test",
                    "control_rate": (x1 / n1) if n1 else None,
                    "treatment_rate": (x2 / n2) if n2 else None,
                    "lift": (
                        ((x2 / n2) - (x1 / n1)) / (x1 / n1)
                        if (x1 and n1 and n2)
                        else None
                    ),
                    "statistic": z,
                    "p_value": p,
                }
            )

        # Continuous metric: average new-booking MRR per user
        tstat, pval = two_sample_ttest(
            control["avg_nb_mrr"],
            control["sd_nb_mrr"],
            control["n_nb_mrr"],
            tr["avg_nb_mrr"],
            tr["sd_nb_mrr"],
            tr["n_nb_mrr"],
        )

        if tstat is not None:
            rows.append(
                {
                    "experiment_name": experiment_name,
                    "variant": tr["variant"],
                    "metric": "average_nb_mrr_per_user",
                    "test": "Welch two-sample t-test",
                    "control_mean": control["avg_nb_mrr"],
                    "treatment_mean": tr["avg_nb_mrr"],
                    "diff": tr["avg_nb_mrr"] - control["avg_nb_mrr"],
                    "statistic": tstat,
                    "p_value": pval,
                }
            )

    return pd.DataFrame(rows)


def run_experiment_analysis(
    csv_path="../data/synthetic_experiment_outcomes.csv",
    experiment_name="homepage_cta_test",
):
    """
    Convenience wrapper: load the CSV from disk and run the analysis.
    """
    df = pd.read_csv(csv_path)
    return run_experiment_analysis_from_user_level(df, experiment_name)


# ------------------------------------------------------------
# 4. Script entry point
# ------------------------------------------------------------

if __name__ == "__main__":
    results_df = run_experiment_analysis()
    # Print to console; in a notebook you might display() instead
    print(results_df.to_string(index=False))
