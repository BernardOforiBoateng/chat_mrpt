#!/bin/bash
# Download urban validation results from Cloud Storage bucket

BUCKET="urban-validation-nigeria"
echo "Downloading urban validation results from gs://${BUCKET}/"

# Create local directory for results
mkdir -p urban_validation_results

# Download the ward-level comparison
echo "Downloading ward comparison data..."
gsutil cp gs://${BUCKET}/ward_comparison/urban_validation_all_methods.csv urban_validation_results/

# Download the correlation points
echo "Downloading correlation analysis data..."
gsutil cp gs://${BUCKET}/correlation_analysis/methods_correlation_points.csv urban_validation_results/

echo ""
echo "Files downloaded to urban_validation_results/"
echo ""
echo "Now run: python analyze_urban_validation_results.py"