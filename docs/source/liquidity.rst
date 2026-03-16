liquidity — Thin-Market Risk
=============================

.. module:: sipQuant.liquidity

The ``liquidity`` module provides risk tools specifically designed for the
thin, opaque physical commodity markets that SIP Global operates in.
Standard VaR and execution models assume market depth that does not exist
in these markets — this module applies the Bangia et al. LVAR framework
and Almgren-Chriss execution model to properly size and exit positions.

.. code-block:: python

   import sipQuant as sq
   import numpy as np

liquidityAdjustedVar()
-----------------------

Liquidity-adjusted Value-at-Risk (LVAR) following Bangia, Diebold, Schuermann,
and Stroughair (1999). Adds a liquidity cost component to standard historical
VaR to account for the cost of exiting a position in a thin market.

.. math::

   \text{LVAR} = \text{VaR} + \tfrac{1}{2} \cdot s

where :math:`s` is the bid-ask spread cost as a fraction of position value.
The 0.5 factor reflects that on average half the spread is paid on entry or exit.

When ``spreadCost`` is not provided, it is estimated from volume data:

.. math::

   s = \frac{1}{\sqrt{V_t / \bar{V}}} \cdot s_0

where :math:`s_0 = 0.001` is the base spread and :math:`V_t / \bar{V}` is
the volume ratio relative to the mean.

.. code-block:: python

   returns = np.array([-0.02, 0.01, -0.03, 0.02, -0.01, 0.04, -0.02, 0.01, -0.05, 0.02])
   volumes = np.array([150, 200, 80, 300, 120, 250, 90, 180, 60, 220], dtype=float)

   lvar = sq.liquidity.liquidityAdjustedVar(
       returns=returns,
       volumes=volumes,
       alpha=0.05,          # 95% confidence
       spreadCost=None,     # estimated from volumes
   )

   print(f"LVAR:           {lvar['lvar']:.4f}")
   print(f"VaR (standard): {lvar['var']:.4f}")
   print(f"Liquidity cost: {lvar['liquidityCost']:.4f}")
   print(f"Spread cost:    {lvar['spreadCost']:.4f}")

**Parameters**

- ``returns`` — array-like. Historical return series (proportional, not percentage).
- ``volumes`` — array-like. Contemporaneous traded volumes.
- ``alpha`` — float. Confidence level tail (e.g. 0.05 = 95% LVAR).
- ``spreadCost`` — float or None. If None, estimated from volume data.

**Returns** — dict: ``lvar``, ``var``, ``liquidityCost``, ``spreadCost``.

marketImpact()
--------------

Estimates the market impact of a trade using the Almgren-Chriss framework.
In thin commodity markets, even moderate trade sizes can move the market
significantly. Use this before sizing positions.

**Models:**

- ``'almgren-chriss'`` (default): permanent impact = γ × (size/ADV); temporary impact = η × √(size/ADV)
- ``'linear'``: permanent impact = γ × (size/ADV); temporary impact = η × (size/ADV)

The square-root temporary impact in Almgren-Chriss reflects empirical evidence
that impact scales with the square root of participation rate.

.. code-block:: python

   impact = sq.liquidity.marketImpact(
       tradeSize=500.0,      # tonnes
       adv=800.0,            # average daily volume in this market
       model='almgren-chriss',
       eta=0.1,              # temporary impact coefficient
       gamma=0.1,            # permanent impact coefficient
   )

   print(f"Permanent impact:  {impact['permanentImpact']:.4f}")
   print(f"Temporary impact:  {impact['temporaryImpact']:.4f}")
   print(f"Total impact:      {impact['totalImpact']:.4f}")
   print(f"Impact in bps:     {impact['impactBps']:.1f}")

**Parameters**

- ``tradeSize`` — float.
- ``adv`` — float. Average daily volume. Must be positive.
- ``model`` — str. ``'almgren-chriss'`` or ``'linear'``.
- ``eta`` — float. Temporary impact coefficient.
- ``gamma`` — float. Permanent impact coefficient.

**Returns** — dict: ``permanentImpact``, ``temporaryImpact``, ``totalImpact``, ``impactBps``.

optimalExecution()
------------------

Almgren-Chriss optimal liquidation schedule. Solves for the trade schedule
that minimises expected execution cost plus risk cost over a given horizon.
The key parameter ``kappa`` determines the shape of the trajectory:
low kappa → near-uniform schedule; high kappa → front-loaded schedule.

.. math::

   \kappa = \sqrt{\frac{\lambda \sigma^2}{\eta}}

.. code-block:: python

   schedule_result = sq.liquidity.optimalExecution(
       totalShares=1000.0,  # total tonnes to liquidate
       T=10,                # liquidate over 10 trading periods
       adv=800.0,
       sigma=0.02,          # 2% daily price vol
       eta=0.1,
       gamma=0.1,
       riskAversion=1e-6,
   )

   print(f"Kappa:             {schedule_result['kappa']:.6f}")
   print(f"Expected cost:     ${schedule_result['expectedCost']:,.2f}")
   print(f"Expected variance: {schedule_result['expectedVariance']:.4f}")
   print(f"Schedule: {schedule_result['schedule'].round(1)}")

**Parameters**

- ``totalShares`` — float. Total position to unwind.
- ``T`` — int. Number of trading periods.
- ``adv`` — float. Average daily volume.
- ``sigma`` — float. Daily price volatility (as fraction, e.g. 0.02).
- ``eta`` — float. Temporary impact coefficient.
- ``gamma`` — float. Permanent impact coefficient.
- ``riskAversion`` — float. Lambda — trade-off between cost and risk. Default 1e-6.

**Returns** — dict: ``schedule`` (ndarray, shares per period), ``trajectory`` (ndarray, remaining shares), ``expectedCost``, ``expectedVariance``, ``kappa``.

thinMarketScore()
-----------------

Computes a liquidity score in [0, 1] for a commodity market based on trade
frequency and price stability. Use before deciding position size or whether
to use OLS vs Huber proxy regression. Score < 0.1 indicates an extremely
thin market requiring maximum caution.

.. math::

   \text{score} = \text{clip}\left(\frac{n_{\text{trades}}}{\text{window}} \cdot (1 - |\text{CV}|),\ 0,\ 1\right)

where CV = std(prices) / mean(prices) is the price coefficient of variation.

.. code-block:: python

   score = sq.liquidity.thinMarketScore(
       tradeRecords=trades,   # list of TradeRecord dicts
       window=30,             # 30-day lookback
   )

   print(f"Liquidity score: {score['score']:.3f}")
   print(f"Trades in window: {score['nTrades']}")
   print(f"Avg volume:       {score['avgVolume']:.0f} tonnes")
   print(f"Price CV:         {score['priceCV']:.4f}")

   # Decision logic
   if score['score'] < 0.1:
       print("Extremely thin — use Huber proxy, max LVAR position sizing")
   elif score['score'] < 0.3:
       print("Thin — use proxyRegression, apply LVAR")
   else:
       print("Moderate — standard index calculation viable")

**Parameters**

- ``tradeRecords`` — list of TradeRecord dicts.
- ``window`` — int. Lookback in days. Default 30.

**Returns** — dict: ``score``, ``nTrades``, ``avgVolume``, ``priceCV``, ``window``.

concentrationRisk()
-------------------

Herfindahl-Hirschman Index (HHI) for position concentration across markets.
HHI = 1 indicates a single dominant position; HHI = 1/n indicates perfectly
diversified. Used to flag over-concentration in a single thin market.

.. code-block:: python

   positions_array = np.array([500.0, 200.0, 150.0, 50.0])  # tonnes
   adv_array       = np.array([800.0, 400.0, 250.0, 100.0])

   conc = sq.liquidity.concentrationRisk(
       positions=positions_array,
       volumes=adv_array,
   )

   print(f"HHI:                {conc['hhi']:.4f}")
   print(f"Concentration score:{conc['concentrationScore']:.4f}")
   print(f"Participation rates:{conc['participationRates'].round(3)}")

**Parameters**

- ``positions`` — array-like. Position sizes (signed; absolute values used for HHI).
- ``volumes`` — array-like. Average daily volumes for each position.

**Returns** — dict: ``hhi``, ``participationRates`` (|pos|/vol per position), ``concentrationScore``.

optimalLiquidation()
--------------------

Estimates total cost of liquidating a position under TWAP or VWAP execution
over a given time horizon. VWAP is approximated as 90% of TWAP cost,
reflecting the benefit of concentrating execution in higher-volume windows.

.. code-block:: python

   liq = sq.liquidity.optimalLiquidation(
       position=1000.0,       # tonnes
       adv=800.0,
       sigma=0.02,
       timeHorizon=5,         # 5 trading periods
       costPerUnit=0.001,     # fixed transaction cost
   )

   print(f"TWAP cost:    ${liq['twapCost']:,.2f}")
   print(f"VWAP cost:    ${liq['vwapCost']:,.2f}")
   print(f"Market impact cost: ${liq['marketImpactCost']:,.2f}")
   print(f"Schedule: {liq['liquidationSchedule'].round(0)} tonnes/period")

**Parameters**

- ``position`` — float. Total position to liquidate.
- ``adv`` — float. Average daily volume.
- ``sigma`` — float. Daily price volatility.
- ``timeHorizon`` — int. Number of trading periods.
- ``costPerUnit`` — float. Fixed cost per unit traded. Default 0.001.

**Returns** — dict: ``twapCost``, ``vwapCost``, ``liquidationSchedule``, ``estimatedSlippage``, ``marketImpactCost``.

Thin-Market Workflow
--------------------

The recommended sequence before trading any new SIP cluster market:

.. code-block:: python

   # 1. Score market liquidity
   score = sq.liquidity.thinMarketScore(recent_trades, window=30)

   # 2. Estimate market impact before sizing the trade
   impact = sq.liquidity.marketImpact(
       tradeSize=proposed_size,
       adv=score['avgVolume'],
   )

   # 3. Compute LVAR for position limit
   if len(returns) >= 5:
       lvar_result = sq.liquidity.liquidityAdjustedVar(returns, volumes)
       position_limit = max_loss_tolerance / lvar_result['lvar']

   # 4. Plan optimal exit if needed
   exit_plan = sq.liquidity.optimalLiquidation(
       position=proposed_size,
       adv=score['avgVolume'],
       sigma=np.std(returns) if len(returns) > 1 else 0.02,
       timeHorizon=10,
   )
   print(f"Exit cost estimate: ${exit_plan['twapCost']:,.2f}")
