#!/bin/bash

echo "State-by-state unmatched ward analysis:"
echo "========================================"

for file in www/all_states_cleaned/*_tpr_cleaned.csv; do
    state=$(basename "$file" | sed 's/_tpr_cleaned.csv//')
    unmatched=$(grep -c "Unmatched" "$file" 2>/dev/null || echo 0)
    total=$(wc -l < "$file")
    # Subtract 1 for header
    total=$((total - 1))
    matched=$((total - unmatched))
    rate=$(echo "scale=2; $matched * 100 / $total" | bc)
    printf "%-30s | Unmatched: %5d | Total: %5d | Rate: %6.2f%%\n" "$state" "$unmatched" "$total" "$rate"
done | sort -t'|' -k2 -rn