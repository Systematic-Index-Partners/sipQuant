commodity — Physical Pricing Primitives
========================================

.. module:: sipQuant.commodity

The ``commodity`` module provides the physical pricing building blocks used
throughout the SIP index and OTC stack. All functions are commodity-agnostic —
replace spot prices, storage costs, convenience yields, and grade factors with
the target cluster's market data.

Primary use clusters: A (Seasonal Ag), B (Weather-Event), C (Specialty Food),
D (Industrial Biomaterials), E (Circular Economy), F (Aquatic/Marine), H (Animal Inputs),
L (Emerging Protein), P (Soil Inputs).

.. code-block:: python

   import sipQuant as sq
   import numpy as np

seasonality()
-------------

STL-like additive decomposition of a price series into trend, seasonal, and
residual components. Uses a centred moving average for the trend and group
means of the detrended series for the seasonal component.

.. code-block:: python

   decomp = sq.commodity.seasonality(
       dates=np.arange(104),   # 2 years of weekly data
       values=weekly_prices,
       period=52,              # 52-week annual harvest cycle
       method='stl',
   )

   trend    = decomp['trend']
   seasonal = decomp['seasonal']
   residual = decomp['residual']

**Parameters**

- ``dates`` — array-like, length n. Time index (used for ordering only; can be integers).
- ``values`` — array-like of float, length n.
- ``period`` — int. Seasonal period. Use 52 for weekly data (annual cycle), 12 for monthly, 4 for quarterly.
- ``method`` — str. ``'stl'`` or ``'additive'`` (both use the same additive algorithm).

**Returns** — dict with keys: ``trend``, ``seasonal``, ``residual``, ``values``, ``period``, ``method``.

.. note::

   The seasonal component is centred so it sums to zero over one period.
   Edge values (first and last ``period//2`` observations) of ``trend`` are
   filled with the nearest valid moving-average value.

**Cluster guide**

- Cluster A (Hay, Straw, Silage): ``period=52``, weekly observations
- Cluster B (Road salt): ``period=52``, demand spikes in winter months
- Cluster F (Seaweed, Fish meal): ``period=52``, harvest season dependency
- Cluster T (Horticultural): ``period=52`` with event-spike overlays (Valentine's Day, etc.)

convenienceYield()
------------------

Extracts the implied convenience yield from the cost-of-carry relationship
between a spot price and a futures price. The convenience yield represents
the benefit of holding the physical commodity rather than the futures contract.

.. math::

   y = r + u - \frac{\ln(F/S)}{T}

where :math:`y` is the convenience yield, :math:`r` is the risk-free rate,
:math:`u` is storage cost, :math:`F` is the futures price, :math:`S` is spot,
and :math:`T` is tenor in years.

.. code-block:: python

   cy = sq.commodity.convenienceYield(
       spotPrice=187.50,
       futuresPrice=192.00,
       tenor=0.25,         # 3-month
       r=0.046,
       storageCost=0.02,   # 2% per year
   )

   print(f"Convenience yield: {cy['convenienceYield']:.4f}")
   print(f"Net carry:         {cy['netCarry']:.4f}")

**Parameters**

- ``spotPrice`` — float. Current spot price S.
- ``futuresPrice`` — float. Observed futures price F.
- ``tenor`` — float. Time to delivery in years.
- ``r`` — float. Risk-free rate (continuous).
- ``storageCost`` — float. Annualised storage cost rate.

**Returns** — dict with keys: ``convenienceYield``, ``carryAdjustedForward``, ``netCarry``.

basis()
-------

Cash price minus reference (benchmark) price. The basis captures local
supply/demand imbalances, transport differentials, and grade differences
relative to a benchmark or composite index.

.. code-block:: python

   b = sq.commodity.basis(
       cashPrice=185.00,
       referencePrice=188.00,     # SIP-AHI-001 composite
       market='lethbridge_ab',
       grade='premium_bale_14pct_moisture',
   )

   print(f"Basis:     {b['basis']:.2f} $/tonne")
   print(f"Basis bps: {b['basisBps']:.0f}")

**Parameters**

- ``cashPrice`` — float. Observed local cash price.
- ``referencePrice`` — float. Benchmark/futures/composite price.
- ``market`` — str, optional. Market label stored in output.
- ``grade`` — str, optional. Grade label stored in output.

**Returns** — dict with keys: ``basis``, ``basisBps``, ``cashPrice``, ``referencePrice``, ``market``, ``grade``.

gradeAdjustment()
-----------------

Quality-adjusted price computed as base price plus the sum of all grade
factor adjustments. Grade factors can be passed as a dict (with descriptive
keys) or as a plain list/array of float adjustments.

.. code-block:: python

   grade_factors = {
       'moisture_premium_14pct':  +2.50,
       'dockage_discount_2pct':   -1.80,
       'test_weight_premium':     +1.20,
   }

   adj = sq.commodity.gradeAdjustment(
       basePrice=185.0,
       gradeFactors=grade_factors,
   )

   print(f"Adjusted price:    {adj['adjustedPrice']:.2f}")
   print(f"Total adjustment:  {adj['totalAdjustment']:+.2f}")

**Parameters**

- ``basePrice`` — float. Unadjusted reference price.
- ``gradeFactors`` — dict or array-like. Dict keys are labels; values (or array elements) are float adjustments in price units.

**Returns** — dict with keys: ``adjustedPrice``, ``totalAdjustment``, ``gradeFactors``.

**Cluster guide**

- Cluster A: moisture %, test weight, dockage, mould
- Cluster C: certification premium (organic, fair trade, ceremonial)
- Cluster L: protein %, amino acid profile, GMO status
- Cluster Q: genetic performance metrics (EPD, EBV)
- Cluster V: certified vs uncertified seed premium

transportDifferential()
-----------------------

Delivered price at destination by adding logistics costs to the origin price.
Transport cost is 30–60% of value in Cluster A markets — this function is
critical for basis calculations between origin and destination.

.. code-block:: python

   delivered = sq.commodity.transportDifferential(
       originPrice=185.0,
       freightCost=8.50,     # $/tonne truck freight Lethbridge → Calgary
       handlingCost=1.20,    # feedlot receiving fee
       insuranceCost=0.30,
   )

   print(f"Delivered price:       {delivered['deliveredPrice']:.2f}")
   print(f"Total logistics cost:  {delivered['totalLogisticsCost']:.2f}")

**Parameters**

- ``originPrice`` — float. Price at origin.
- ``freightCost`` — float. Freight/shipping cost per unit.
- ``handlingCost`` — float. Terminal/handling charges per unit.
- ``insuranceCost`` — float. Cargo insurance per unit.

**Returns** — dict with keys: ``deliveredPrice``, ``originPrice``, ``totalLogisticsCost``, ``breakdown``.

localForwardCurve()
-------------------

Builds a local forward price curve using the cost-of-carry model adjusted
for local basis. This is the primary input to OTC pricing via ``schema.ForwardCurve``.

.. math::

   F(t) = (S + \text{basis}) \cdot e^{(r + u - y) \cdot t}

where :math:`y` is the convenience yield, :math:`u` is storage cost,
and basis adjustment shifts the spot price to reflect the local market.

.. code-block:: python

   tenors = np.array([0.0, 0.25, 0.50, 0.75, 1.0])

   fwd = sq.commodity.localForwardCurve(
       spotPrice=187.50,
       tenor=tenors,
       r=0.046,
       convYield=0.028,
       storageCost=0.020,
       basisAdjustment=-2.50,  # local market at -$2.50 to benchmark
   )

   # Wrap in ForwardCurve schema for OTC pricing
   curve = sq.schema.ForwardCurve(
       tenors=fwd['tenors'],
       prices=fwd['forwards'],
       baseDate='2026-03-14',
       market='alberta_hay_premium',
   )

**Parameters**

- ``spotPrice`` — float. Current spot price S.
- ``tenor`` — array-like. Forward tenors in years.
- ``r`` — float. Risk-free rate.
- ``convYield`` — float. Convenience yield (from ``convenienceYield()`` or assumed).
- ``storageCost`` — float. Annualised storage cost rate.
- ``basisAdjustment`` — float. Local basis adjustment to spot.

**Returns** — dict with keys: ``tenors``, ``forwards``, ``netCarry``, ``impliedConvenienceYield``.

rollingRollCost()
-----------------

Estimates roll costs from the shape of the forward curve at specified
roll indices. Used in index methodology to quantify the cost of maintaining
a rolling futures exposure.

.. code-block:: python

   roll_dates = np.array([0, 1, 2, 3])  # quarterly roll indices

   roll = sq.commodity.rollingRollCost(fwd, roll_dates)

   print(f"Quarterly roll costs:  {roll['rollCosts']}")
   print(f"Annualised roll cost:  {roll['annualizedRollCost']:.4f}")

**Parameters**

- ``forwardCurve`` — dict. Must contain ``'forwards'`` or ``'prices'`` array and ``'tenors'``.
- ``rollDates`` — array-like of int. Indices into the forwards array at which rolls occur.

**Returns** — dict with keys: ``rollCosts``, ``totalRollCost``, ``annualizedRollCost``.
