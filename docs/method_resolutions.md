# Urban Validation Method Resolutions

## Native Resolutions of Data Sources:
1. **NASA HLS (Control)**: 30m native resolution
2. **MODIS IGBP (Control)**: 500m native resolution  
3. **Sentinel-2 NDBI**: 10-20m native resolution (B8=10m, B11=20m)
4. **Africapolis**: 
   - Sentinel-2: 10-20m
   - WorldPop: 100m population grid
5. **GHSL**:
   - SMOD: 1000m (1km) resolution
   - Built-up: 10m-100m depending on product
6. **EBBI (Landsat 8)**: 30m native resolution (thermal=100m)

## Standardization:
All methods are being **resampled to 100m** for consistent comparison.

This is a good compromise because:
- Not too coarse (preserves urban detail)
- Not too fine (avoids artifacts from upsampling coarser data)
- Computationally efficient for 9,410 wards
- Matches WorldPop resolution (important for Africapolis method)

The script uses `.reproject({crs: 'EPSG:4326', scale: 100})` to ensure all layers are at the same resolution before stacking and analysis.