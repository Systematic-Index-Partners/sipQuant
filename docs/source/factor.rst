factor — Factor Models
=======================

.. module:: sipQuant.factor

Factor models for proxy construction, hedge ratio estimation, and return
attribution. Primary use in clusters where liquid benchmark instruments
exist to hedge or proxy illiquid physical prices.

**Proxy construction workflow (Clusters G, H, O, D):**

.. code-block:: python

   # Step 1: Test if benchmark Granger-causes target
   gc = sq.econometrics.grangerCausality(target_prices, benchmark_prices, maxlag=4)

   # Step 2: Estimate rolling beta (hedge ratio changes over time)
   beta_series = sq.factor.rollingBeta(target_prices, benchmark_prices, window=13)

   # Step 3: Use CAPM-style factor model for proxy value
   capm_result = sq.factor.capm(target_returns, benchmark_returns)

Key Functions
-------------

``capm(returns, marketReturns, riskFreeRate=0.0)``
    CAPM: ``r = rf + beta * (rm - rf) + alpha``. Returns ``{alpha, beta, rSquared}``.

``estimateBeta(returns, marketReturns)``
    OLS beta estimate with standard error.

``rollingBeta(returns, marketReturns, window=52)``
    Rolling beta over a sliding window. Returns array of betas.
    Use to track how the hedge ratio of a thin market vs its proxy changes over time.

``estimateFactorLoading(returns, factorReturns)``
    Multiple factor loadings via OLS. Returns ``{loadings, alphas, rSquared}``.

``famaFrench3(returns, mktReturns, smbReturns, hmlReturns)``
    Fama-French 3-factor model.

``carhart4(returns, mktReturns, smbReturns, hmlReturns, momReturns)``
    Carhart 4-factor model with momentum.

``apt(returns, factorReturns)``
    Arbitrage Pricing Theory multi-factor model.

``pcaFactors(returns, nFactors=3)``
    Extract statistical risk factors from returns via PCA. Useful when no
    fundamental factors are available (emerging clusters).

``factorMimicking(returns, characteristics)``
    Construct factor-mimicking portfolios (SMB/HML style) from asset characteristics.

``jensenAlpha(returns, marketReturns, riskFreeRate=0.0)``
    Jensen's alpha — risk-adjusted excess return.

``treynorMazuy(returns, marketReturns, riskFreeRate=0.0)``
    Treynor-Mazuy market timing model.

``multifactor(returns, factors)``
    General multi-factor regression. Returns coefficients for each factor.

.. code-block:: python

   import sipQuant as sq
   import numpy as np

   # Cluster H example: Canola meal price proxied by CME Soybean Meal
   canola_meal_returns  = np.random.normal(0.001, 0.025, 104)
   soybean_meal_returns = np.random.normal(0.001, 0.022, 104)

   # Static beta for hedge ratio
   capm_result = sq.factor.capm(canola_meal_returns, soybean_meal_returns)
   print(f"Beta vs SBM: {capm_result['beta']:.4f}  R²: {capm_result['rSquared']:.4f}")

   # Rolling beta to detect drift in hedge ratio
   rolling_betas = sq.factor.rollingBeta(canola_meal_returns, soybean_meal_returns, window=13)
   print(f"Beta range: [{rolling_betas.min():.3f}, {rolling_betas.max():.3f}]")

   # Multi-factor for Cluster D (industrial biomaterials)
   # Factors: energy price, carbon credit price, policy indicator
   energy_ret  = np.random.normal(0.0, 0.03, 104)
   carbon_ret  = np.random.normal(0.001, 0.04, 104)
   factors = np.column_stack([energy_ret, carbon_ret])
   mf_result = sq.factor.multifactor(canola_meal_returns, factors)
   print(f"Energy loading: {mf_result['loadings'][0]:.4f}")
   print(f"Carbon loading: {mf_result['loadings'][1]:.4f}")
