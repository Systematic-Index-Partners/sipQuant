Getting Started
===============

sipQuant implements the full SIP Global pricing pipeline:
**trade data → price series → seasonality → forward curve → index → OTC instrument → dealer book → risk**.

All inputs are validated schema objects. All outputs are plain dicts or NumPy arrays.

Installation
------------

.. code-block:: bash

   pip install sipQuant

Requires Python 3.10+ and NumPy 1.23+. No other dependencies.

Import Convention
-----------------

.. code-block:: python

   import sipQuant as sq
   import numpy as np

All 17 modules are available as ``sq.<module>``.

The Full Pipeline
-----------------

The following example walks through building a pricing index for an Alberta hay market
(Cluster A — Seasonal Agricultural Bulk) and structuring an OTC swap against it.

Step 1 — Ingest Physical Trade Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Physical trades are the primary data source for thin commodity markets.
Each trade is validated before entering the calculation pipeline.

.. code-block:: python

   trade = sq.schema.TradeRecord(
       date='2026-03-14',
       price=187.50,
       volume=500.0,
       grade='premium_bale_14pct_moisture',
       origin='lethbridge_ab',
       destination='red_deer_ab',
       counterpartyId='CP_ANON_004',
   )

   errors = sq.schema.validate(trade)
   assert errors == [], f"Trade validation failed: {errors}"

For markets with broker quotes rather than physical trades, use ``QuoteSheet``:

.. code-block:: python

   quote = sq.schema.QuoteSheet(
       date='2026-03-14',
       bid=186.00,
       ask=189.00,
       mid=187.50,
       source='broker_prairie_ag',
       market='alberta_hay_premium',
       grade='premium_bale_14pct_moisture',
       tenor=0.25,
   )

Step 2 — Build a Price Series
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assemble weekly broker quotes into a validated price series:

.. code-block:: python

   dates = np.array([
       '2026-01-06', '2026-01-13', '2026-01-20', '2026-01-27',
       '2026-02-03', '2026-02-10', '2026-02-17',
   ], dtype='datetime64')
   prices = np.array([182.0, 184.5, 187.0, 186.0, 185.5, 183.0, 187.50])

   ps = sq.schema.PriceSeries(
       dates=dates,
       values=prices,
       source='broker_prairie_ag',
       market='alberta_hay_premium',
       grade='premium_bale_14pct_moisture',
   )

For markets with irregular observations (most SIP thin markets), use ``SparsePriceSeries``:

.. code-block:: python

   sparse_ps = sq.schema.SparsePriceSeries(
       dates=dates[:4],
       values=prices[:4],
       source='broker_prairie_ag',
       market='alberta_hay_premium',
       maxGapDays=14,  # flags gaps > 2 weeks
   )

Step 3 — Decompose Seasonality
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For Cluster A markets, the harvest cycle creates a strong annual seasonal pattern.
Use a 52-week period for weekly observations:

.. code-block:: python

   # Need at least 2 full years for robust seasonal decomposition
   # Using synthetic 2-year weekly series for illustration
   n = 104  # 2 years of weekly data
   t = np.arange(n)
   long_prices = 185.0 + 10 * np.sin(2 * np.pi * t / 52) + np.random.normal(0, 2, n)

   decomp = sq.commodity.seasonality(
       dates=t,
       values=long_prices,
       period=52,
       method='stl',
   )

   trend    = decomp['trend']     # underlying price trend
   seasonal = decomp['seasonal']  # harvest-cycle component
   residual = decomp['residual']  # unexplained noise

Step 4 — Extract Convenience Yield
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When futures prices are available, extract the implied convenience yield:

.. code-block:: python

   cy = sq.commodity.convenienceYield(
       spotPrice=187.50,
       futuresPrice=192.00,
       tenor=0.25,       # 3-month futures
       r=0.046,
       storageCost=0.02, # 2% annualised bale storage
   )
   print(f"Convenience yield: {cy['convenienceYield']:.4f}")
   print(f"Net carry: {cy['netCarry']:.4f}")

Step 5 — Compute Local Basis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The local basis is the cash price minus the benchmark (e.g. the SIP composite index):

.. code-block:: python

   b = sq.commodity.basis(
       cashPrice=185.00,
       referencePrice=188.00,
       market='lethbridge_ab',
       grade='premium_bale_14pct_moisture',
   )
   print(f"Basis: {b['basis']:.2f} $/tonne  ({b['basisBps']:.0f} bps)")

Step 6 — Build the Local Forward Curve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The forward curve drives all OTC pricing:

.. code-block:: python

   tenors = np.array([0.0, 0.25, 0.50, 0.75, 1.0])

   fwd = sq.commodity.localForwardCurve(
       spotPrice=187.50,
       tenor=tenors,
       r=0.046,
       convYield=cy['convenienceYield'],
       storageCost=0.02,
       basisAdjustment=-2.50,
   )

   curve = sq.schema.ForwardCurve(
       tenors=fwd['tenors'],
       prices=fwd['forwards'],
       baseDate='2026-03-14',
       market='alberta_hay_premium',
   )

Step 7 — Price an OTC Commodity Swap
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Price a fixed-float swap where the counterparty pays fixed at $190/tonne:

.. code-block:: python

   swap = sq.otc.commoditySwap(
       fixedPrice=190.0,
       indexCurve=curve['prices'],
       notional=1000.0,      # tonnes
       schedule=curve['tenors'],
       r=0.046,
   )

   print(f"Swap NPV:       ${swap['npv']:,.2f}")
   print(f"Fixed leg PV:   ${swap['fixedLegPV']:,.2f}")
   print(f"Float leg PV:   ${swap['floatLegPV']:,.2f}")
   print(f"Delta:          {swap['greeks']['delta']:.4f}")

Step 8 — Register the Position in the Dealer Book
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   pos = sq.schema.OTCPosition(
       instrumentType='commodity_swap',
       direction='receive_fixed',
       notional=1000.0,
       strikeOrFixed=190.0,
       expiry='2026-12-31',
       counterpartyId='CP_ANON_004',
       greeks={
           'delta': swap['greeks']['delta'],
           'gamma': 0.0,
           'vega': 0.0,
           'theta': -0.05,
           'rho': swap['greeks']['dv01'],
       },
   )

   positions = [pos]
   ng = sq.book.netGreeks(positions)
   print(f"Book net delta: {ng['delta']:.2f}")

Step 9 — Calculate the IOSCO Index
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   spec = sq.schema.IndexSpec(
       name='SIP-AHI-001',
       version='1.0',
       constituents=['premium_bale_14pct_moisture', 'feed_grade'],
       weightsMethod='volume',
       rollRule='monthly_last_business_day',
       effectiveDate='2026-01-01',
   )

   # Multiple trade records needed for a real index
   trades = [
       sq.schema.TradeRecord('2026-03-14', 187.50, 500.0,
                             'premium_bale_14pct_moisture', 'lethbridge_ab', 'red_deer_ab', 'CP001'),
       sq.schema.TradeRecord('2026-03-13', 185.00, 300.0,
                             'premium_bale_14pct_moisture', 'ponoka_ab', 'calgary_ab', 'CP002'),
       sq.schema.TradeRecord('2026-03-12', 162.00, 400.0,
                             'feed_grade', 'medicine_hat_ab', 'lethbridge_ab', 'CP003'),
   ]

   result = sq.index.calculateIndex(trades, spec, '2026-03-14')
   audit  = sq.index.auditTrail(result, spec)

   print(f"Index value:    {result['indexValue']:.2f}")
   print(f"Trades used:    {result['nTrades']}")
   print(f"Checksum:       {audit['checksum']}")

Step 10 — Assess Thin-Market Liquidity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before sizing a position, score the market's liquidity:

.. code-block:: python

   score = sq.liquidity.thinMarketScore(trades, window=30)
   print(f"Liquidity score: {score['score']:.3f}  (n={score['nTrades']} trades in 30 days)")

   # Compute LVAR for position sizing
   returns = np.diff(np.log(np.array([t['price'] for t in trades])))
   volumes = np.array([t['volume'] for t in trades[:-1]])

   if len(returns) > 0:
       lvar = sq.liquidity.liquidityAdjustedVar(returns, volumes, alpha=0.05)
       print(f"LVAR:  {lvar['lvar']:.4f}  (VaR: {lvar['var']:.4f}  LiqCost: {lvar['liquidityCost']:.4f})")

Next Steps
----------

- See :doc:`cluster_taxonomy` for the full 26-cluster reference and module mapping
- See :doc:`index_module` for the IOSCO methodology and restatement procedures
- See :doc:`otc` for all OTC instrument types and when to use each
- See :doc:`sim` for process selection by cluster type
- See :doc:`liquidity` for thin-market risk management
