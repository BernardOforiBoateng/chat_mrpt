#!/usr/bin/env python3
"""Check distance calculation for Falgore."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.analysis.itn_pipeline import haversine_distance

# Falgore (KN1104) coordinates from unified
falgore_unified = (11.0392, 8.6433)

# Falgore options from population
falgore_doguwa = (11.1234, 8.5727)
falgore_rogo = (11.4952, 7.7053)

# Calculate distances
dist_doguwa = haversine_distance(falgore_unified[0], falgore_unified[1], 
                                  falgore_doguwa[0], falgore_doguwa[1])
dist_rogo = haversine_distance(falgore_unified[0], falgore_unified[1], 
                               falgore_rogo[0], falgore_rogo[1])

print(f"Falgore (KN1104) at {falgore_unified}")
print(f"Distance to Falgore in Doguwa: {dist_doguwa:.2f} km")
print(f"Distance to Falgore in Rogo: {dist_rogo:.2f} km")
print(f"\nThreshold is 5.0 km, so Doguwa match should fail (>{dist_doguwa:.1f} km)")
print(f"Rogo is too far: {dist_rogo:.1f} km")