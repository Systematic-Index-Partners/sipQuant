bootstrap — Curve & Surface Construction
==========================================

.. module:: sipQuant.bootstrap

Interpolation and bootstrapping tools for constructing smooth curves and
surfaces from sparse market observations. Essential for building forward
curves from thin commodity markets with few observable data points.

Key Functions
-------------

``curve(x, y, method='linear')``
    1D curve interpolation. ``method``: ``'linear'``, ``'cubic'``, ``'pchip'``.
    Use ``'pchip'`` (piecewise cubic Hermite) to avoid overshooting in commodity forward curves.

``surface(x, y, z, method='linear')``
    2D surface interpolation for vol surfaces and grade surfaces.

``zeroRateCurve(bondPrices, maturities, faceValues=None, coupons=None)``
    Bootstrap zero rate curve from bond prices.

``forwardCurve(zeroCurve, tenors)``
    Derive instantaneous forward rates from a zero curve.

``discountCurve(zeroCurve, tenors)``
    Discount factor curve from zero rates.

``yieldCurve(zeroCurve, tenors)``
    Par yield curve construction.

``volSurface(strikes, tenors, impliedVols)``
    Implied volatility surface interpolation from OTC option quotes.
    Input: sparse (strike, tenor, vol) observations; output: dense surface.

``creditCurve(cdsSpreads, tenors, r, recovery=0.4)``
    CDS curve bootstrapping for counterparty credit risk.

``fxForwardCurve(spotFx, domesticRates, foreignRates, tenors)``
    FX forward curve from covered interest parity.

``inflationCurve(nominalRates, realRates, tenors)``
    Inflation breakeven curve from nominal and real rates.

.. code-block:: python

   import sipQuant as sq
   import numpy as np

   # Build a commodity forward curve from sparse futures observations
   observed_tenors = np.array([0.25, 0.50, 1.00])
   observed_prices = np.array([188.0, 190.5, 193.5])

   # Interpolate to monthly tenors using PCHIP (no overshoot)
   all_tenors = np.arange(0.083, 1.001, 0.083)  # monthly
   dense_curve = sq.bootstrap.curve(
       x=observed_tenors,
       y=observed_prices,
       method='pchip',
   )

   # Build implied vol surface from OTC collar quotes
   strikes = np.array([170.0, 180.0, 190.0, 200.0, 210.0])
   tenors  = np.array([0.25, 0.50, 1.00])
   vols    = np.array([
       [0.22, 0.20, 0.19, 0.20, 0.22],  # 3-month
       [0.21, 0.19, 0.18, 0.19, 0.21],  # 6-month
       [0.20, 0.18, 0.17, 0.18, 0.20],  # 12-month
   ])
   vol_surf = sq.bootstrap.volSurface(strikes, tenors, vols)
