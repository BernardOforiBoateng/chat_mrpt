#!/usr/bin/env python3
"""
TPR Data Cleaning Script
Cleans ward names in TPR data files by matching them to standard shapefile ward names
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
import warnings
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz, process
import re

warnings.filterwarnings('ignore')

class TPRDataCleaner:
    def __init__(self, shapefile_path, tpr_data_dir, output_dir):
        """Initialize the cleaner with paths"""
        self.shapefile_path = Path(shapefile_path)
        self.tpr_data_dir = Path(tpr_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Load shapefile
        print("Loading shapefile...")
        self.gdf = gpd.read_file(str(self.shapefile_path))
        
        # Create state-ward mapping
        self.state_ward_mapping = {}
        for state in self.gdf['StateName'].unique():
            if pd.notna(state):
                state_wards = self.gdf[self.gdf['StateName'] == state]['WardName'].dropna().unique()
                self.state_ward_mapping[state] = list(state_wards)
        
        print(f"Loaded {len(self.state_ward_mapping)} states with ward data")
        
        # State file mappings (19-37)
        self.state_files = {
            'Kaduna': 'kd_Kaduna_State_TPR_LLIN_2024.xlsx',
            'Kebbi': 'ke_Kebbi_State_TPR_LLIN_2024.xlsx',
            'Kano': 'kn_Kano_State_TPR_LLIN_2024.xlsx',
            'Kogi': 'ko_Kogi_State_TPR_LLIN_2024.xlsx',
            'Katsina': 'kt_Katsina_State_TPR_LLIN_2024.xlsx',
            'Kwara': 'kw_Kwara_State_TPR_LLIN_2024.xlsx',
            'Lagos': 'la_Lagos_State_TPR_LLIN_2024.xlsx',
            'Nasarawa': 'na_Nasarawa_State_TPR_LLIN_2024.xlsx',
            'Niger': 'ni_Niger_State_TPR_LLIN_2024.xlsx',
            'Ogun': 'og_Ogun_State_TPR_LLIN_2024.xlsx',
            'Ondo': 'on_Ondo_State_TPR_LLIN_2024.xlsx',
            'Osun': 'os_Osun_State_TPR_LLIN_2024.xlsx',
            'Oyo': 'oy_Oyo_State_TPR_LLIN_2024.xlsx',
            'Plateau': 'pl_Plateau_State_TPR_LLIN_2024.xlsx',
            'Rivers': 'ri_Rivers_State_TPR_LLIN_2024.xlsx',
            'Sokoto': 'so_Sokoto_State_TPR_LLIN_2024.xlsx',
            'Taraba': 'ta_Taraba_State_TPR_LLIN_2024.xlsx',
            'Yobe': 'yo_Yobe_State_TPR_LLIN_2024.xlsx',
            'Zamfara': 'za_Zamfara_State_TPR_LLIN_2024.xlsx'
        }
    
    def clean_ward_name(self, ward_name):
        """Basic cleaning of ward name"""
        if pd.isna(ward_name):
            return ""
        
        # Convert to string and strip
        ward = str(ward_name).strip()
        
        # Remove state prefixes (e.g., 'kd ', 'ke ', etc.)
        prefixes = ['ab ', 'ad ', 'ak ', 'an ', 'ba ', 'be ', 'bo ', 'by ', 'cr ', 'de ',
                   'eb ', 'ed ', 'ek ', 'en ', 'fc ', 'go ', 'im ', 'ji ', 'kd ', 'ke ',
                   'kn ', 'ko ', 'kt ', 'kw ', 'la ', 'na ', 'ni ', 'og ', 'on ', 'os ',
                   'oy ', 'pl ', 'ri ', 'so ', 'ta ', 'yo ', 'za ']
        
        for prefix in prefixes:
            if ward.lower().startswith(prefix):
                ward = ward[len(prefix):].strip()
                break
        
        # Remove 'Ward' suffix and LGA in parentheses
        ward = re.sub(r'\s*[Ww]ard\s*$', '', ward)
        ward = re.sub(r'\s*\([^)]+\)\s*$', '', ward)
        
        return ward.strip()
    
    def find_best_match(self, ward_name, candidate_wards, threshold=80):
        """Find best matching ward using fuzzy matching"""
        if not ward_name or not candidate_wards:
            return None, 0
        
        # Clean the input ward name
        cleaned_ward = self.clean_ward_name(ward_name)
        if not cleaned_ward:
            return None, 0
        
        # Prepare for matching
        cleaned_ward_upper = cleaned_ward.upper()
        
        # First try exact match (after cleaning)
        for candidate in candidate_wards:
            if candidate.upper() == cleaned_ward_upper:
                return candidate, 100
        
        # Try fuzzy matching
        best_match = process.extractOne(
            cleaned_ward,
            candidate_wards,
            scorer=fuzz.token_sort_ratio
        )
        
        if best_match and best_match[1] >= threshold:
            return best_match[0], best_match[1]
        
        # Try partial matching for compound names
        for candidate in candidate_wards:
            # Check if one is substring of the other
            if cleaned_ward_upper in candidate.upper() or candidate.upper() in cleaned_ward_upper:
                similarity = fuzz.partial_ratio(cleaned_ward, candidate)
                if similarity >= threshold:
                    return candidate, similarity
        
        # Try token-based matching
        best_match = process.extractOne(
            cleaned_ward,
            candidate_wards,
            scorer=fuzz.token_set_ratio
        )
        
        if best_match and best_match[1] >= threshold:
            return best_match[0], best_match[1]
        
        return None, 0
    
    def clean_state_data(self, state_name, file_name):
        """Clean TPR data for a specific state"""
        file_path = self.tpr_data_dir / file_name
        
        if not file_path.exists():
            print(f"  File not found: {file_path}")
            return None
        
        print(f"\nProcessing {state_name}...")
        
        try:
            # Read the Excel file
            df = pd.read_excel(file_path)
            print(f"  Loaded {len(df)} rows")
            
            # Get standard ward names for this state
            if state_name not in self.state_ward_mapping:
                print(f"  Warning: No shapefile data for {state_name}")
                return df
            
            standard_wards = self.state_ward_mapping[state_name]
            print(f"  Found {len(standard_wards)} standard wards for {state_name}")
            
            # Create mapping for this state's wards
            ward_mapping = {}
            unmatched = []
            
            unique_tpr_wards = df['WardName'].dropna().unique()
            print(f"  Processing {len(unique_tpr_wards)} unique ward names...")
            
            for tpr_ward in unique_tpr_wards:
                best_match, score = self.find_best_match(tpr_ward, standard_wards)
                
                if best_match:
                    ward_mapping[tpr_ward] = best_match
                    if score < 100:
                        print(f"    Matched: '{tpr_ward}' -> '{best_match}' (score: {score})")
                else:
                    unmatched.append(tpr_ward)
                    # Keep original if no match found
                    ward_mapping[tpr_ward] = self.clean_ward_name(tpr_ward)
            
            # Apply the mapping
            df['WardName_Original'] = df['WardName']
            df['WardName'] = df['WardName_Original'].map(lambda x: ward_mapping.get(x, x))
            df['Match_Status'] = df['WardName_Original'].map(
                lambda x: 'Matched' if x in ward_mapping and ward_mapping[x] in standard_wards else 'Unmatched'
            )
            
            # Summary statistics
            matched_count = len([w for w in ward_mapping.values() if w in standard_wards])
            print(f"  Results: {matched_count}/{len(unique_tpr_wards)} wards matched")
            
            if unmatched:
                print(f"  Unmatched wards ({len(unmatched)}):")
                for ward in unmatched[:10]:  # Show first 10
                    print(f"    - {ward}")
                if len(unmatched) > 10:
                    print(f"    ... and {len(unmatched) - 10} more")
            
            return df
            
        except Exception as e:
            print(f"  Error processing {file_name}: {str(e)}")
            return None
    
    def process_all_states(self):
        """Process all target states"""
        print("="*60)
        print("Starting TPR Data Cleaning Process")
        print("="*60)
        
        results = {}
        
        for state_name, file_name in self.state_files.items():
            cleaned_df = self.clean_state_data(state_name, file_name)
            
            if cleaned_df is not None:
                # Save the cleaned file
                output_filename = f"{state_name.lower()}_tpr_cleaned.csv"
                output_path = self.output_dir / output_filename
                
                # Save with original and cleaned ward names for verification
                cleaned_df.to_csv(output_path, index=False)
                print(f"  Saved: {output_path}")
                
                results[state_name] = {
                    'rows': len(cleaned_df),
                    'unique_wards': cleaned_df['WardName'].nunique(),
                    'matched': len(cleaned_df[cleaned_df['Match_Status'] == 'Matched']['WardName'].unique()) if 'Match_Status' in cleaned_df.columns else 0
                }
        
        # Print summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        for state, stats in results.items():
            print(f"{state}: {stats['rows']} rows, {stats['unique_wards']} unique wards, {stats['matched']} matched")
        
        return results


def main():
    """Main execution function"""
    # Set paths
    shapefile_path = "www/complete_names_wards/wards.shp"
    tpr_data_dir = "www/tpr_data_by_state"
    output_dir = "www"
    
    # Create cleaner and process
    cleaner = TPRDataCleaner(shapefile_path, tpr_data_dir, output_dir)
    results = cleaner.process_all_states()
    
    print("\nCleaning complete!")
    print(f"Cleaned files saved to: {output_dir}")


if __name__ == "__main__":
    main()