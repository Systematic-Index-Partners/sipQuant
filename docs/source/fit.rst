fit — Model Calibration
========================

.. module:: sipQuant.fit

Calibrates stochastic process parameters to observed price series.
The standard workflow: validate data → test stationarity → select process → calibrate → validate fit.

**Calibration workflow:**

.. code-block:: python

   import sipQuant as sq
   import numpy as np

   # 1. Test stationarity
   adf = sq.econometrics.adfTest(prices)
   kpss = sq.econometrics.kpssTest(prices)

   # 2. Select process based on stationarity and cluster type
   # Stationary → OU; Non-stationary → GBM; Jumps → LevyOU

   # 3. Calibrate
   params = sq.fit.fitOu(prices, dt=1/52)  # weekly hay prices

   # 4. Rank distribution fit by AIC
   dist_results = sq.fit.fitDistributions(np.diff(np.log(prices)))

Key Functions
-------------

``fitOu(prices, dt=1/52)``
    Fit Ornstein-Uhlenbeck process to a price series. Returns ``{theta, mu, sigma, logLikelihood}``.
    Primary calibration tool for Cluster A, F, H, K markets.

``fitLevyOU(prices, dt=1/52)``
    Fit Lévy OU process (OU + jump component). Returns OU parameters plus ``{jumpIntensity, jumpMean, jumpStd}``.

``fitGbm(prices, dt=1/252)``
    Fit GBM drift and volatility. Returns ``{mu, sigma, logLikelihood}``.

``fitGarch(returns)``
    Fit GARCH(1,1) to return series. Returns ``{omega, alpha, beta, unconditionalVol}``.

``fitHeston(prices, dt=1/252)``
    Fit Heston stochastic volatility model. Returns ``{kappa, theta, xi, rho, v0}``.

``fitArma(series, p, q)``
    Fit ARMA(p,q). Returns ``{arCoeffs, maCoeffs, sigma, aic, bic}``.

``fitCir(rates, dt=1/252)``
    Fit Cox-Ingersoll-Ross interest rate model.

``fitVasicek(rates, dt=1/252)``
    Fit Vasicek model.

``fitJumpDiffusion(prices, dt=1/252)``
    Fit Merton jump-diffusion model.

``fitCopula(data)``
    Fit Gaussian copula to multivariate data. Returns correlation matrix and marginal parameters.

``fitDistributions(data)``
    Fit all available distributions (normal, lognormal, t, gamma, exponential) to data and rank by AIC.
    Use this to identify the best marginal distribution before copula fitting.

``aic(logLikelihood, nParams)``
    Akaike Information Criterion: ``-2 * logL + 2 * k``.

``bic(logLikelihood, nParams, nObs)``
    Bayesian Information Criterion: ``-2 * logL + k * ln(n)``.

.. code-block:: python

   # Full calibration example — Alberta Hay (Cluster A)
   # Weekly prices, 2 years of data
   prices = np.array([182.0, 184.5, 187.0, 186.0, 185.5, 183.0, 187.5,
                      189.0, 191.0, 188.5, 186.0, 184.0])  # abbreviated

   # Calibrate OU
   ou_params = sq.fit.fitOu(prices, dt=1/52)
   print(f"OU: theta={ou_params['theta']:.4f}  mu={ou_params['mu']:.2f}  sigma={ou_params['sigma']:.4f}")

   # Simulate forward using calibrated parameters
   fwd_paths = sq.sim.ou(
       theta=ou_params['theta'],
       mu=ou_params['mu'],
       sigma=ou_params['sigma'],
       n=52, dt=1/52, x0=prices[-1], nSims=1000,
   )

   # Fit distributions to log-returns
   log_returns = np.diff(np.log(prices))
   dist_fits = sq.fit.fitDistributions(log_returns)
   for d in dist_fits[:3]:
       print(f"  {d['distribution']:15s} AIC={d['aic']:.2f}")
