econometrics — Statistical Testing
====================================

.. module:: sipQuant.econometrics

Statistical testing and regression tools. Run these tests before building
any price model to ensure appropriate model selection.

**Standard pre-modelling test sequence:**

1. ``adfTest`` + ``kpssTest`` → stationarity decision
2. ``ljungBox`` → serial correlation check
3. ``grangerCausality`` → proxy/factor selection
4. ``ols`` → factor regression and grade surfaces

Key Functions
-------------

``ols(y, X)``
    OLS regression with robust (HC3) standard errors.
    Returns ``{coefficients, intercept, rSquared, tStats, pValues, residuals}``.

``adfTest(series)``
    Augmented Dickey-Fuller unit root test. Returns ``{adfStat, pValue, isStationary}``.
    ``isStationary=True`` → use OU/ARMA; ``False`` → use GBM or difference the series.

``kpssTest(series)``
    KPSS stationarity test (null = stationary). Returns ``{kpssStat, pValue, isStationary}``.
    Use together with ADF: ADF rejects unit root AND KPSS fails to reject → strong stationarity evidence.

``grangerCausality(y, x, maxlag=4)``
    Tests whether ``x`` Granger-causes ``y``. Returns ``{fStat, pValue, granger_causes}`` per lag.
    Use for proxy selection: choose proxies that Granger-cause the target series.

``ljungBox(series, lags=10)``
    Ljung-Box autocorrelation test. Returns ``{qStats, pValues}`` at each lag.
    Significant autocorrelation → use ARMA or include lagged terms in regression.

``whiteTest(y, X)``
    White's heteroskedasticity test. Returns ``{testStat, pValue, isHomoskedastic}``.

``breuschPaganTest(y, X)``
    Breusch-Pagan heteroskedasticity test.

``durbinWatson(residuals)``
    Durbin-Watson autocorrelation statistic. Values near 2.0 indicate no autocorrelation.

.. code-block:: python

   import sipQuant as sq
   import numpy as np

   prices = np.array([182.0, 184.5, 187.0, 186.0, 185.5, 183.0, 187.5, 189.0])

   # Stationarity tests
   adf  = sq.econometrics.adfTest(prices)
   kpss = sq.econometrics.kpssTest(prices)
   print(f"ADF stationary:  {adf['isStationary']}  (p={adf['pValue']:.4f})")
   print(f"KPSS stationary: {kpss['isStationary']}  (p={kpss['pValue']:.4f})")

   # Autocorrelation check
   returns = np.diff(np.log(prices))
   lb = sq.econometrics.ljungBox(returns, lags=5)
   print(f"Ljung-Box p-values: {lb['pValues'].round(4)}")

   # Proxy selection via Granger causality
   # e.g. test if CME Corn Granger-causes local feed grain price
   corn_prices = np.array([420.0, 425.0, 422.0, 430.0, 428.0, 435.0, 432.0, 440.0])
   gc = sq.econometrics.grangerCausality(prices, corn_prices, maxlag=2)
   print(f"Corn Granger-causes hay? {gc[1]['granger_causes']}  (p={gc[1]['pValue']:.4f})")

   # Grade surface regression
   # Regress adjusted price on grade factors
   moisture = np.array([14.0, 15.0, 13.0, 16.0, 14.5, 15.5, 13.5, 14.0])
   X = np.column_stack([moisture])
   result = sq.econometrics.ols(prices, X)
   print(f"Moisture coefficient: {result['coefficients'][0]:.4f}")
   print(f"R-squared:            {result['rSquared']:.4f}")
