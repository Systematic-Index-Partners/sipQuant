dimension — Dimensionality Reduction
======================================

.. module:: sipQuant.dimension

Dimensionality reduction for multi-market analysis and feature extraction.
Primary use: identifying common price drivers across cluster markets, and
compressing grade factor spaces before regression.

Key Functions
-------------

``pca(X, nComponents=None)``
    Principal Component Analysis. Returns ``{components, explainedVariance, scores, loadings}``.
    PC1 typically captures the common commodity price factor across a cluster.
    PC2/PC3 often isolate regional or grade effects.

``kernelPca(X, nComponents=2, kernel='rbf', gamma=None)``
    Kernel PCA for non-linear structure (``'rbf'``, ``'poly'``, ``'linear'``).

``lda(X, y, nComponents=None)``
    Linear Discriminant Analysis for supervised grade classification.

``tsne(X, nComponents=2, perplexity=30.0, nIter=1000)``
    t-SNE for visualising high-dimensional market data.

``ica(X, nComponents=None)``
    Independent Component Analysis — separates independent supply/demand signals
    from observed correlated price series.

``nmf(X, nComponents=2)``
    Non-negative Matrix Factorisation for non-negative data (prices, volumes).

``mds(X, nComponents=2)``
    Multidimensional Scaling for distance-preserving projection.

``isomap(X, nComponents=2, nNeighbors=5)``
    Isomap for manifold-preserving dimensionality reduction.

.. code-block:: python

   import sipQuant as sq
   import numpy as np

   # 52 weeks × 8 markets (different locations/grades within a cluster)
   prices_matrix = np.random.normal(185, 10, (52, 8))

   # PCA to identify common price driver (PC1) and regional spread (PC2)
   pca_result = sq.dimension.pca(prices_matrix, nComponents=3)
   print(f"Explained variance: {pca_result['explainedVariance'].round(4)}")
   # PC1 explained variance > 0.70 → strong common factor → good index candidate

   # ICA to separate independent supply shock vs demand shock
   ica_result = sq.dimension.ica(prices_matrix, nComponents=2)

   # LDA to classify price observations into grade tiers
   grade_labels = np.array([0, 1, 2, 0, 1, 2, 0, 1] * 6 + [0, 1, 2, 0])[:52]
   lda_result = sq.dimension.lda(prices_matrix, grade_labels, nComponents=2)
