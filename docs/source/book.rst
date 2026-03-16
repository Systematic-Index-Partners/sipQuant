book — Dealer Book Management
==============================

.. module:: sipQuant.book

The ``book`` module aggregates OTC positions and computes book-level Greeks,
hedge ratios, P&L attribution, scenario analysis, and margin estimates.
It operates on lists of ``schema.OTCPosition`` dicts.

**Direction sign convention:** ``buy`` / ``long`` / ``receive_fixed`` = +1;
``sell`` / ``short`` / ``pay_fixed`` = −1. All Greek contributions are scaled
by ``notional × direction_sign``.

.. code-block:: python

   import sipQuant as sq

   positions = [pos1, pos2, pos3]  # list of OTCPosition dicts

Daily Risk Workflow
-------------------

The standard morning risk run at SIP Global:

.. code-block:: python

   # 1. Net Greeks snapshot
   ng = sq.book.netGreeks(positions)

   # 2. Alert thresholds
   if abs(ng['delta']) > 500:
       print("ALERT: Net delta > ±500 tonnes — escalate to head trader")
   if abs(ng['vega']) > 50_000:
       print("ALERT: Net vega > ±$50,000 — review vol exposure")

   # 3. Delta hedge if needed
   if abs(ng['delta']) > 500:
       hedge = sq.book.hedgeRatios(positions, hedgeInstrumentDelta=1.0)
       print(f"Hedge {hedge['hedgeUnits']:.1f} futures contracts")
       print(f"Residual delta after hedging: {hedge['residualDelta']:.2f}")

   # 4. Book summary for daily report
   summary = sq.book.bookSummary(positions)
   print(f"Total notional:      {summary['totalNotional']:,.0f} tonnes")
   print(f"Positions:           {summary['nPositions']}")
   print(f"Concentration risk:  {summary['concentrationRisk']:.1%}")

netGreeks()
-----------

Aggregates Greeks across all positions in the book. Each Greek contribution
is scaled by notional and direction sign.

.. math::

   \text{NetDelta} = \sum_i \delta_i \cdot N_i \cdot \text{sign}_i

.. code-block:: python

   ng = sq.book.netGreeks(positions)

   print(f"Delta: {ng['delta']:.2f}")
   print(f"Gamma: {ng['gamma']:.4f}")
   print(f"Vega:  {ng['vega']:.2f}")
   print(f"Theta: {ng['theta']:.4f}")
   print(f"Rho:   {ng['rho']:.4f}")

**Parameters**

- ``positions`` — list of OTCPosition dicts.

**Returns** — dict: ``delta``, ``gamma``, ``vega``, ``theta``, ``rho``.

hedgeRatios()
-------------

Computes the number of hedge instruments needed to delta-neutralise the book.

.. math::

   \text{hedgeUnits} = -\frac{\text{netDelta}}{\delta_{\text{hedge}}}

.. code-block:: python

   hedge = sq.book.hedgeRatios(
       positions=positions,
       hedgeInstrumentDelta=1.0,   # 1 futures = delta 1.0
   )

   print(f"Net delta:       {hedge['netDelta']:.2f}")
   print(f"Hedge units:     {hedge['hedgeUnits']:.2f}  (negative = sell)")
   print(f"Residual delta:  {hedge['residualDelta']:.2f}  (after rounding)")

**Parameters**

- ``positions`` — list of OTCPosition dicts.
- ``hedgeInstrumentDelta`` — float. Delta of one unit of the hedge instrument (e.g. 1.0 for a futures contract, 0.5 for an ATM option).

**Returns** — dict: ``hedgeUnits``, ``netDelta``, ``residualDelta``.

pnlAttribution()
----------------

Decomposes daily P&L into delta, gamma, vega, and theta components using
a first-order Taylor expansion. Used in the daily risk report sent to
senior management.

.. math::

   dP = \delta \cdot dS + \tfrac{1}{2}\gamma \cdot dS^2 + \nu \cdot d\sigma + \theta \cdot dt

.. code-block:: python

   # End-of-day price and vol moves
   price_moves = {'default': +2.50}    # Alberta hay +$2.50/tonne
   vol_moves   = {'default': +0.005}   # vol up 50 bps

   pnl = sq.book.pnlAttribution(
       positions=positions,
       priceMoves=price_moves,
       volMoves=vol_moves,
       timeDecay=1.0,   # 1 calendar day
   )

   print(f"Total P&L:         ${pnl['totalPnL']:,.2f}")
   print(f"  Delta component: ${pnl['deltaComponent']:,.2f}")
   print(f"  Gamma component: ${pnl['gammaComponent']:,.2f}")
   print(f"  Vega component:  ${pnl['vegaComponent']:,.2f}")
   print(f"  Theta component: ${pnl['thetaComponent']:,.2f}")

   # Largest single-position P&L drivers
   for i, p in enumerate(positions):
       print(f"  Position {i}: ${pnl['totalByPosition'][i]:,.2f}")

**Parameters**

- ``positions`` — list of OTCPosition dicts. Each position may optionally carry a ``'marketId'`` key for market-specific move lookup.
- ``priceMoves`` — dict. ``{marketId: dS}``. Falls back to ``'default'`` key if no market match.
- ``volMoves`` — dict, optional. ``{marketId: dVol}``. If None, vega contribution is zero.
- ``timeDecay`` — float, optional. Calendar days elapsed. If None, theta contribution is zero.

**Returns** — dict: ``totalPnL``, ``deltaComponent``, ``gammaComponent``, ``vegaComponent``, ``thetaComponent``, ``totalByPosition`` (ndarray, per-position P&L).

scenarioShock()
---------------

Applies uniform scenario shocks to the book and computes the resulting P&L
impact. Run before scheduled market events: WASDE releases, weather events,
quota announcements, regulatory decisions.

.. code-block:: python

   # Pre-WASDE scenario analysis (calibrated to historical WASDE surprise magnitudes)
   scenarios = [
       {'name': 'bearish', 'priceShock': -15.0, 'volShock': +0.03},
       {'name': 'neutral', 'priceShock':   0.0, 'volShock':  0.00},
       {'name': 'bullish', 'priceShock': +15.0, 'volShock': -0.02},
   ]

   shocks = sq.book.scenarioShock(positions, scenarios)

   for s in shocks['scenarioResults']:
       print(f"{s['name']:10s}  P&L: ${s['pnl']:+,.2f}  "
             f"Delta: ${s['deltaContrib']:+,.2f}  Vega: ${s['vegaContrib']:+,.2f}")

**Event calibration guide**

+----------------------------------+--------------------+--------------+
| Event                            | Typical priceShock | volShock     |
+==================================+====================+==============+
| WASDE (bearish surprise)         | −$10 to −$20/t     | +0.02–0.04   |
+----------------------------------+--------------------+--------------+
| Winter weather event (Cluster B) | +$20 to +$50/t     | +0.05–0.10   |
+----------------------------------+--------------------+--------------+
| Quota cut (Cluster F)            | +$30 to +$80/t     | +0.08–0.15   |
+----------------------------------+--------------------+--------------+
| Regulatory reclassification (R)  | −$100 to +$200/t   | +0.10–0.25   |
+----------------------------------+--------------------+--------------+

**Parameters**

- ``positions`` — list of OTCPosition dicts.
- ``scenarios`` — list of dicts, each with ``'name'``, ``'priceShock'``, ``'volShock'``.

**Returns** — dict: ``scenarioResults`` (list of dicts with ``name``, ``pnl``, ``deltaContrib``, ``vegaContrib``).

bookSummary()
-------------

Summary of book composition by instrument type, with net Greeks and
concentration risk. Used in weekly risk committee reporting.

.. code-block:: python

   summary = sq.book.bookSummary(positions)

   print(f"Total notional:     {summary['totalNotional']:,.0f}")
   print(f"Positions:          {summary['nPositions']}")
   print(f"Concentration risk: {summary['concentrationRisk']:.1%}")
   for inst, notional in summary['byInstrument'].items():
       print(f"  {inst}: {notional:,.0f}")

**Returns** — dict: ``totalNotional``, ``nPositions``, ``byInstrument``, ``netGreeks``, ``concentrationRisk`` (largest single position as fraction of total notional).

marginEstimate()
----------------

Rapid intraday margin estimate. This is a working estimate only —
formal margin calls are governed by ISDA Credit Support Annexes.

.. code-block:: python

   margin = sq.book.marginEstimate(
       positions=positions,
       initialMarginRate=0.10,        # 10% of notional * |delta|
       variationMarginBuffer=0.05,    # 5% buffer on daily theta decay
   )

   print(f"Initial margin:    ${margin['initialMargin']:,.2f}")
   print(f"Variation margin:  ${margin['variationMargin']:,.2f}")
   print(f"Total margin:      ${margin['totalMargin']:,.2f}")

**Parameters**

- ``positions`` — list of OTCPosition dicts.
- ``initialMarginRate`` — float. Fraction of ``notional * |delta|``. Default 0.10.
- ``variationMarginBuffer`` — float. Multiplier on daily theta. Default 0.05.

**Returns** — dict: ``initialMargin``, ``variationMargin``, ``totalMargin``.
