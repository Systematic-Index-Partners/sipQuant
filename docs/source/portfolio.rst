portfolio — Portfolio Optimisation
====================================

.. module:: sipQuant.portfolio

Portfolio construction and optimisation. In the SIP context, used for:

- **Index constituent weighting** — risk parity or volume-weighted allocation across commodity grades
- **Cross-cluster capital allocation** — HRP for allocating trading capital across multiple SIP index products
- **OTC book hedge optimisation** — mean-variance for computing optimal hedge ratios

Key Functions
-------------

``riskParity(covMatrix)``
    Risk parity weights: equalise risk contribution across assets.
    Robust to estimation error — preferred for sparse commodity return histories.

``hierarchicalRiskParity(returns)``
    HRP (López de Prado 2016). Uses hierarchical clustering + inverse-variance
    weighting. Best for allocating across non-correlated SIP cluster products.

``meanVariance(mu, covMatrix, targetReturn)``
    Mean-variance optimisation for a given target return (Markowitz frontier).

``minVariance(covMatrix)``
    Minimum variance portfolio — no return estimate required.

``equalWeight(n)``
    Equal weight across n assets.

``maxDiversification(covMatrix)``
    Maximum diversification ratio portfolio.

``tangency(mu, covMatrix, riskFreeRate=0.0)`` / ``maxSharpe(mu, covMatrix, riskFreeRate=0.0)``
    Maximum Sharpe ratio (tangency) portfolio.

``efficientFrontier(mu, covMatrix, nPoints=50)``
    Efficient frontier computation — returns array of (return, vol, weights) tuples.

``blackLitterman(mu, covMatrix, views, viewConfidence, tau=0.05)``
    Black-Litterman model incorporating analyst views on relative commodity returns.

``minCvar(returns, alpha=0.05)``
    Minimum CVaR portfolio.

.. code-block:: python

   import sipQuant as sq
   import numpy as np

   # 5 SIP index products: AHI, SKS, MBO, BCF, and a new cluster
   returns_matrix = np.random.normal(0.001, 0.02, (252, 5))  # 1 year daily
   cov = np.cov(returns_matrix.T)

   # Risk parity — preferred for commodity indices with sparse history
   rp_weights = sq.portfolio.riskParity(cov)
   print(f"Risk parity weights: {rp_weights.round(3)}")

   # HRP — for allocating capital across uncorrelated clusters
   hrp_weights = sq.portfolio.hierarchicalRiskParity(returns_matrix)
   print(f"HRP weights: {hrp_weights.round(3)}")

   # Equal weight as baseline
   ew_weights = sq.portfolio.equalWeight(5)
   print(f"Equal weights: {ew_weights}")
