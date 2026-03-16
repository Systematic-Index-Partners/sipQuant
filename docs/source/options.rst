options — Option Pricing
=========================

.. module:: sipQuant.options

Analytical and Monte Carlo option pricing with full Greeks.

**Option selection by cluster:**

+----------------------+--------------------------------------------------+
| Function             | Cluster use case                                 |
+======================+==================================================+
| ``blackScholes``     | All liquid clusters with vol surface available   |
+----------------------+--------------------------------------------------+
| ``barrier``          | F (quota risk), R (regulatory), X (capacity)    |
+----------------------+--------------------------------------------------+
| ``binary``           | Y (parametric insurance triggers)               |
+----------------------+--------------------------------------------------+
| ``spread``           | A, E (basis options between markets)            |
+----------------------+--------------------------------------------------+
| ``asian``            | C, N, Z (average-price settlement)              |
+----------------------+--------------------------------------------------+
| ``impliedVol``       | All — back out vol from observed option prices  |
+----------------------+--------------------------------------------------+

Key Functions
-------------

``blackScholes(S, K, T, r, sigma, optType='call', q=0.0)``
    European Black-Scholes with cost of carry. Returns ``{price, delta, gamma, vega, theta, rho}``.

``binomial(S, K, T, r, sigma, n=100, optType='call', style='european', q=0.0)``
    Binomial tree for European or American options.

``trinomial(S, K, T, r, sigma, n=100, optType='call', style='european', q=0.0)``
    Trinomial tree — more stable than binomial for barrier options.

``asian(S, K, T, r, sigma, nSims=10000, optType='call', avgType='geometric', q=0.0)``
    Asian option. ``avgType='geometric'`` has closed form; ``'arithmetic'`` uses Monte Carlo.

``binary(S, K, T, r, sigma, optType='call', q=0.0)``
    Cash-or-nothing binary option. Core pricing tool for parametric insurance triggers (Cluster Y).

``spread(S1, S2, K, T, r, sigma1, sigma2, rho)``
    Two-asset spread option using Kirk's approximation. For basis spread options between local and benchmark.

``barrier(S, K, H, T, r, sigma, barrierType, rebate=0.0, optType='call', q=0.0)``
    Barrier option. ``barrierType``: ``'up-and-out'``, ``'up-and-in'``, ``'down-and-out'``, ``'down-and-in'``.
    Use for Cluster F (quota barrier: price explodes if quota is cut) or Cluster X (capacity ceiling options).

``simulate(S, K, T, r, sigma, nSims=10000, optType='call', q=0.0, seed=None)``
    Plain Monte Carlo option pricing.

``impliedVol(price, S, K, T, r, optType='call', q=0.0)``
    Implied volatility by bisection. Required for vol surface construction.

``buildForwardCurve(spotPrice, rates, tenors, dividendYields=None)``
    Forward curve from spot price, rates, and dividend/convenience yields.

``bootstrapCurve(futuresPrices, tenors, spotPrice, r)``
    Bootstrap convenience yields from a strip of futures prices.

.. code-block:: python

   import sipQuant as sq
   import numpy as np

   # Black-Scholes cap on hay delivery price
   bs = sq.options.blackScholes(
       S=187.50, K=200.0, T=0.50,
       r=0.046, sigma=0.18,
       optType='call', q=0.028,
   )
   print(f"Cap price: ${bs['price']:.2f}  Delta: {bs['delta']:.4f}")

   # Binary option for drought-triggered delivery (Cluster Y)
   binary_opt = sq.options.binary(
       S=187.50, K=220.0, T=0.25,
       r=0.046, sigma=0.18,
       optType='call',
   )
   print(f"Binary price (trigger probability): {binary_opt['price']:.4f}")

   # Down-and-out barrier for quota protection (Cluster F)
   barrier_opt = sq.options.barrier(
       S=95.0, K=90.0, H=70.0,
       T=0.50, r=0.046, sigma=0.30,
       barrierType='down-and-out',
       optType='call',
   )
   print(f"Barrier option price: ${barrier_opt['price']:.4f}")

   # Spread option for basis arb (Cluster A)
   spread_opt = sq.options.spread(
       S1=187.50,  # Alberta hay
       S2=182.00,  # Saskatchewan hay
       K=0.0,      # zero-strike spread option
       T=0.25, r=0.046,
       sigma1=0.18, sigma2=0.20,
       rho=0.75,   # high correlation between regions
   )
   print(f"Spread option price: ${spread_opt['price']:.4f}")
