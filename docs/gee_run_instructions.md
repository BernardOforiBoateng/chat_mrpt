# Urban Validation GEE Execution Instructions

## Step 1: Open Google Earth Engine
1. Go to https://code.earthengine.google.com/
2. Sign in with your urbanmalaria account

## Step 2: Import Ward Boundaries
1. In the Assets tab, navigate to: `projects/epidemiological-intelligence/assets/NGA_wards_complete`
2. Click on it and select "Import"
3. Rename the import to `table` (this is crucial!)

## Step 3: Copy the Script
1. Create a new script in GEE
2. Copy the entire content of `gee_urban_validation_final_verified.js`
3. Paste it into the GEE code editor

## Step 4: Run the Script
1. Click the "Run" button
2. Wait for the script to process (may take 2-3 minutes)
3. Check the Console for progress messages:
   - "Processing CONTROL method..." 
   - "Processing NDBI..."
   - "Processing GHSL..."
   - "Processing Night Lights..."
   - "Successfully processed X methods"

## Step 5: Export Results
1. Go to the Tasks tab (top right)
2. You should see two export tasks:
   - `Urban_Validation_Final` (to Google Drive)
   - `Urban_Validation_Final_Bucket` (to Cloud Storage)
3. Click "RUN" on the Google Drive export (easier to access)
4. Confirm the export settings:
   - Folder: GEE_Urban_Validation
   - Format: CSV
5. Wait for export to complete (may take 5-10 minutes)

## Step 6: Download Results
1. Go to your Google Drive
2. Navigate to the `GEE_Urban_Validation` folder
3. Download the CSV file (named with today's date)

## What the Results Show
The CSV will contain for each ward:
- `control_urban`: MODIS urban percentage
- `ndbi_urban`: Sentinel-2 NDBI urban percentage  
- `ghsl_urban`: GHSL urban percentage
- `nightlights_urban`: Night lights urban percentage
- `mean_urban`: Average across all methods
- `consistently_rural`: "YES" if ALL methods show <30% urban
- `classification`: "Urban" / "Peri-urban" / "Rural"

## Key Validation Points
Wards marked `consistently_rural = YES` are definitively rural according to ALL satellite methods. These should NOT be selected for urban-targeted interventions.

If Delta State (or any state) selected these wards as urban for intervention, that would indicate a potential data issue or misclassification.