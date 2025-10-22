# Analysis Module

This module contains the core malaria risk analysis pipelines and algorithms for ChatMRPT.

## Key Components

- **engine.py** - Main analysis orchestration engine
- **imputation.py** - Data imputation for missing values (KNN, mean, median strategies)
- **itn_pipeline.py** - Insecticide-Treated Net (ITN) distribution and intervention planning
- **pca_pipeline.py** - Principal Component Analysis for dimensionality reduction
- **scoring.py** - Composite risk scoring algorithms
- **normalization.py** - Data normalization utilities

## Purpose

Implements multi-stage analysis workflows including data preparation, variable selection, PCA analysis, composite scoring, and vulnerability ranking for malaria risk assessment.
