# TPR Module

Test Positivity Rate (TPR) analysis module for epidemiological data processing.

## Structure

- **core/** - TPR calculator, conversation manager, pipeline, state management
- **integration/** - LLM TPR handler, workflow routing, risk transition
- **output/** - Report and output generation
- **services/** - Facility filtering, raster extraction, shapefile processing
- **raster_database/** - Geospatial raster data organized by category
- **data/** - TPR dataset storage

## Purpose

Specialized module for analyzing Test Positivity Rate data, integrating geospatial rasters, generating risk maps, and producing epidemiological reports for malaria intervention targeting.
