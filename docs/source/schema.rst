schema — Data Contract Layer
=============================

.. module:: sipQuant.schema

The ``schema`` module is the data contract layer for all of sipQuant.
Every pricing, risk, index, and book function accepts validated schema objects
rather than raw arrays. This ensures consistent, validated inputs across the
entire stack regardless of which module is called.

All schema objects are plain Python dicts with a ``'type'`` key. This keeps
them lightweight, serialisable, and framework-agnostic.

.. code-block:: python

   import sipQuant as sq

   trade = sq.schema.TradeRecord(
       date='2026-03-14', price=187.50, volume=500.0,
       grade='premium_bale_14pct_moisture',
       origin='lethbridge_ab', destination='red_deer_ab',
       counterpartyId='CP_ANON_004',
   )
   errors = sq.schema.validate(trade)
   assert errors == []

Schema Objects
--------------

PriceSeries
~~~~~~~~~~~

Regular, evenly-spaced price time series. Use for broker quotes, exchange
settlements, or any daily/weekly series with consistent observation frequency.

.. code-block:: python

   ps = sq.schema.PriceSeries(
       dates=np.array(['2026-01-06', '2026-01-13'], dtype='datetime64'),
       values=np.array([182.0, 184.5]),
       source='broker_prairie_ag',
       market='alberta_hay_premium',
       grade='premium_bale_14pct_moisture',  # optional
   )

**Parameters**

- ``dates`` — array-like. Observation dates. Any comparable type.
- ``values`` — array-like of float. Must be same length as ``dates``.
- ``source`` — str. Data source identifier (broker name, exchange, internal).
- ``market`` — str. Market identifier (e.g. ``'alberta_hay_premium'``).
- ``grade`` — str, optional. Grade specification.

**Returns** — dict with keys: ``type``, ``dates``, ``values``, ``source``, ``market``, ``grade``, ``n``.

**Raises** — ``ValueError`` if lengths mismatch or values is empty.

SparsePriceSeries
~~~~~~~~~~~~~~~~~

Irregularly-spaced price series for thin markets with ad-hoc or infrequent
observations. Stores gap metadata for use in proxy and interpolation routines.
The majority of SIP Cluster markets (B through Z) require this type rather than
``PriceSeries``.

.. code-block:: python

   sparse_ps = sq.schema.SparsePriceSeries(
       dates=dates,
       values=prices,
       source='internal_survey',
       market='alberta_hay_feed',
       maxGapDays=21,  # flags gaps > 3 weeks in gapFlags array
   )

**Parameters**

- ``dates`` — array-like. Must be monotonically non-decreasing.
- ``values`` — array-like of float.
- ``source`` — str.
- ``market`` — str.
- ``maxGapDays`` — int, optional. If provided, ``gapFlags`` array marks gaps exceeding this threshold.

**Returns** — dict with keys: ``type``, ``dates``, ``values``, ``source``, ``market``, ``maxGapDays``, ``gapFlags``, ``n``.

TradeRecord
~~~~~~~~~~~

A single physical trade observation. Physical trades are the primary input
to index calculation (``index.calculateIndex``) and proxy regression
(``index.proxyRegression``). Each trade must pass validation before entering
the calculation pipeline.

.. code-block:: python

   trade = sq.schema.TradeRecord(
       date='2026-03-14',
       price=187.50,
       volume=500.0,           # tonnes
       grade='premium_bale_14pct_moisture',
       origin='lethbridge_ab',
       destination='red_deer_ab',
       counterpartyId='CP_ANON_004',
   )

**Parameters**

- ``date`` — any. Trade date.
- ``price`` — float. Must be positive.
- ``volume`` — float. Traded volume in any unit. Must be positive.
- ``grade`` — str. Quality specification at time of trade. Must match ``IndexSpec`` constituents for index inclusion.
- ``origin`` — str. Origin delivery point.
- ``destination`` — str. Destination delivery point.
- ``counterpartyId`` — str. Anonymised counterparty identifier.

**Returns** — dict with keys: ``type``, ``date``, ``price``, ``volume``, ``grade``, ``origin``, ``destination``, ``counterpartyId``.

**Raises** — ``ValueError`` if ``price <= 0`` or ``volume <= 0``.

QuoteSheet
~~~~~~~~~~

An OTC broker quote with full bid/ask/mid metadata. Use when no physical
trade has occurred but broker quotes are available as a mark-to-model input.

.. code-block:: python

   quote = sq.schema.QuoteSheet(
       date='2026-03-14',
       bid=186.00,
       ask=189.00,
       mid=187.50,
       source='broker_prairie_ag',
       market='alberta_hay_premium',
       grade='premium_bale_14pct_moisture',
       tenor=0.25,  # 3-month quote
   )

**Parameters**

- ``date`` — any.
- ``bid`` — float or None.
- ``ask`` — float or None.
- ``mid`` — float. Required.
- ``source`` — str.
- ``market`` — str.
- ``grade`` — str.
- ``tenor`` — float. Contract tenor in years.

**Returns** — dict with keys: ``type``, ``date``, ``bid``, ``ask``, ``mid``, ``source``, ``market``, ``grade``, ``tenor``.

**Raises** — ``ValueError`` if ``bid > ask`` (when both provided) or ``tenor < 0``.

ForwardCurve
~~~~~~~~~~~~

A validated forward price curve. The primary input to all OTC pricing
functions (``otc.commoditySwap``, ``otc.collar``, etc.). Built from
``commodity.localForwardCurve`` or ``bootstrap.forwardCurve``.

.. code-block:: python

   curve = sq.schema.ForwardCurve(
       tenors=np.array([0.25, 0.50, 0.75, 1.0]),
       prices=np.array([188.0, 190.5, 192.0, 193.5]),
       baseDate='2026-03-14',
       market='alberta_hay_premium',
       methodology='linear',
   )

**Parameters**

- ``tenors`` — array-like of float. In years. Must be monotonically non-decreasing and non-negative.
- ``prices`` — array-like of float. Must all be positive.
- ``baseDate`` — any. The as-of date for the curve.
- ``market`` — str.
- ``methodology`` — str, optional. Interpolation method. Default ``'linear'``.

**Returns** — dict with keys: ``type``, ``tenors``, ``prices``, ``baseDate``, ``market``, ``methodology``, ``n``.

**Raises** — ``ValueError`` if tenors not monotone, any price non-positive, or length mismatch.

OTCPosition
~~~~~~~~~~~

A live OTC position record for dealer book aggregation. All book functions
(``book.netGreeks``, ``book.pnlAttribution``, etc.) operate on lists of
``OTCPosition`` dicts.

.. code-block:: python

   pos = sq.schema.OTCPosition(
       instrumentType='commodity_swap',
       direction='receive_fixed',   # long the index
       notional=1000.0,             # tonnes
       strikeOrFixed=190.0,
       expiry='2026-12-31',
       counterpartyId='CP_ANON_004',
       greeks={
           'delta': 950.0,
           'gamma': 0.0,
           'vega': 0.0,
           'theta': -50.0,
           'rho': 0.3,
       },
   )

**Parameters**

- ``instrumentType`` — str. E.g. ``'commodity_swap'``, ``'collar'``, ``'physical_forward'``.
- ``direction`` — str. One of: ``'buy'``, ``'sell'``, ``'pay_fixed'``, ``'receive_fixed'``, ``'long'``, ``'short'``.
- ``notional`` — float. Must be positive.
- ``strikeOrFixed`` — float. Strike (options) or fixed rate (swaps).
- ``expiry`` — any. Contract expiry.
- ``counterpartyId`` — str.
- ``greeks`` — dict, optional. Keys: ``delta``, ``gamma``, ``vega``, ``theta``, ``rho``. Defaults to all zeros.

**Returns** — dict with keys: ``type``, ``instrumentType``, ``direction``, ``notional``, ``strikeOrFixed``, ``expiry``, ``counterpartyId``, ``greeks``.

**Raises** — ``ValueError`` if direction not valid or notional non-positive.

IndexSpec
~~~~~~~~~

An immutable index methodology specification. Governs the index calculation
and is pinned to each audit record. Changing the methodology requires creating
a new ``IndexSpec`` with an incremented version string.

.. code-block:: python

   spec = sq.schema.IndexSpec(
       name='SIP-AHI-001',
       version='1.0',
       constituents=['premium_bale_14pct_moisture', 'feed_grade'],
       weightsMethod='volume',
       rollRule='monthly_last_business_day',
       effectiveDate='2026-01-01',
   )

**Parameters**

- ``name`` — str. Index name (e.g. ``'SIP-AHI-001'``).
- ``version`` — str. Methodology version.
- ``constituents`` — list of str. Grade identifiers that contribute to the index. Must match ``TradeRecord.grade`` values.
- ``weightsMethod`` — str. One of: ``'equal'``, ``'volume'``, ``'liquidity'``, ``'custom'``.
- ``rollRule`` — str. Roll logic description.
- ``effectiveDate`` — any. Date from which this version is effective.

**Returns** — dict with keys: ``type``, ``name``, ``version``, ``constituents``, ``weightsMethod``, ``rollRule``, ``effectiveDate``.

**Raises** — ``ValueError`` if ``weightsMethod`` not valid or ``constituents`` empty.

Validation
----------

validate()
~~~~~~~~~~

Universal validation dispatcher. Runs type-specific checks on any schema
object and returns a list of error strings. An empty list means the object
is valid. Always call ``validate()`` before passing objects to pricing
or index functions in production pipelines.

.. code-block:: python

   errors = sq.schema.validate(trade)
   if errors:
       raise ValueError(f"Invalid trade: {errors}")

   # Validate multiple objects at once
   for obj in [trade, ps, spec, curve, pos]:
       errs = sq.schema.validate(obj)
       if errs:
           raise ValueError(f"{obj['type']} validation failed: {errs}")

**Parameters**

- ``obj`` — dict. Any sipQuant schema object.

**Returns** — list of str. Empty if valid.

Valid Types
-----------

+------------------+----------------------------------+
| Type             | Use in                           |
+==================+==================================+
| PriceSeries      | commodity, sim, fit, econometrics|
+------------------+----------------------------------+
| SparsePriceSeries| index (thin markets)             |
+------------------+----------------------------------+
| TradeRecord      | index.calculateIndex             |
+------------------+----------------------------------+
| QuoteSheet       | otc pricing mark-to-model        |
+------------------+----------------------------------+
| ForwardCurve     | otc, book, bootstrap             |
+------------------+----------------------------------+
| OTCPosition      | book (all functions)             |
+------------------+----------------------------------+
| IndexSpec        | index (all functions)            |
+------------------+----------------------------------+
