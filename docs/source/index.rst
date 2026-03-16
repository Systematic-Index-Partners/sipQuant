sipQuant Documentation
======================

**Quantitative library for physically-settled commodity markets.**

sipQuant is the internal quantitative infrastructure of SIP Global (Systematic Index Partners).
It provides a complete stack for building, maintaining, and trading against physically-settled
commodity price indices in thin, opaque markets — from raw trade data to IOSCO-aligned indices
to OTC structured products and dealer book management.

Pure NumPy. No external dependencies beyond NumPy 1.23+.

.. code-block:: bash

   pip install sipQuant

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   getting_started

.. toctree::
   :maxdepth: 2
   :caption: Core Commodity Stack

   schema
   commodity
   index_module
   otc
   book
   liquidity

.. toctree::
   :maxdepth: 2
   :caption: Quantitative Toolkit

   sim
   fit
   options
   econometrics
   bootstrap

.. toctree::
   :maxdepth: 2
   :caption: Portfolio & Risk

   portfolio
   risk
   distributions
   dimension
   factor
   ml

.. toctree::
   :maxdepth: 2
   :caption: Reference

   cluster_taxonomy

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
