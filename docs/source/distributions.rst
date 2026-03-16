distributions — Distribution Fitting
======================================

.. module:: sipQuant.distributions

Parametric distribution fitting, goodness-of-fit testing, and divergence
measures for commodity return distributions. Used to select the best
marginal distribution before copula fitting, and to characterise tail behaviour.

Key Functions
-------------

``fitNormal(data)`` / ``fitLognormal(data)`` / ``fitExponential(data)``
    Fit named parametric distributions by MLE. Return ``{params, logLikelihood, aic, bic}``.

``fitGamma(data)`` / ``fitBeta(data)`` / ``fitT(data)``
    Additional parametric families. Gamma is useful for convenience yields.
    Student-t captures fat tails common in commodity returns.

``fitMixture(data, nComponents=2)``
    Gaussian mixture model fitted by EM algorithm. Use for bimodal return
    distributions (e.g. Cluster R under two regulatory regimes).

``moments(data)``
    Returns ``{mean, variance, skewness, kurtosis, excessKurtosis}``.

``ksTest(data, distribution, params)``
    Kolmogorov-Smirnov goodness-of-fit test. Returns ``{ksStat, pValue, passed}``.

``adTest(data)``
    Anderson-Darling test for normality.

``klDivergence(p, q)``
    Kullback-Leibler divergence D(p||q). Use to compare empirical vs fitted distributions
    or to detect regime changes by comparing rolling KL against a baseline.

``jsDivergence(p, q)``
    Jensen-Shannon divergence (symmetric KL). Values near 0 = distributions are similar.

``quantile(data, q)`` / ``qqPlot(data, distribution)``
    Quantile computation and Q-Q plot data for visual diagnostics.

``fitDistributions(data)``
    Fits all available distributions and returns a list sorted by AIC.
    The primary tool for selecting the marginal distribution for a new cluster.

.. code-block:: python

   import sipQuant as sq
   import numpy as np

   log_returns = np.random.normal(0.001, 0.025, 260)

   # Rank all distributions by AIC
   fits = sq.distributions.fitDistributions(log_returns)
   print("Distribution fits by AIC:")
   for f in fits[:4]:
       print(f"  {f['distribution']:15s}  AIC={f['aic']:.2f}  BIC={f['bic']:.2f}")

   # Return distribution moments
   m = sq.distributions.moments(log_returns)
   print(f"Skewness: {m['skewness']:.4f}  Excess kurtosis: {m['excessKurtosis']:.4f}")

   # Fit Student-t for fat-tailed commodity returns
   t_fit = sq.distributions.fitT(log_returns)
   ks = sq.distributions.ksTest(log_returns, 't', t_fit['params'])
   print(f"KS test p-value: {ks['pValue']:.4f}  (>0.05 = good fit)")

   # KL divergence to detect regime change
   baseline = log_returns[:130]
   recent   = log_returns[130:]
   p = np.histogram(baseline, bins=30, density=True)[0] + 1e-10
   q = np.histogram(recent,   bins=30, density=True)[0] + 1e-10
   kl = sq.distributions.klDivergence(p / p.sum(), q / q.sum())
   print(f"KL divergence (regime change indicator): {kl:.4f}")
