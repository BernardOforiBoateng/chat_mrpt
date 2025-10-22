#!/usr/bin/env python3
"""
Special fix for Rivers State ward mapping
Creates a mapping table based on pattern analysis
"""

import pandas as pd
import geopandas as gpd
from fuzzywuzzy import fuzz, process
import re

def create_rivers_mapping():
    """Create mapping table for Rivers state wards"""
    
    print("CREATING RIVERS STATE WARD MAPPING")
    print("="*60)
    
    # Load data
    rivers_df = pd.read_csv('www/cleaned_tpr_data/rivers_tpr_cleaned.csv')
    gdf = gpd.read_file('www/complete_names_wards/wards.shp')
    
    # Get unique TPR wards
    tpr_wards = rivers_df['WardName_Original'].dropna().unique()
    
    # Get Rivers shapefile wards
    shapefile_wards = gdf[gdf['StateName'] == 'Rivers']['WardName'].dropna().unique()
    
    # Analyze LGA names in both datasets
    if 'LGA' in rivers_df.columns:
        tpr_lgas = rivers_df['LGA'].dropna().unique()
        print(f"TPR LGAs found: {len(tpr_lgas)}")
        
        # Clean LGA names (remove 'ri ' prefix and 'Local Government Area' suffix)
        cleaned_lgas = []
        for lga in tpr_lgas:
            cleaned = lga.replace('ri ', '').replace(' Local Government Area', '').strip()
            cleaned_lgas.append(cleaned)
        
        print("\nTPR LGAs (cleaned):")
        for lga in sorted(set(cleaned_lgas)):
            print(f"  - {lga}")
    
    # Analyze shapefile ward patterns
    print("\n\nSHAPEFILE WARD PATTERNS:")
    print("-"*40)
    
    # Group shapefile wards by prefix
    prefix_mapping = {}
    for ward in shapefile_wards:
        if 'ward' in ward.lower() and any(c.isdigit() for c in ward):
            # Extract prefix
            match = re.match(r'^([A-Za-z]+)ward\s*(\d+)', ward, re.IGNORECASE)
            if match:
                prefix = match.group(1).lower()
                number = match.group(2)
                if prefix not in prefix_mapping:
                    prefix_mapping[prefix] = []
                prefix_mapping[prefix].append(int(number))
    
    # Sort and show prefix patterns
    print("\nDetected prefixes and their ward count:")
    for prefix, numbers in sorted(prefix_mapping.items()):
        max_num = max(numbers) if numbers else 0
        print(f"  {prefix}ward: {len(numbers)} wards (1-{max_num})")
    
    # Create intelligent mapping based on LGA names and patterns
    print("\n\nCREATING INTELLIGENT MAPPING:")
    print("-"*40)
    
    # Mapping dictionary
    mapping = {}
    
    # Known LGA abbreviations (based on pattern analysis)
    lga_abbreviations = {
        'Abua/Odual': 'abo',
        'Ahoada East': 'ahe',
        'Ahoada West': 'ahw',
        'Akuku-Toru': 'akt',
        'Andoni': 'and',
        'Asari-Toru': 'ast',
        'Bonny': 'bo',
        'Degema': 'de',
        'Eleme': 'ele',
        'Emuoha': 'em',
        'Etche': 'etc',
        'Gokana': 'go',
        'Ikwerre': 'ik',
        'Khana': 'kha',
        'Obio/Akpor': 'obi',
        'Ogu/Bolo': 'ogb',
        'Okrika': 'okr',
        'Omuma': 'omu',
        'Opobo/Nkoro': 'opn',
        'Oyigbo': 'oyi',
        'Port Harcourt': 'ph',
        'Port-Hartcourt': 'ph',
        'Tai': 'tai'
    }
    
    # Process each TPR ward
    for tpr_ward in tpr_wards:
        cleaned = tpr_ward.replace('ri ', '').strip()
        
        if ' Ward ' in cleaned:
            parts = cleaned.split(' Ward ')
            location = parts[0].strip()
            number = parts[1].strip() if len(parts) > 1 else ''
            
            # Check if location matches known LGA
            matched = False
            for lga_name, abbrev in lga_abbreviations.items():
                if lga_name.lower() == location.lower():
                    # Find corresponding shapefile ward
                    potential_match = f"{abbrev}ward {number}"
                    
                    # Look for exact or close match in shapefile
                    for sf_ward in shapefile_wards:
                        if potential_match.lower() == sf_ward.lower():
                            mapping[tpr_ward] = sf_ward
                            matched = True
                            print(f"✓ Mapped: '{tpr_ward}' -> '{sf_ward}'")
                            break
                        elif abbrev in sf_ward.lower() and number in sf_ward:
                            mapping[tpr_ward] = sf_ward
                            matched = True
                            print(f"✓ Mapped: '{tpr_ward}' -> '{sf_ward}'")
                            break
                    
                    if matched:
                        break
            
            # If no match found, try fuzzy matching on the location name
            if not matched and location:
                # Try to find wards with similar prefixes
                location_short = location[:3].lower()
                candidates = [w for w in shapefile_wards if w.lower().startswith(location_short) and number in w]
                
                if candidates:
                    mapping[tpr_ward] = candidates[0]
                    print(f"~ Fuzzy mapped: '{tpr_ward}' -> '{candidates[0]}'")
    
    print(f"\n\nMAPPING RESULTS:")
    print(f"Total TPR wards: {len(tpr_wards)}")
    print(f"Successfully mapped: {len(mapping)} ({len(mapping)/len(tpr_wards)*100:.1f}%)")
    
    # Save mapping to CSV
    mapping_df = pd.DataFrame(list(mapping.items()), columns=['TPR_Ward', 'Shapefile_Ward'])
    mapping_df.to_csv('www/rivers_ward_mapping.csv', index=False)
    print(f"\nMapping saved to: www/rivers_ward_mapping.csv")
    
    # Apply mapping to Rivers data
    print("\nAPPLYING MAPPING TO RIVERS DATA...")
    
    # Create new cleaned file with better matching
    rivers_df_new = rivers_df.copy()
    
    # Apply mapping
    rivers_df_new['WardName_Mapped'] = rivers_df_new['WardName_Original'].map(mapping)
    
    # Use mapped name where available, otherwise keep cleaned name
    rivers_df_new['WardName'] = rivers_df_new['WardName_Mapped'].fillna(rivers_df_new['WardName'])
    
    # Update match status
    shapefile_ward_set = set(shapefile_wards)
    rivers_df_new['Match_Status'] = rivers_df_new['WardName'].apply(
        lambda x: 'Matched' if x in shapefile_ward_set else 'Unmatched'
    )
    
    # Save improved Rivers file
    rivers_df_new.to_csv('www/cleaned_tpr_data/rivers_tpr_cleaned_improved.csv', index=False)
    
    # Calculate improvement
    original_matched = len(rivers_df[rivers_df['Match_Status'] == 'Matched']) if 'Match_Status' in rivers_df.columns else 0
    new_matched = len(rivers_df_new[rivers_df_new['Match_Status'] == 'Matched'])
    
    print(f"\nIMPROVEMENT STATISTICS:")
    print(f"Original matched: {original_matched}/{len(rivers_df)} ({original_matched/len(rivers_df)*100:.1f}%)")
    print(f"New matched: {new_matched}/{len(rivers_df_new)} ({new_matched/len(rivers_df_new)*100:.1f}%)")
    
    improvement = new_matched - original_matched
    if improvement > 0:
        print(f"✓ Improved by {improvement} matches ({improvement/len(rivers_df)*100:.1f}% improvement)")
    
    return mapping


if __name__ == "__main__":
    mapping = create_rivers_mapping()