# sipQuant

**Quantitative library for physically-settled commodity markets.**
Built by [SIP Global — Systematic Index Partners](https://sipglobally.com/).

[![PyPI](https://img.shields.io/badge/PyPI-sipQuant-blue)](https://pypi.org/project/sipQuant/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docs](https://readthedocs.org/projects/sipquant/badge/?version=latest)](https://sipquant.readthedocs.io/en/latest/)

---

## About

sipQuant is a pure-NumPy quantitative stack for building, maintaining, and trading against physically-settled commodity price indices in thin, opaque markets. It covers the full pipeline from raw trade data to OTC structured products.

It is the internal quantitative infrastructure of SIP Global, open-sourced under GPL-3.0. All mathematics are implemented in pure NumPy — no pandas, scipy, or other external dependencies.

## About SIP Global

Systematic Index Partners (SIP Global) brings liquidity to overlooked markets that move the world. We apply systematic rigour and modern trading standards to create transparent pricing, real liquidity, and durable market function in physically-settled commodity markets across 26 cluster types — from seasonal agricultural bulk to artisanal small-batch outputs.

*Tota Ad Manum.*

[Visit SIP Global](https://sipglobally.com/)

---

## Installation

```bash
pip install sipQuant
```

Requires Python 3.10+ and NumPy 1.23+. No other dependencies.

---

## Quick Start

The full SIP pricing pipeline in one block:

```python
import sipQuant as sq
import numpy as np

# 1. Ingest a physical trade
trade = sq.schema.TradeRecord(
    date='2026-03-14',
    price=187.50,
    volume=500.0,
    grade='premium_bale_14pct_moisture',
    origin='lethbridge_ab',
    destination='red_deer_ab',
    counterpartyId='CP_ANON_004',
)
assert sq.schema.validate(trade) == []

# 2. Decompose price seasonality (weekly hay prices)
prices = np.array([182.0, 184.5, 187.0, 189.0, 185.5, 183.0, 186.5])
decomp = sq.commodity.seasonality(np.arange(7), prices, period=52)

# 3. Build a local forward curve
fwd = sq.commodity.localForwardCurve(
    spotPrice=187.50,
    tenor=np.array([0.0, 0.25, 0.50, 0.75, 1.0]),
    r=0.046,
    convYield=0.028,
    storageCost=0.020,
    basisAdjustment=-2.50,
)
curve = sq.schema.ForwardCurve(
    tenors=fwd['tenors'],
    prices=fwd['forwards'],
    baseDate='2026-03-14',
    market='alberta_hay_premium',
)

# 4. Price a commodity swap against the index curve
swap = sq.otc.commoditySwap(
    fixedPrice=190.0,
    indexCurve=curve['prices'],
    notional=1000.0,
    schedule=curve['tenors'],
    r=0.046,
)
print(f"Swap NPV: ${swap['npv']:,.2f}")

# 5. Calculate an IOSCO-aligned index
spec = sq.schema.IndexSpec(
    name='SIP-AHI-001',
    version='1.0',
    constituents=['premium_bale_14pct_moisture', 'feed_grade'],
    weightsMethod='volume',
    rollRule='monthly_last_business_day',
    effectiveDate='2026-01-01',
)
result = sq.index.calculateIndex([trade], spec, '2026-03-14')
audit  = sq.index.auditTrail(result, spec)
print(f"Index value: {result['indexValue']:.2f}  Checksum: {audit['checksum']}")
```

---

## Design Philosophy

- **Pure NumPy** — all mathematics implemented without pandas, scipy, or statsmodels
- **Vectorised operations** — performance-first for simulation-heavy workflows
- **Schema-validated inputs** — every function accepts validated dict objects from `sipQuant.schema`
- **Lightweight outputs** — all functions return plain dicts or NumPy arrays; convert to DataFrame as needed
- **Production-ready** — IOSCO-aligned audit trail, restatement procedures, and margin estimation built in

---

## Module Reference

### Core Commodity Stack

#### `schema` — Data Contract Layer

The foundation of sipQuant. Every pricing, risk, and index function accepts schema objects.

| Object | Purpose |
|---|---|
| `PriceSeries` | Regular price time series (broker quotes, exchange settlements) |
| `SparsePriceSeries` | Irregular physical trade observations (thin/weekly markets) |
| `TradeRecord` | Single physical trade (price, volume, grade, origin, destination) |
| `QuoteSheet` | OTC broker quote with bid/ask/mid and tenor |
| `ForwardCurve` | Forward curve for pricing and hedging |
| `OTCPosition` | Live OTC position for dealer book aggregation |
| `IndexSpec` | Immutable index methodology specification |
| `validate()` | Universal validation — returns list of error strings |

#### `commodity` — Physical Pricing Primitives

| Function | Use Case |
|---|---|
| `seasonality()` | STL-like decomposition: trend + seasonal + residual |
| `convenienceYield()` | Implied convenience yield from spot/futures pair |
| `basis()` | Local cash price minus benchmark reference |
| `gradeAdjustment()` | Quality-adjusted price from grade factor dict |
| `transportDifferential()` | Delivered price including logistics costs |
| `localForwardCurve()` | Forward curve from spot, carry, and convenience yield |
| `rollingRollCost()` | Roll cost estimated from forward curve shape |

#### `index` — IOSCO-Aligned Index Infrastructure

| Function | Use Case |
|---|---|
| `calculateIndex()` | VWAP-weighted index value from trade records |
| `auditTrail()` | IOSCO-aligned audit record with checksum |
| `restatement()` | Documented index correction procedure |
| `rollSchedule()` | Roll date generation (monthly/weekly/quarterly) |
| `proxyRegression()` | OLS or Huber regression for sparse-market proxy values |
| `backtestIndex()` | Historical index values, returns, volatility, drawdown |

#### `otc` — OTC Instrument Pricing

| Function | Use Case |
|---|---|
| `commoditySwap()` | Fixed-float commodity swap NPV and Greeks |
| `asianSwap()` | Arithmetic average price swap NPV |
| `collar()` | Long cap + short floor (buyer protection) |
| `physicalForward()` | PV of a physically-settled forward contract |
| `swaption()` | Black's formula swaption on forward swap rate |
| `asianOption()` | Monte Carlo Asian option with antithetic variates |

#### `book` — Dealer Book Management

| Function | Use Case |
|---|---|
| `netGreeks()` | Aggregate Greeks across all positions |
| `hedgeRatios()` | Delta-hedge units to flatten book delta |
| `pnlAttribution()` | Taylor expansion P&L decomposition |
| `scenarioShock()` | Pre-event scenario analysis (WASDE, weather, quota) |
| `bookSummary()` | Position summary by instrument type |
| `marginEstimate()` | Initial and variation margin estimation |

#### `liquidity` — Thin-Market Risk

| Function | Use Case |
|---|---|
| `liquidityAdjustedVar()` | LVAR following Bangia et al. |
| `marketImpact()` | Almgren-Chriss permanent + temporary impact |
| `optimalExecution()` | AC optimal liquidation schedule |
| `thinMarketScore()` | Liquidity score [0,1] for market quality assessment |
| `concentrationRisk()` | HHI position concentration |
| `optimalLiquidation()` | TWAP/VWAP cost estimation |

---

### Quantitative Toolkit

#### `sim` — Price Process Simulation

`gbm`, `ou`, `levyOu`, `ar1`, `arma`, `markovSwitching`, `arch`, `garch`, `heston`, `cir`, `vasicek`, `poisson`, `compoundPoisson`, `simulate`

#### `fit` — Model Calibration

`fitGbm`, `fitOu`, `fitLevyOU`, `fitAr1`, `fitArma`, `fitGarch`, `fitHeston`, `fitCir`, `fitVasicek`, `fitJumpDiffusion`, `fitCopula`, `fitDistributions`, `aic`, `bic`

#### `options` — Option Pricing

`blackScholes`, `binomial`, `trinomial`, `asian`, `binary`, `spread`, `barrier`, `simulate`, `impliedVol`, `buildForwardCurve`, `bootstrapCurve`

#### `econometrics` — Statistical Testing

`ols`, `whiteTest`, `breuschPaganTest`, `durbinWatson`, `ljungBox`, `adfTest`, `kpssTest`, `grangerCausality`

#### `bootstrap` — Curve & Surface Construction

`curve`, `surface`, `zeroRateCurve`, `forwardCurve`, `discountCurve`, `yieldCurve`, `volSurface`, `creditCurve`, `fxForwardCurve`, `inflationCurve`

---

### Portfolio & Risk

#### `portfolio` — Portfolio Optimisation

`blackLitterman`, `meanVariance`, `minVariance`, `riskParity`, `equalWeight`, `maxDiversification`, `tangency`, `maxSharpe`, `efficientFrontier`, `hierarchicalRiskParity`, `minCvar`

#### `risk` — Risk Metrics

`parametricVar`, `historicalVar`, `parametricCvar`, `historicalCvar`, `expectedShortfall`, `drawdown`, `maxDrawdownDuration`, `calmarRatio`, `sharpeRatio`, `sortinoRatio`, `omegaRatio`, `treynorRatio`, `informationRatio`, `modifiedVar`, `hillTailIndex`, `beta`, `downsideDeviation`, `ulcerIndex`, `painIndex`, `tailRatio`, `capturRatio`, `stabilityRatio`

#### `distributions` — Distribution Fitting

`fitNormal`, `fitLognormal`, `fitExponential`, `fitGamma`, `fitBeta`, `fitT`, `fitMixture`, `moments`, `ksTest`, `adTest`, `klDivergence`, `jsDivergence`, `quantile`, `qqPlot`

#### `dimension` — Dimensionality Reduction

`pca`, `lda`, `tsne`, `ica`, `nmf`, `kernelPca`, `mds`, `isomap`

#### `factor` — Factor Models

`famaFrench3`, `carhart4`, `apt`, `capm`, `estimateBeta`, `estimateFactorLoading`, `rollingBeta`, `pcaFactors`, `factorMimicking`, `jensenAlpha`, `treynorMazuy`, `multifactor`

#### `ml` — Machine Learning

`regressionTree`, `decisionTree`, `predictTree`, `isolationForest`, `anomalyScore`, `kmeans`, `knn`, `naiveBayes`, `randomForest`, `gradientBoosting`, `pca`, `lda`, `logisticRegression`

---

## Cluster Coverage

sipQuant is designed against the SIP 26-cluster commodity taxonomy. The module stack covers all 26 cluster types:

| Cluster Type | Primary Modules |
|---|---|
| A — Seasonal Agricultural Bulk | `sim.ou`, `fit.fitOu`, `commodity.seasonality`, `commodity.localForwardCurve` |
| B — Weather-Event Demand | `sim.compoundPoisson`, `sim.markovSwitching`, `options.barrier` |
| C — Specialty Food & Beverage | `commodity.gradeAdjustment`, `index.proxyRegression`, `otc.collar` |
| D — Industrial Biomaterials | `econometrics.ols`, `factor`, `sim.markovSwitching` |
| E — Circular Economy & By-Products | `commodity.basis`, `commodity.transportDifferential`, `otc.physicalForward` |
| F — Aquatic & Marine | `sim.ou`, `sim.compoundPoisson`, `options.barrier` |
| G — Functional Minerals | `factor`, `econometrics.ols`, `index.proxyRegression` |
| H — Animal Inputs & Feed Additives | `factor`, `econometrics.grangerCausality`, `sim.ou` |
| I — Carbon & Environmental Credits | `econometrics.ols`, `sim.markovSwitching`, `index.calculateIndex` |
| J — Water & Irrigation Inputs | `liquidity.thinMarketScore`, `index.proxyRegression` |
| K — Textile & Natural Fibre | `commodity.basis`, `fit.fitOu`, `econometrics.ols` |
| L — Emerging Protein Crops | `commodity.gradeAdjustment`, `index.calculateIndex`, `otc.collar` |
| M — Fermentation & Microbial Inputs | `commodity.gradeAdjustment`, `liquidity.thinMarketScore` |
| N — Exotic & Ceremonial | `index.proxyRegression`, `otc.asianOption` |
| O — Waste Heat & Energy By-Products | `factor`, `econometrics.ols`, `otc.commoditySwap` |
| P — Soil Inputs & Amendments | `commodity.seasonality`, `factor`, `index.calculateIndex` |
| Q — Animal Genetics & Biologics | `factor`, `econometrics.ols`, `index.calculateIndex` |
| R — Pharmaceutical Botanicals | `sim.markovSwitching`, `options.barrier`, `index.calculateIndex` |
| S — Construction & Natural Building | `commodity.basis`, `commodity.transportDifferential` |
| T — Non-Edible Horticultural | `sim.compoundPoisson`, `commodity.gradeAdjustment`, `otc.collar` |
| U — Reclaimed & Recovered Industrial | `commodity.basis`, `econometrics.ols`, `otc.physicalForward` |
| V — Traded Seeds & Propagation | `commodity.gradeAdjustment`, `index.calculateIndex` |
| W — Traditional & Indigenous Food | `index.proxyRegression`, `liquidity.thinMarketScore` |
| X — Logistics & Capacity Contracts | `options.barrier`, `otc.commoditySwap`, `bootstrap.curve` |
| Y — Prediction & Outcome Markets | `options.binary`, `sim.compoundPoisson` |
| Z — Artisanal & Small-Batch | `index.proxyRegression`, `econometrics.ols` |

---

## Converting to Pandas or Polars

All functions return NumPy arrays or dicts. Convert as needed:

```python
import pandas as pd
import polars as pl
from sipQuant import sim

paths = sim.gbm(mu=0.1, sigma=0.2, nSteps=252, nSims=100)
df_pandas = pd.DataFrame(paths.T, columns=[f'sim_{i}' for i in range(100)])
df_polars = pl.DataFrame(paths.T)
```

---

## Documentation

Full documentation: [sipquant.readthedocs.io](https://sipquant.readthedocs.io/en/latest/)

---

## License

This project is licensed under **GPL-3.0**. See [LICENSE](LICENSE) for details.

---

## Contact

For inquiries: [packages@sipglobally.com](mailto:packages@sipglobally.com)

Brayden Boyko — [brayden@sipglobally.com](mailto:brayden@sipglobally.com)
