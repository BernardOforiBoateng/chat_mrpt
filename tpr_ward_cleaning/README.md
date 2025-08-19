# TPR Ward Name Cleaning Script - User Guide

## Quick Start

### 1. Installation
First, install required packages:
```bash
pip install pandas geopandas fuzzywuzzy python-Levenshtein jellyfish openpyxl
```

### 2. File Setup
Ensure you have the following directory structure:
```
your_project/
├── comprehensive_tpr_ward_cleaning.py  (the script)
├── complete_names_wards/               (shapefile folder)
│   ├── wards.shp
│   ├── wards.dbf
│   ├── wards.prj
│   └── wards.shx
└── tpr_data_by_state/                  (TPR Excel files)
    ├── ab_Abia_State_TPR_LLIN_2024.xlsx
    ├── ad_Adamawa_State_TPR_LLIN_2024.xlsx
    └── ... (other state files)
```

### 3. Basic Usage

#### Clean ALL states:
```bash
python comprehensive_tpr_ward_cleaning.py
```

#### Clean states 1-18 only:
```bash
python comprehensive_tpr_ward_cleaning.py --states 1-18
```

#### Clean specific states by name:
```bash
python comprehensive_tpr_ward_cleaning.py --states Kaduna Lagos Kano
```

#### Clean specific states by number:
```bash
python comprehensive_tpr_ward_cleaning.py --states 1 5 10 15
```

### 4. Custom Directories
If your files are in different locations:
```bash
python comprehensive_tpr_ward_cleaning.py \
    --shapefile path/to/shapefile/folder \
    --tpr-dir path/to/tpr/files \
    --output-dir path/to/save/cleaned/files
```

## Output

The script will create:
1. **Cleaned CSV files**: One for each state (e.g., `kaduna_tpr_cleaned.csv`)
2. **Summary report**: `cleaning_summary.csv` with match statistics

Each cleaned file contains:
- `WardName_Original`: Original ward name from TPR file
- `WardName`: Standardized ward name matched to shapefile
- `Match_Status`: "Matched" or "Unmatched"
- All original TPR data columns preserved

## State Numbers Reference

| Number | State | Number | State |
|--------|-------|--------|-------|
| 1 | Abia | 20 | Kano |
| 2 | Adamawa | 21 | Katsina |
| 3 | Akwa Ibom | 22 | Kebbi |
| 4 | Anambra | 23 | Kogi |
| 5 | Bauchi | 24 | Kwara |
| 6 | Bayelsa | 25 | Lagos |
| 7 | Benue | 26 | Nasarawa |
| 8 | Borno | 27 | Niger |
| 9 | Cross River | 28 | Ogun |
| 10 | Delta | 29 | Ondo |
| 11 | Ebonyi | 30 | Osun |
| 12 | Edo | 31 | Oyo |
| 13 | Ekiti | 32 | Plateau |
| 14 | Enugu | 33 | Rivers |
| 15 | FCT | 34 | Sokoto |
| 16 | Gombe | 35 | Taraba |
| 17 | Imo | 36 | Yobe |
| 18 | Jigawa | 37 | Zamfara |
| 19 | Kaduna | | |

## Matching Techniques Used

The script uses multiple advanced techniques to achieve maximum accuracy:

1. **Fuzzy Matching** - Finds similar ward names using token-based comparison
2. **Abbreviation Inference** - Handles abbreviated names (e.g., "Phward" = "Port Harcourt Ward")
3. **Phonetic Matching** - Matches based on how words sound
4. **LGA Context** - Uses Local Government Area to disambiguate similar ward names

## Expected Match Rates

- **Excellent (>95%)**: Most states should achieve this
- **Good (90-95%)**: Acceptable for states with naming variations
- **Special Cases**: Rivers State may have lower rates due to unique abbreviation system

## Troubleshooting

### Error: "Shapefile not found"
- Ensure the `wards.shp` file is in the shapefile directory
- Check the path is correct

### Error: "jellyfish not installed"
- Run: `pip install jellyfish`
- Script will still work but phonetic matching will be skipped

### Low match rates
- Check if TPR file has correct column name (`WardName`)
- Verify state name matches between TPR and shapefile
- Some states (like Rivers) use abbreviations and may have lower match rates

## Support

For issues or questions about the cleaning process, contact the ChatMRPT development team.

## Example Output

After running the script, you'll see:
```
Processing Kaduna...
  Loaded 4890 rows
  Found 247 standard wards for Kaduna
  Processing 231 unique ward names...
  Results: 223/231 wards matched (96.5%)
  Saved: cleaned_tpr_data/kaduna_tpr_cleaned.csv

OVERALL STATISTICS
==================
States processed: 18
Total rows: 125,432
Total matched: 118,653
Total unmatched: 6,779
Overall match rate: 94.6%
```

The cleaned files are ready for use in ChatMRPT!