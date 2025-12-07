"""
bayesian_experiment_analysis.py

Bayesian experiment analysis on the synthetic dataset in
data/synthetic_experiment_outcomes.csv.

For each metric:
    - activation_rate
    - conversion_rate
    - new_booking_rate

we assume a Beta-Binomial model with a uniform prior Beta(1, 1) on the
rate for each variant.

We then:
    - compute the posterior for control and treatment
    - draw samples from both posteriors
    - estimate:
        * posterior mean rate per variant
        * posterior mean difference (treatment - control)
        * 95% credible interval for the difference
        * P(treatment > control)
"""

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# 1. Aggregation (same clean cohort logic as in experiment_analysis.py)
# ------------------------------------------------------------

def aggregate_for_experiment(df, experiment_name="homepage_cta_test"):
    """
    Filter to a clean cohort and aggregate counts by variant.

    Returns a DataFrame with:
    - users
    - activations
    - conversions
    - new_bookings
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
        )
        .reset_index()
    )

    return agg


# ------------------------------------------------------------
# 2. Beta-Binomial helpers
# ------------------------------------------------------------

def beta_posterior_params(a_prior, b_prior, successes, trials):
    """
    Conjugate update of Beta prior with Binomial likelihood.

    a_post = a_prior + successes
    b_post = b_prior + trials - successes
    """
    return a_prior + successes, b_prior + trials - successes


def simulate_posterior_difference(a_c, b_c, a_t, b_t, n_draws=50000, random_state=42):
    """
    Draw samples from Beta(a_c, b_c) and Beta(a_t, b_t) and compute
    the distribution of differences and relative lift.

    Returns a dict of summary statistics.
    """
    rng = np.random.default_rng(random_state)

    control_samples = rng.beta(a_c, b_c, size=n_draws)
    treatment_samples = rng.beta(a_t, b_t, size=n_draws)

    diff = treatment_samples - control_samples

    # Relative lift; guard against division by zero
    with np.errstate(divide="ignore", invalid="ignore"):
        rel_lift = np.where(
            control_samples > 0,
            diff / control_samples,
            np.nan,
        )

    prob_t_greater = float((treatment_samples > control_samples).mean())
    diff_mean = float(diff.mean())
    diff_ci_low, diff_ci_high = np.percentile(diff, [2.5, 97.5])

    rel_lift_mean = float(np.nanmean(rel_lift))
    rel_lift_ci_low, rel_lift_ci_high = np.nanpercentile(rel_lift, [2.5, 97.5])

    return {
        "posterior_mean_control": float(control_samples.mean()),
        "posterior_mean_treatment": float(treatment_samples.mean()),
        "posterior_mean_diff": diff_mean,
        "diff_ci_low": float(diff_ci_low),
        "diff_ci_high": float(diff_ci_high),
        "posterior_mean_rel_lift": rel_lift_mean,
        "rel_lift_ci_low": float(rel_lift_ci_low),
        "rel_lift_ci_high": float(rel_lift_ci_high),
        "prob_treatment_greater": prob_t_greater,
    }


# ------------------------------------------------------------
# 3. Main Bayesian analysis
# ------------------------------------------------------------

def run_bayesian_experiment_analysis_from_user_level(
    df,
    experiment_name="homepage_cta_test",
    a_prior=1.0,
    b_prior=1.0,
    n_draws=50000,
):
    """
    Run Bayesian Beta-Binomial analysis comparing each treatment
    variant to control for:
        - activation_rate
        - conversion_rate
        - new_booking_rate

    Returns a DataFrame where each row is (variant, metric) with
    posterior summaries and P(treatment > control).
    """
    agg = aggregate_for_experiment(df, experiment_name)

    if "control" not in set(agg["variant"]):
        raise ValueError("No 'control' variant found in the aggregated data.")

    control = agg[agg["variant"] == "control"].iloc[0]
    rows = []

    for _, tr in agg.iterrows():
        if tr["variant"] == "control":
            continue

        n1, n2 = float(control["users"]), float(tr["users"])

        for metric_name, count_col in [
            ("activation_rate", "activations"),
            ("conversion_rate", "conversions"),
            ("new_booking_rate", "new_bookings"),
        ]:
            x1, x2 = float(control[count_col]), float(tr[count_col])

            # Posterior parameters for control and treatment
            a_c, b_c = beta_posterior_params(a_prior, b_prior, x1, n1)
            a_t, b_t = beta_posterior_params(a_prior, b_prior, x2, n2)

            summary = simulate_posterior_difference(
                a_c, b_c, a_t, b_t, n_draws=n_draws
            )

            rows.append(
                {
                    "experiment_name": experiment_name,
                    "variant": tr["variant"],
                    "metric": metric_name,
                    "prior_a": a_prior,
                    "prior_b": b_prior,
                    **summary,
                }
            )

    return pd.DataFrame(rows)


def run_bayesian_experiment_analysis(
    csv_path="../data/synthetic_experiment_outcomes.csv",
    experiment_name="homepage_cta_test",
    a_prior=1.0,
    b_prior=1.0,
    n_draws=50000,
):
    """
    Convenience wrapper: load the CSV from disk and run the Bayesian analysis.
    """
    df = pd.read_csv(csv_path)
    return run_bayesian_experiment_analysis_from_user_level(
        df,
        experiment_name=experiment_name,
        a_prior=a_prior,
        b_prior=b_prior,
        n_draws=n_draws,
    )


# ------------------------------------------------------------
# 4. Script entry point
# ------------------------------------------------------------

if __name__ == "__main__":
    results_df = run_bayesian_experiment_analysis()
    print(results_df.to_string(index=False))
