index — IOSCO-Aligned Index Infrastructure
==========================================

.. module:: sipQuant.index

The ``index`` module implements the full IOSCO-aligned commodity index
calculation pipeline: trade ingestion, VWAP-weighted calculation, audit trail
generation, restatement procedures, roll schedule management, proxy regression
for sparse markets, and historical backtesting.

All SIP indices adhere to the **IOSCO Principles for Financial Benchmarks
(2013, revised 2021)**. The audit trail and restatement functions directly
implement compliance requirements.

.. code-block:: python

   import sipQuant as sq

IOSCO Alignment
---------------

The following IOSCO principles are directly addressed by this module:

- **Principle 7 (Data Sufficiency)** — minimum 3 trades per constituent required; proxy regression fills gaps flagged as estimated.
- **Principle 12 (Transparency)** — audit trail captures all calculation inputs, weights, and sources.
- **Principle 15 (Data Retention)** — audit records must be retained for 7 years; the ``auditTrail()`` output is designed for archival.
- **Principle 14 (Restatements)** — ``restatement()`` creates a documented correction record with analystId.

calculateIndex()
----------------

Calculates the index value for a given date using VWAP-weighted constituent
prices. Trades are filtered to those on or before ``calculationDate`` whose
``grade`` matches a constituent in ``indexSpec``.

.. code-block:: python

   trades = [
       sq.schema.TradeRecord('2026-03-14', 187.50, 500.0,
                             'premium_bale_14pct_moisture',
                             'lethbridge_ab', 'red_deer_ab', 'CP001'),
       sq.schema.TradeRecord('2026-03-13', 185.00, 300.0,
                             'premium_bale_14pct_moisture',
                             'ponoka_ab', 'calgary_ab', 'CP002'),
       sq.schema.TradeRecord('2026-03-12', 162.00, 400.0,
                             'feed_grade',
                             'medicine_hat_ab', 'lethbridge_ab', 'CP003'),
   ]

   spec = sq.schema.IndexSpec(
       name='SIP-AHI-001',
       version='1.0',
       constituents=['premium_bale_14pct_moisture', 'feed_grade'],
       weightsMethod='volume',
       rollRule='monthly_last_business_day',
       effectiveDate='2026-01-01',
   )

   result = sq.index.calculateIndex(trades, spec, '2026-03-14')

   print(f"Index value: {result['indexValue']:.2f}")
   print(f"Trades used: {result['nTrades']}")
   for c, vwap in result['constituentValues'].items():
       w = result['constituentWeights'][c]
       print(f"  {c}: VWAP={vwap:.2f}  weight={w:.3f}")

**Algorithm**

1. Filter: trades where ``date <= calculationDate`` and ``grade`` in ``constituents``.
2. VWAP per constituent: ``sum(price * volume) / sum(volume)``.
3. Weights: ``equal`` = 1/n; ``volume`` or ``liquidity`` = volume share; ``custom`` = equal fallback.
4. Index value: ``sum(weight_i * vwap_i)``.

**Parameters**

- ``tradeRecords`` — list of TradeRecord dicts.
- ``indexSpec`` — IndexSpec dict.
- ``calculationDate`` — comparable. Filter cutoff.

**Returns** — dict: ``indexValue``, ``constituentValues``, ``constituentWeights``, ``nTrades``, ``calculationDate``, ``methodology``.

.. warning::

   Constituents with zero matching trades receive ``vwap=0.0``. Run
   ``index.proxyRegression()`` to fill missing constituents before
   calling ``calculateIndex()`` if minimum trade count is not met.

auditTrail()
------------

Creates an IOSCO-aligned audit record for a completed index calculation.
The audit record is designed for archival — it is immutable once generated.
Archive to durable storage immediately after each calculation.

.. code-block:: python

   audit = sq.index.auditTrail(result, spec)

   print(f"Index name:    {audit['indexName']}")
   print(f"Timestamp:     {audit['timestamp']}")
   print(f"Index value:   {audit['indexValue']:.2f}")
   print(f"Checksum:      {audit['checksum']}")

   for detail in audit['constituentDetail']:
       print(f"  {detail['constituent']}: VWAP={detail['vwap']:.2f}  weight={detail['weight']:.3f}")

**Returns** — dict: ``timestamp``, ``indexName``, ``version``, ``calculationDate``, ``indexValue``, ``constituentDetail``, ``dataSourcesUsed``, ``methodologyVersion``, ``checksum``.

.. note::

   ``checksum`` is the sum of ASCII ordinals of ``str(indexValue) + str(version)``.
   It serves as a simple integrity marker to detect accidental modification of
   archived records.

restatement()
-------------

Records a methodology-compliant correction to a previously published index value.
A restatement is required when a trade is found to be non-arm's-length, or when
a data error is discovered post-publication. The result must be disclosed to
subscribers within 1 business day per IOSCO Principle 14.

.. code-block:: python

   restate = sq.index.restatement(
       originalRecord=audit,
       correctedValue=186.20,
       reason='Trade CP001 on 2026-03-14 excluded — found to be related-party transaction',
       analystId='ANALYST_007',
   )

   print(f"Original:       {restate['originalValue']:.2f}")
   print(f"Corrected:      {restate['correctedValue']:.2f}")
   print(f"Delta:          {restate['delta']:+.2f}")
   print(f"Restatement ID: {restate['restatementId']}")

**Parameters**

- ``originalRecord`` — dict. The original ``auditTrail()`` output.
- ``correctedValue`` — float. The corrected index value.
- ``reason`` — str. Human-readable explanation. Archive with restatement log.
- ``analystId`` — str. Authorising analyst identifier.

**Returns** — dict: ``originalValue``, ``correctedValue``, ``delta``, ``reason``, ``analystId``, ``timestamp``, ``restatementId``.

.. warning::

   ``restatementId`` is a module-level sequential integer. It resets to zero
   on each Python session. Persistent restatement IDs must be managed by the
   caller's archival system.

rollSchedule()
--------------

Generates index roll dates between two dates at a specified frequency.
Roll schedules are published to subscribers at the start of each calendar year.

.. code-block:: python

   schedule = sq.index.rollSchedule(
       indexSpec=spec,
       startDate=738887,   # integer ordinal for 2026-01-01
       endDate=739252,     # integer ordinal for 2027-01-01
       step='monthly',
   )

   print(f"Rolls in 2026: {schedule['nRolls']}")

**Parameters**

- ``indexSpec`` — IndexSpec dict.
- ``startDate`` — int. Start ordinal.
- ``endDate`` — int. End ordinal.
- ``step`` — str. ``'monthly'`` (≈30 days), ``'weekly'`` (≈7 days), ``'quarterly'`` (≈91 days).

**Returns** — dict: ``rollDates``, ``nRolls``, ``step``.

proxyRegression()
-----------------

Constructs a proxy estimate for a constituent market that has insufficient
trade activity (fewer than 3 trades in the window). Uses OLS or Huber
regression against a correlated liquid series (e.g. CME Corn futures for
grain-based indices, CME Canola for canola meal).

The proxy is flagged as estimated in the audit record — it is never presented
as an observed price.

.. code-block:: python

   # Target: Saskatchewan straw (sparse)
   # Proxy: Alberta hay (more liquid, correlated)
   proxy = sq.index.proxyRegression(
       targetSeries=sask_straw_prices,
       proxySeries=alberta_hay_prices,
       method='huber',   # robust to outliers — important for thin markets
   )

   print(f"R-squared:   {proxy['rSquared']:.4f}")
   print(f"Slope:       {proxy['coefficients'][0]:.4f}")
   print(f"Intercept:   {proxy['intercept']:.4f}")

   # Use predicted values to fill gaps
   filled_prices = proxy['predictedValues']

**Parameters**

- ``targetSeries`` — array-like. The sparse series to reconstruct.
- ``proxySeries`` — array-like. The liquid proxy series. Same length.
- ``method`` — str. ``'ols'`` (default) or ``'huber'`` (IRLS with Huber weights — recommended for thin markets with outliers).

**Returns** — dict: ``coefficients``, ``intercept``, ``rSquared``, ``predictedValues``, ``residuals``.

.. note::

   Use ``'huber'`` when the thin market contains potential outlier trades
   (non-arm's-length, data errors). The Huber method downweights large residuals
   iteratively using a 1.345 × MAD threshold.

backtestIndex()
---------------

Runs ``calculateIndex()`` across a list of historical dates and computes
return, volatility, and maximum drawdown statistics. Used during the annual
methodology review to assess index stability.

.. code-block:: python

   backtest = sq.index.backtestIndex(
       tradeRecords=all_trades,
       indexSpec=spec,
       dates=['2025-01-31', '2025-02-28', '2025-03-31',
              '2025-04-30', '2025-05-31', '2025-06-30'],
   )

   print(f"Annualised volatility: {backtest['volatility']:.4f}")
   print(f"Maximum drawdown:      {backtest['maxDrawdown']:.4f}")

**Parameters**

- ``tradeRecords`` — list of TradeRecord dicts.
- ``indexSpec`` — IndexSpec dict.
- ``dates`` — list. Ordered calculation dates.

**Returns** — dict: ``dates``, ``indexValues`` (ndarray), ``returns`` (log returns, length n-1), ``volatility`` (annualised), ``maxDrawdown``.
