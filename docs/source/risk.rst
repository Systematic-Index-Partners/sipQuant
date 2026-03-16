risk — Risk Metrics
====================

.. module:: sipQuant.risk

Risk measurement and performance analytics. Used at three levels:
position-level (pre-trade sizing), book-level (daily risk monitoring),
and index-level (IOSCO methodology review and subscriber reporting).

Key Functions
-------------

**Value at Risk**

``parametricVar(returns, alpha=0.05, mean=None, std=None)``
    Parametric VaR assuming normal distribution.

``historicalVar(returns, alpha=0.05)``
    Historical simulation VaR — no distributional assumption. Preferred for commodity returns.

``parametricCvar(returns, alpha=0.05)``
    Parametric Conditional VaR (Expected Shortfall).

``historicalCvar(returns, alpha=0.05)``
    Historical CVaR — average loss beyond VaR.

``expectedShortfall(returns, alpha=0.05)``
    Expected Shortfall (ES) — same as CVaR.

``modifiedVar(returns, alpha=0.05)``
    Cornish-Fisher modified VaR adjusting for skewness and kurtosis.

``hillTailIndex(returns, k=None)``
    Hill tail index estimator for fat-tailed commodity return distributions.
    Use to characterise extreme risk in Cluster B (weather events) and Cluster F (quota risk).

**Drawdown**

``drawdown(prices)``
    Drawdown series from peak. Returns array of drawdowns at each point.

``maxDrawdownDuration(prices)``
    Maximum duration (in periods) of a drawdown below previous peak.

**Performance Ratios**

``sharpeRatio(returns, riskFreeRate=0.0)``
    Sharpe ratio: ``(mean(r) - rf) / std(r)`` × √252.

``sortinoRatio(returns, riskFreeRate=0.0)``
    Sortino ratio: Sharpe but downside deviation in denominator.

``calmarRatio(returns, prices)``
    Calmar ratio: annualised return / maximum drawdown.

``omegaRatio(returns, threshold=0.0)``
    Omega ratio: probability-weighted gains / losses above threshold.

``treynorRatio(returns, benchmarkReturns, riskFreeRate=0.0)``
    Treynor ratio using beta relative to benchmark.

``informationRatio(returns, benchmarkReturns)``
    Information ratio: active return / tracking error.

**Downside Risk**

``downsideDeviation(returns, riskFreeRate=0.0)``
    Semi-deviation below the risk-free rate.

``ulcerIndex(prices)``
    Ulcer Index: RMS of drawdowns — penalises prolonged drawdowns.

``painIndex(prices)``
    Pain Index: average drawdown over full period.

``beta(returns, benchmarkReturns)``
    Systematic risk relative to a benchmark.

``tailRatio(returns)``
    Right-tail / left-tail ratio — measures return distribution asymmetry.

``capturRatio(returns, benchmarkReturns)``
    Up-capture and down-capture ratios.

``stabilityRatio(returns)``
    R² of returns regressed on time — measures trend consistency.

.. code-block:: python

   import sipQuant as sq
   import numpy as np

   # Simulate 1 year of weekly index returns
   returns = np.random.normal(0.002, 0.025, 52)
   prices  = 185.0 * np.cumprod(1 + returns)

   # Standard risk metrics
   hvar = sq.risk.historicalVar(returns, alpha=0.05)
   hcvar = sq.risk.historicalCvar(returns, alpha=0.05)
   print(f"95% VaR:  {hvar:.4f}")
   print(f"95% CVaR: {hcvar:.4f}")

   # Performance metrics for IOSCO methodology review
   sharpe  = sq.risk.sharpeRatio(returns)
   sortino = sq.risk.sortinoRatio(returns)
   calmar  = sq.risk.calmarRatio(returns, prices)
   dd      = sq.risk.drawdown(prices)
   print(f"Sharpe:      {sharpe:.4f}")
   print(f"Sortino:     {sortino:.4f}")
   print(f"Calmar:      {calmar:.4f}")
   print(f"Max drawdown: {dd.min():.4f}")

   # Tail risk for thin commodity markets
   hill = sq.risk.hillTailIndex(returns)
   print(f"Hill tail index: {hill:.4f}  (lower = fatter tails)")
