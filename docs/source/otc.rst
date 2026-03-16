otc — OTC Instrument Pricing
=============================

.. module:: sipQuant.otc

The ``otc`` module prices the OTC structured products that SIP Global
structures around its commodity indices. All functions are pure analytics —
they compute NPV and Greeks given a forward curve. Position management
is handled by ``schema.OTCPosition`` and ``book``.

**Instrument selection by cluster:**

+-------------------------+-----------------------------------------------+
| Instrument              | Primary Clusters                              |
+=========================+===============================================+
| ``commoditySwap``       | A, B, D, H, O — fixed-float index exposure   |
+-------------------------+-----------------------------------------------+
| ``asianSwap``           | A, C, L — averaging reduces manipulation risk |
+-------------------------+-----------------------------------------------+
| ``collar``              | A, C, L, T — buyer price protection          |
+-------------------------+-----------------------------------------------+
| ``physicalForward``     | E, G, S, U — direct physical delivery        |
+-------------------------+-----------------------------------------------+
| ``swaption``            | A, D, H — optionality on a future swap       |
+-------------------------+-----------------------------------------------+
| ``asianOption``         | C, N, Z — exotic payoff on average price     |
+-------------------------+-----------------------------------------------+

.. code-block:: python

   import sipQuant as sq
   import numpy as np

commoditySwap()
---------------

Fixed-float commodity swap. The fixed payer pays ``fixedPrice * notional``
per period; the floating receiver pays the index value. NPV is computed as
the sum of discounted cashflow differences across all payment periods.

.. math::

   \text{NPV} = \sum_{i} (F_i - K) \cdot N \cdot e^{-r t_i}

where :math:`F_i` is the forward index price at payment date :math:`t_i`,
:math:`K` is the fixed price, and :math:`N` is notional.

.. code-block:: python

   # Forward curve prices from commodity.localForwardCurve
   index_curve = np.array([187.50, 189.00, 190.50, 192.00])
   schedule    = np.array([0.25, 0.50, 0.75, 1.00])

   swap = sq.otc.commoditySwap(
       fixedPrice=190.0,
       indexCurve=index_curve,
       notional=1000.0,    # tonnes
       schedule=schedule,
       r=0.046,
   )

   print(f"NPV:          ${swap['npv']:,.2f}")
   print(f"Fixed leg PV: ${swap['fixedLegPV']:,.2f}")
   print(f"Float leg PV: ${swap['floatLegPV']:,.2f}")
   print(f"Delta:        {swap['greeks']['delta']:.4f}")
   print(f"DV01:         {swap['greeks']['dv01']:.4f}")

**Parameters**

- ``fixedPrice`` — float. Fixed leg price K.
- ``indexCurve`` — array-like, length n. Floating index prices at each payment date.
- ``notional`` — float. Contract notional.
- ``schedule`` — array-like, length n. Payment tenors in years.
- ``r`` — float. Flat discount rate (continuous).

**Returns** — dict: ``npv``, ``fixedLegPV``, ``floatLegPV``, ``greeks`` (``delta``, ``dv01``).

asianSwap()
-----------

Arithmetic average price swap. The floating leg pays the arithmetic mean of
index prices observed over the averaging period. Averaging reduces the risk of
price manipulation in thin markets — preferred over a point-in-time swap for
all SIP index products.

.. math::

   \text{NPV} = \left(\bar{F} - K\right) \cdot N \cdot e^{-rT}

where :math:`\bar{F}` is the arithmetic mean of ``indexPrices``.

.. code-block:: python

   # Weekly index observations over the averaging period
   index_prices = np.array([185.0, 186.5, 187.0, 188.5, 187.5, 189.0, 188.0, 190.0])

   asian_swap = sq.otc.asianSwap(
       fixedPrice=187.0,
       indexPrices=index_prices,
       notional=500.0,
       r=0.046,
       T=0.25,   # 3-month contract
   )

   print(f"NPV:           ${asian_swap['npv']:,.2f}")
   print(f"Average index: {asian_swap['averageIndex']:.2f}")

**Parameters**

- ``fixedPrice`` — float.
- ``indexPrices`` — array-like. Observed or projected index prices over the averaging period.
- ``notional`` — float.
- ``r`` — float.
- ``T`` — float. Maturity in years.

**Returns** — dict: ``npv``, ``averageIndex``, ``fixedPrice``, ``dv01``.

collar()
--------

Long cap (call) + short floor (put) using Black-Scholes analytics.
Net collar price = cap premium − floor premium. Used to provide buyers
price protection while capping upside participation.

.. code-block:: python

   collar_result = sq.otc.collar(
       S=187.50,           # current spot
       capStrike=200.0,    # buyer pays no more than $200/tonne
       floorStrike=175.0,  # seller receives no less than $175/tonne
       T=0.50,             # 6-month
       r=0.046,
       sigma=0.18,         # 18% implied vol — typical for thin ag markets
       notional=1000.0,
       q=0.028,            # convenience yield acts as dividend yield
   )

   print(f"Net collar price: ${collar_result['price']:,.2f}")
   print(f"Cap premium:      ${collar_result['capPrice']:,.2f}")
   print(f"Floor premium:    ${collar_result['floorPrice']:,.2f}")
   print(f"Net delta:        {collar_result['greeks']['delta']:.4f}")

**Parameters**

- ``S`` — float. Spot price.
- ``capStrike`` — float. Cap (call) strike.
- ``floorStrike`` — float. Floor (put) strike.
- ``T`` — float. Time to expiry in years.
- ``r`` — float. Risk-free rate.
- ``sigma`` — float. Volatility.
- ``notional`` — float. Default 1.0.
- ``q`` — float. Continuous dividend / convenience yield.

**Returns** — dict: ``price``, ``capPrice``, ``floorPrice``, ``greeks`` (``delta``, ``gamma``, ``vega``, ``theta``, ``rho``).

physicalForward()
-----------------

Present value of a physically-settled forward contract, adjusted for storage
costs and quality premium. The primary instrument for Cluster E (by-products),
Cluster G (minerals), and Cluster S (construction materials) where the trade
is a direct physical commitment rather than an index-linked instrument.

.. math::

   \text{PV} = (F + \text{qualityPremium}) \cdot e^{-(r + u) T} \cdot N

.. code-block:: python

   # Physical forward for Saskatchewan wheat straw delivery
   fwd_result = sq.otc.physicalForward(
       F=95.00,               # forward price $/tonne
       deliveryTenor=0.50,    # 6-month delivery
       r=0.046,
       storageCost=0.015,     # outdoor straw storage
       qualityPremium=3.50,   # premium for baled vs. loose straw
       notional=200.0,        # tonnes
   )

   print(f"PV:       ${fwd_result['pv']:,.2f}")
   print(f"Delta:    {fwd_result['greeks']['delta']:.4f}")

**Parameters**

- ``F`` — float. Forward/futures price.
- ``deliveryTenor`` — float. Time to delivery in years.
- ``r`` — float. Risk-free rate.
- ``storageCost`` — float. Annualised storage cost rate.
- ``qualityPremium`` — float. Quality/grade premium on top of F.
- ``notional`` — float. Contract notional.

**Returns** — dict: ``pv``, ``forwardPrice``, ``adjustedForward``, ``greeks`` (``delta``, ``dv01``).

swaption()
----------

Swaption priced with Black's formula on the forward swap rate.
A payer swaption (``optType='call'``) gives the right to enter a fixed-price
swap as the fixed-price payer. Used when a counterparty wants optionality on
locking in a future index swap.

.. code-block:: python

   swaption_result = sq.otc.swaption(
       fixedPrice=190.0,
       indexCurve=index_curve,
       notional=1000.0,
       schedule=schedule,
       r=0.046,
       sigma=0.18,
       T=0.25,         # swaption expires in 3 months
       optType='call', # payer swaption
   )

   print(f"Swaption price:    ${swaption_result['price']:,.2f}")
   print(f"Forward swap rate: {swaption_result['forwardSwapRate']:.2f}")
   print(f"Vega:              {swaption_result['greeks']['vega']:.4f}")

**Parameters**

- ``fixedPrice`` — float. Fixed rate of the underlying swap.
- ``indexCurve`` — array-like. Forward index prices.
- ``notional`` — float.
- ``schedule`` — array-like. Payment tenors.
- ``r`` — float. Discount rate.
- ``sigma`` — float. Black volatility.
- ``T`` — float. Swaption expiry (must be ≤ ``schedule[0]``).
- ``optType`` — str. ``'call'`` (payer) or ``'put'`` (receiver).

**Returns** — dict: ``price``, ``forwardSwapRate``, ``annuity``, ``greeks`` (``delta``, ``vega``, ``theta``).

asianOption()
-------------

Arithmetic-average Asian option priced by Monte Carlo simulation with
antithetic variates for variance reduction. Use for exotic payoffs where
the settlement is based on the average index over a period rather than
a point-in-time price.

.. code-block:: python

   asian_opt = sq.otc.asianOption(
       S=187.50,
       K=190.0,
       T=0.50,
       r=0.046,
       sigma=0.18,
       nSims=50000,
       nSteps=26,      # 26 fortnightly steps = 6 months
       optType='call',
       q=0.028,
       seed=42,
   )

   print(f"Price:  ${asian_opt['price']:.4f}")
   print(f"Stderr: {asian_opt['stderr']:.4f}")
   print(f"Delta:  {asian_opt['greeks']['delta']:.4f}")
   print(f"Vega:   {asian_opt['greeks']['vega']:.4f}")

**Parameters**

- ``S`` — float. Spot price.
- ``K`` — float. Strike price.
- ``T`` — float. Maturity in years.
- ``r`` — float. Risk-free rate.
- ``sigma`` — float. Volatility.
- ``nSims`` — int. Simulation paths (antithetic: half base + half mirror). Default 10000.
- ``nSteps`` — int. Averaging time steps. Default 50.
- ``optType`` — str. ``'call'`` or ``'put'``.
- ``q`` — float. Convenience yield.
- ``seed`` — int or None. RNG seed for reproducibility.

**Returns** — dict: ``price``, ``stderr``, ``greeks`` (``delta``, ``vega``).

.. note::

   Greeks are computed via finite difference (1% bump for delta, +0.01 for vega).
   For production Greeks, use ``nSims >= 50000`` to reduce finite-difference noise.
