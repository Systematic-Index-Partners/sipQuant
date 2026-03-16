sim — Price Process Simulation
================================

.. module:: sipQuant.sim

Stochastic process simulation for commodity price modelling and Monte Carlo.
Process selection is driven by the cluster type of the commodity being modelled.

**Process selection by cluster:**

+----------------------------------+-----------------------------+
| Process                          | Cluster applicability       |
+==================================+=============================+
| ``ou``                           | A, F, H, K, L — mean-revert|
+----------------------------------+-----------------------------+
| ``levyOu``                       | A, F, P — OU + jumps        |
+----------------------------------+-----------------------------+
| ``compoundPoisson``              | B, T, Y — event demand      |
+----------------------------------+-----------------------------+
| ``markovSwitching``              | B, I, R — regime changes    |
+----------------------------------+-----------------------------+
| ``gbm``                          | D, O — energy-linked        |
+----------------------------------+-----------------------------+
| ``garch`` / ``arch``             | All — conditional vol       |
+----------------------------------+-----------------------------+
| ``heston``                       | A, C — stochastic vol       |
+----------------------------------+-----------------------------+
| ``arma``                         | G, Q — AR structure         |
+----------------------------------+-----------------------------+

Key Functions
-------------

``ou(theta, mu, sigma, n, dt=1/252, x0=None, nSims=1)``
    Ornstein-Uhlenbeck mean-reverting process. Primary model for Cluster A.

``gbm(mu, sigma, nSteps, nSims, s0=100, dt=1/252)``
    Geometric Brownian Motion. Standard for energy-linked clusters.

``levyOu(theta, mu, sigma, jumpIntensity, jumpMean, jumpStd, n, dt=1/252)``
    Lévy OU — OU process with superimposed compound Poisson jumps.

``compoundPoisson(lam, jumpMean, jumpStd, n, dt=1/252, seed=None)``
    Compound Poisson process for event-triggered demand (Cluster B: road salt; Cluster T: floral events).

``markovSwitching(states, transitionMatrix, stateMeans, stateSigmas, n, seed=None)``
    Hidden Markov regime-switching process. Use for markets with regulatory regimes (Cluster R) or weather state transitions (Cluster B).

``garch(omega, alpha, beta, n, mu=0.0, seed=None)``
    GARCH(1,1) conditional volatility. Calibrate with ``fit.fitGarch()``.

``heston(S0, v0, kappa, theta, xi, rho, r, T, nSteps, nSims, seed=None)``
    Heston stochastic volatility model. For markets with vol-of-vol dynamics.

``arma(ar, ma, n, sigma=1.0, mu=0.0, seed=None)``
    ARMA(p,q) process for serially correlated price drivers.

``poisson(lam, n, seed=None)``
    Homogeneous Poisson process for event counting.

``simulate(model, params, n, nSims=1, seed=None)``
    General dispatcher: pass model name as string and params dict.

.. code-block:: python

   import sipQuant as sq
   import numpy as np

   # Cluster A — OU process for Alberta Hay (calibrated from fit.fitOu)
   paths = sq.sim.ou(
       theta=0.85,   # mean reversion speed (weekly)
       mu=187.50,    # long-run mean price
       sigma=8.20,   # volatility $/tonne per week
       n=52,         # 1 year of weekly steps
       dt=1/52,
       x0=185.0,
       nSims=1000,
   )
   # paths shape: (1000, 52)

   # Cluster B — Compound Poisson for weather-event demand
   jumps = sq.sim.compoundPoisson(
       lam=2.5,      # 2.5 demand events per year
       jumpMean=35.0, # avg price spike $/tonne
       jumpStd=12.0,
       n=52,
       dt=1/52,
       seed=42,
   )

   # Cluster R — Markov switching for regulatory regime
   transition = np.array([[0.95, 0.05],   # stable → disrupted: 5%/period
                           [0.20, 0.80]])  # disrupted → stable: 20%/period
   regime_paths = sq.sim.markovSwitching(
       states=2,
       transitionMatrix=transition,
       stateMeans=np.array([185.0, 320.0]),   # stable vs disrupted price
       stateSigmas=np.array([8.0, 45.0]),
       n=52,
       seed=42,
   )
