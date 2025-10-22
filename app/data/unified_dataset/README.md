# Unified Dataset Module

Modular unified dataset construction system (refactored from monolithic builder).

## Key Components

- **loading.py** - CSV/shapefile/model/PCA source loading with dynamic fallback
- **integration.py** - Analysis integration and data merging logic
- **metadata.py** - Region metadata handling and reconstruction
- **merge.py** - Ward duplicate detection and merge utilities

## Purpose

Combines demographic data, shapefiles, raster extractions, and PCA components into a unified dataset for analysis. Reduced from 2,167 lines to 704 lines while maintaining functionality.
