ml — Machine Learning
======================

.. module:: sipQuant.ml

Machine learning tools for commodity market analysis. Key applications:

- **Isolation Forest** — outlier detection in thin market trade data (critical for index integrity)
- **Random Forest** — grade surface regression with non-linear interactions
- **K-means** — market segmentation within clusters
- **Gradient Boosting** — price prediction for proxy construction

Key Functions
-------------

``isolationForest(X, nTrees=100, contamination=0.05, seed=None)``
    Isolation forest for anomaly detection. Returns ``{scores, isAnomaly, threshold}``.
    **Primary use**: flag potentially non-arm's-length trades before index calculation.
    Low anomaly scores (negative) indicate potential price manipulation.

``anomalyScore(forest, X)``
    Score new observations against a trained isolation forest.

``regressionTree(X, y, maxDepth=5, minSamplesSplit=2)`` / ``decisionTree(...)``
    Decision tree for regression or classification.

``predictTree(tree, X)``
    Predict using a trained tree model.

``randomForest(X, y, nTrees=100, maxDepth=5, seed=None)``
    Random forest regressor. Returns ``{predictions, featureImportances}``.
    Use for grade surface regression when moisture, protein, test weight, and
    dockage interact non-linearly.

``gradientBoosting(X, y, nEstimators=100, learningRate=0.1, maxDepth=3, seed=None)``
    Gradient boosting regressor.

``kmeans(X, nClusters=3, nInit=10, maxIter=300, seed=None)``
    K-means clustering. Returns ``{labels, centers, inertia}``.
    Use to segment markets within a cluster by price level and volatility regime.

``knn(X, y, nNeighbors=5)``
    K-nearest neighbours regressor/classifier.

``naiveBayes(X, y)``
    Gaussian naive Bayes classifier.

``logisticRegression(X, y, maxIter=1000, tol=1e-4)``
    Binary logistic regression classifier. Use for regime classification.

``pca(X, nComponents=None)``
    PCA (same as ``dimension.pca`` — included here for pipeline convenience).

``lda(X, y, nComponents=None)``
    LDA classifier.

.. code-block:: python

   import sipQuant as sq
   import numpy as np

   # --- Outlier detection for index integrity ---
   # Trade prices: one potentially non-arm's-length outlier at index 7
   trade_features = np.array([
       [187.5, 500.0],  # price, volume
       [185.0, 300.0],
       [189.0, 250.0],
       [186.5, 400.0],
       [188.0, 350.0],
       [187.0, 320.0],
       [188.5, 280.0],
       [215.0, 50.0],   # suspicious: high price, low volume
       [186.0, 360.0],
       [187.8, 310.0],
   ])

   forest = sq.ml.isolationForest(
       trade_features,
       nTrees=100,
       contamination=0.10,  # expect ~10% anomalies in this thin market
       seed=42,
   )

   for i, (score, flag) in enumerate(zip(forest['scores'], forest['isAnomaly'])):
       status = 'ANOMALY - REVIEW' if flag else 'clean'
       print(f"Trade {i}: score={score:.3f}  {status}")

   # --- Grade surface regression ---
   # Features: moisture %, test_weight, dockage %, protein %
   grade_features = np.random.normal([14.0, 42.0, 1.5, 12.0], [1.0, 2.0, 0.5, 1.0], (200, 4))
   prices         = 185.0 + 3*(14 - grade_features[:,0]) + 0.5*grade_features[:,1] \
                          - 2*grade_features[:,2] + 0.8*grade_features[:,3]

   rf_model = sq.ml.randomForest(grade_features, prices, nTrees=200, maxDepth=6, seed=42)
   print(f"Feature importances: {rf_model['featureImportances'].round(3)}")
   # Expected: moisture and dockage dominate

   # --- Market segmentation ---
   # Segment markets by weekly avg price and avg volume
   market_stats = np.random.normal([185, 300], [15, 100], (50, 2))
   km = sq.ml.kmeans(market_stats, nClusters=3, seed=42)
   print(f"Market cluster labels: {km['labels']}")
   print(f"Cluster centers:\n{km['centers'].round(1)}")
