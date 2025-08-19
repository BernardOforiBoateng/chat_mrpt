#!/usr/bin/env python3
"""
Comprehensive TPR Ward Name Cleaning Script
============================================
Author: Bernard Boateng
Date: 2025
Version: 1.0

Description:
This script cleans and standardizes ward names in TPR (Test Positivity Rate) data files
by matching them against the official Nigerian ward shapefile. It uses multiple advanced
matching techniques to achieve maximum accuracy.

Requirements:
- Python 3.7+
- Required packages: pandas, geopandas, fuzzywuzzy, python-Levenshtein, jellyfish

Installation:
pip install pandas geopandas fuzzywuzzy python-Levenshtein jellyfish openpyxl

Usage:
1. Place your TPR Excel files in a directory (e.g., 'tpr_data_by_state/')
2. Ensure you have the ward shapefile in 'complete_names_wards/'
3. Run: python comprehensive_tpr_ward_cleaning.py
4. For specific states (1-18): python comprehensive_tpr_ward_cleaning.py --states 1-18
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
import warnings
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz, process
import re
import argparse
from collections import defaultdict
import sys

warnings.filterwarnings('ignore')

# Try importing optional packages
try:
    import jellyfish
    PHONETIC_AVAILABLE = True
except ImportError:
    PHONETIC_AVAILABLE = False
    print("Warning: jellyfish not installed. Phonetic matching will be skipped.")
    print("Install with: pip install jellyfish")


class ComprehensiveTPRCleaner:
    """
    Comprehensive ward name cleaning system for TPR data
    """
    
    # State file mappings for all 37 Nigerian states
    STATE_FILE_MAPPINGS = {
        # States 1-18
        'Abia': 'ab_Abia_State_TPR_LLIN_2024.xlsx',
        'Adamawa': 'ad_Adamawa_State_TPR_LLIN_2024.xlsx',
        'Akwa Ibom': 'ak_Akwa_Ibom_State_TPR_LLIN_2024.xlsx',
        'Anambra': 'an_Anambra_state_TPR_LLIN_2024.xlsx',
        'Bauchi': 'ba_Bauchi_State_TPR_LLIN_2024.xlsx',
        'Bayelsa': 'by_Bayelsa_State_TPR_LLIN_2024.xlsx',
        'Benue': 'be_Benue_State_TPR_LLIN_2024.xlsx',
        'Borno': 'bo_Borno_State_TPR_LLIN_2024.xlsx',
        'Cross River': 'cr_Cross_River_State_TPR_LLIN_2024.xlsx',
        'Delta': 'de_Delta_State_TPR_LLIN_2024.xlsx',
        'Ebonyi': 'eb_Ebonyi_State_TPR_LLIN_2024.xlsx',
        'Edo': 'ed_Edo_State_TPR_LLIN_2024.xlsx',
        'Ekiti': 'ek_Ekiti_State_TPR_LLIN_2024.xlsx',
        'Enugu': 'en_Enugu_State_TPR_LLIN_2024.xlsx',
        'Federal Capital Territory': 'fc_Federal_Capital_Territory_TPR_LLIN_2024.xlsx',
        'Gombe': 'go_Gombe_State_TPR_LLIN_2024.xlsx',
        'Imo': 'im_Imo_State_TPR_LLIN_2024.xlsx',
        'Jigawa': 'ji_Jigawa_State_TPR_LLIN_2024.xlsx',
        
        # States 19-37
        'Kaduna': 'kd_Kaduna_State_TPR_LLIN_2024.xlsx',
        'Kano': 'kn_Kano_State_TPR_LLIN_2024.xlsx',
        'Katsina': 'kt_Katsina_State_TPR_LLIN_2024.xlsx',
        'Kebbi': 'ke_Kebbi_State_TPR_LLIN_2024.xlsx',
        'Kogi': 'ko_Kogi_State_TPR_LLIN_2024.xlsx',
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
    
    # State number mapping
    STATE_NUMBERS = {
        1: 'Abia', 2: 'Adamawa', 3: 'Akwa Ibom', 4: 'Anambra', 5: 'Bauchi',
        6: 'Bayelsa', 7: 'Benue', 8: 'Borno', 9: 'Cross River', 10: 'Delta',
        11: 'Ebonyi', 12: 'Edo', 13: 'Ekiti', 14: 'Enugu', 15: 'Federal Capital Territory',
        16: 'Gombe', 17: 'Imo', 18: 'Jigawa', 19: 'Kaduna', 20: 'Kano',
        21: 'Katsina', 22: 'Kebbi', 23: 'Kogi', 24: 'Kwara', 25: 'Lagos',
        26: 'Nasarawa', 27: 'Niger', 28: 'Ogun', 29: 'Ondo', 30: 'Osun',
        31: 'Oyo', 32: 'Plateau', 33: 'Rivers', 34: 'Sokoto', 35: 'Taraba',
        36: 'Yobe', 37: 'Zamfara'
    }
    
    def __init__(self, shapefile_path, tpr_data_dir, output_dir):
        """
        Initialize the cleaner
        
        Args:
            shapefile_path: Path to the ward shapefile directory
            tpr_data_dir: Directory containing TPR Excel files
            output_dir: Directory to save cleaned files
        """
        self.shapefile_path = Path(shapefile_path)
        self.tpr_data_dir = Path(tpr_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Load shapefile
        print("Loading shapefile...")
        shapefile = self.shapefile_path / 'wards.shp'
        if not shapefile.exists():
            raise FileNotFoundError(f"Shapefile not found at {shapefile}")
        
        self.gdf = gpd.read_file(str(shapefile))
        
        # Create state-ward mapping
        self.state_ward_mapping = {}
        for state in self.gdf['StateName'].unique():
            if pd.notna(state):
                state_wards = self.gdf[self.gdf['StateName'] == state]['WardName'].dropna().unique()
                self.state_ward_mapping[state] = list(state_wards)
        
        print(f"Loaded {len(self.state_ward_mapping)} states with ward data")
        
        # Statistics tracking
        self.overall_stats = {
            'total_rows': 0,
            'total_matched': 0,
            'total_unmatched': 0,
            'states_processed': 0
        }
    
    def clean_ward_name_basic(self, ward_name):
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
    
    def technique_1_fuzzy_matching(self, ward_name, candidate_wards, threshold=75):
        """Fuzzy matching technique"""
        if not ward_name or not candidate_wards:
            return None, 0
        
        cleaned_ward = self.clean_ward_name_basic(ward_name)
        if not cleaned_ward:
            return None, 0
        
        # Try exact match first
        cleaned_upper = cleaned_ward.upper()
        for candidate in candidate_wards:
            if candidate.upper() == cleaned_upper:
                return candidate, 100
        
        # Fuzzy matching
        best_match = process.extractOne(
            cleaned_ward,
            candidate_wards,
            scorer=fuzz.token_sort_ratio
        )
        
        if best_match and best_match[1] >= threshold:
            return best_match[0], best_match[1]
        
        # Try token set ratio for compound names
        best_match = process.extractOne(
            cleaned_ward,
            candidate_wards,
            scorer=fuzz.token_set_ratio
        )
        
        if best_match and best_match[1] >= threshold:
            return best_match[0], best_match[1]
        
        return None, 0
    
    def technique_2_abbreviation_inference(self, ward_name, shapefile_wards):
        """
        Special technique for Rivers-style abbreviations
        Infers abbreviations like 'Phward' from 'Port Harcourt Ward'
        """
        cleaned = self.clean_ward_name_basic(ward_name)
        
        # Check if it has the pattern "Location Ward N"
        match = re.match(r'^(.+?)\s+Ward\s+(\d+)$', ward_name, re.IGNORECASE)
        if not match:
            return None, 0
        
        location = match.group(1).strip()
        number = match.group(2)
        
        # Clean location
        location = re.sub(r'^[a-z]{2}\s+', '', location)
        
        # Generate possible abbreviations
        abbreviations = []
        
        # Method 1: First letters of each word
        words = location.replace('-', ' ').replace('/', ' ').split()
        if words:
            abbrev1 = ''.join(w[0].lower() for w in words)
            abbreviations.append(abbrev1)
        
        # Method 2: First 2-3 letters
        clean_location = re.sub(r'[^a-z]', '', location.lower())
        if len(clean_location) >= 2:
            abbreviations.append(clean_location[:2])
            abbreviations.append(clean_location[:3])
        
        # Method 3: Key consonants
        consonants = ''.join(c for c in location.lower() if c not in 'aeiou' and c.isalpha())
        if len(consonants) >= 2:
            abbreviations.append(consonants[:3])
        
        # Try to find matching abbreviated ward
        for abbrev in abbreviations:
            for sf_ward in shapefile_wards:
                # Check if shapefile ward matches pattern
                sf_match = re.match(r'^([a-z]+)ward\s*(\d+)$', sf_ward.lower())
                if sf_match:
                    sf_abbrev = sf_match.group(1)
                    sf_number = sf_match.group(2)
                    
                    if abbrev.startswith(sf_abbrev[:2]) and number == sf_number:
                        return sf_ward, 90
        
        return None, 0
    
    def technique_3_phonetic_matching(self, ward_name, candidate_wards):
        """Phonetic matching using soundex and metaphone"""
        if not PHONETIC_AVAILABLE:
            return None, 0
        
        cleaned = self.clean_ward_name_basic(ward_name)
        if not cleaned:
            return None, 0
        
        try:
            ward_soundex = jellyfish.soundex(cleaned)
            ward_metaphone = jellyfish.metaphone(cleaned)
            
            best_match = None
            best_score = 0
            
            for candidate in candidate_wards:
                cand_soundex = jellyfish.soundex(candidate)
                cand_metaphone = jellyfish.metaphone(candidate)
                
                if ward_soundex == cand_soundex or ward_metaphone == cand_metaphone:
                    fuzz_score = fuzz.ratio(cleaned.lower(), candidate.lower())
                    if fuzz_score > best_score and fuzz_score >= 60:
                        best_score = fuzz_score
                        best_match = candidate
            
            if best_match:
                return best_match, best_score
        except:
            pass
        
        return None, 0
    
    def technique_4_lga_context(self, ward_name, ward_lga, state_gdf):
        """Use LGA context for matching"""
        if 'LGAName' not in state_gdf.columns or pd.isna(ward_lga):
            return None, 0
        
        # Clean LGA name
        clean_lga = re.sub(r'^[a-z]{2}\s+', '', str(ward_lga))
        clean_lga = clean_lga.replace(' Local Government Area', '').strip()
        
        # Find matching LGA in shapefile
        for sf_lga in state_gdf['LGAName'].unique():
            if fuzz.ratio(clean_lga.lower(), str(sf_lga).lower()) > 85:
                # Get wards in this LGA
                lga_wards = state_gdf[state_gdf['LGAName'] == sf_lga]['WardName'].unique()
                
                # Try to match within LGA
                best_match, score = self.technique_1_fuzzy_matching(ward_name, lga_wards, threshold=70)
                if best_match:
                    return best_match, score
        
        return None, 0
    
    def clean_state_data(self, state_name, file_name):
        """
        Clean TPR data for a specific state
        
        Args:
            state_name: Name of the state
            file_name: TPR file name
            
        Returns:
            Cleaned DataFrame or None if error
        """
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
            
            # Get state geodataframe for LGA context
            state_gdf = self.gdf[self.gdf['StateName'] == state_name]
            
            # Create mapping for this state's wards
            ward_mapping = {}
            unmatched = []
            
            unique_tpr_wards = df['WardName'].dropna().unique()
            print(f"  Processing {len(unique_tpr_wards)} unique ward names...")
            
            for tpr_ward in unique_tpr_wards:
                best_match = None
                best_score = 0
                technique_used = None
                
                # Try techniques in order of effectiveness
                
                # Technique 1: Fuzzy matching
                match, score = self.technique_1_fuzzy_matching(tpr_ward, standard_wards)
                if match and score > best_score:
                    best_match = match
                    best_score = score
                    technique_used = "fuzzy"
                
                # Technique 2: Abbreviation inference (for Rivers-style)
                if best_score < 100:
                    match, score = self.technique_2_abbreviation_inference(tpr_ward, standard_wards)
                    if match and score > best_score:
                        best_match = match
                        best_score = score
                        technique_used = "abbreviation"
                
                # Technique 3: Phonetic matching
                if best_score < 100 and PHONETIC_AVAILABLE:
                    match, score = self.technique_3_phonetic_matching(tpr_ward, standard_wards)
                    if match and score > best_score:
                        best_match = match
                        best_score = score
                        technique_used = "phonetic"
                
                # Technique 4: LGA context matching
                if best_score < 100 and 'LGA' in df.columns:
                    # Get LGA for this ward
                    ward_rows = df[df['WardName'] == tpr_ward]
                    if len(ward_rows) > 0:
                        ward_lga = ward_rows.iloc[0]['LGA']
                        match, score = self.technique_4_lga_context(tpr_ward, ward_lga, state_gdf)
                        if match and score > best_score:
                            best_match = match
                            best_score = score
                            technique_used = "lga_context"
                
                if best_match:
                    ward_mapping[tpr_ward] = best_match
                    if best_score < 100:
                        print(f"    Matched ({technique_used}): '{tpr_ward}' -> '{best_match}' (score: {best_score})")
                else:
                    unmatched.append(tpr_ward)
                    # Keep original if no match found
                    ward_mapping[tpr_ward] = self.clean_ward_name_basic(tpr_ward)
            
            # Apply the mapping
            df['WardName_Original'] = df['WardName']
            df['WardName'] = df['WardName_Original'].map(lambda x: ward_mapping.get(x, x))
            df['Match_Status'] = df['WardName_Original'].map(
                lambda x: 'Matched' if x in ward_mapping and ward_mapping[x] in standard_wards else 'Unmatched'
            )
            
            # Summary statistics
            matched_count = len([w for w in ward_mapping.values() if w in standard_wards])
            print(f"  Results: {matched_count}/{len(unique_tpr_wards)} wards matched ({matched_count/len(unique_tpr_wards)*100:.1f}%)")
            
            if unmatched:
                print(f"  Unmatched wards ({len(unmatched)}):")
                for ward in unmatched[:5]:  # Show first 5
                    print(f"    - {ward}")
                if len(unmatched) > 5:
                    print(f"    ... and {len(unmatched) - 5} more")
            
            # Update overall statistics
            self.overall_stats['total_rows'] += len(df)
            self.overall_stats['total_matched'] += len(df[df['Match_Status'] == 'Matched'])
            self.overall_stats['total_unmatched'] += len(df[df['Match_Status'] == 'Unmatched'])
            self.overall_stats['states_processed'] += 1
            
            return df
            
        except Exception as e:
            print(f"  Error processing {file_name}: {str(e)}")
            return None
    
    def process_states(self, state_list=None):
        """
        Process specified states or all states
        
        Args:
            state_list: List of state names or numbers to process (None for all)
        """
        print("="*60)
        print("TPR DATA CLEANING PROCESS")
        print("="*60)
        
        # Determine which states to process
        if state_list:
            # Convert state numbers to names if needed
            states_to_process = []
            for item in state_list:
                if isinstance(item, int):
                    if item in self.STATE_NUMBERS:
                        states_to_process.append(self.STATE_NUMBERS[item])
                else:
                    states_to_process.append(str(item))
        else:
            states_to_process = list(self.STATE_FILE_MAPPINGS.keys())
        
        print(f"Processing {len(states_to_process)} states...")
        
        results = {}
        
        for state_name in states_to_process:
            if state_name not in self.STATE_FILE_MAPPINGS:
                print(f"Warning: No file mapping for {state_name}")
                continue
            
            file_name = self.STATE_FILE_MAPPINGS[state_name]
            cleaned_df = self.clean_state_data(state_name, file_name)
            
            if cleaned_df is not None:
                # Save the cleaned file
                output_filename = f"{state_name.lower().replace(' ', '_')}_tpr_cleaned.csv"
                output_path = self.output_dir / output_filename
                
                cleaned_df.to_csv(output_path, index=False)
                print(f"  Saved: {output_path}")
                
                results[state_name] = {
                    'rows': len(cleaned_df),
                    'unique_wards': cleaned_df['WardName'].nunique(),
                    'matched': len(cleaned_df[cleaned_df['Match_Status'] == 'Matched']['WardName'].unique()) if 'Match_Status' in cleaned_df.columns else 0
                }
        
        # Print summary
        self.print_summary(results)
        
        return results
    
    def print_summary(self, results):
        """Print cleaning summary"""
        print("\n" + "="*60)
        print("CLEANING SUMMARY")
        print("="*60)
        
        for state, stats in results.items():
            print(f"{state}: {stats['rows']} rows, {stats['unique_wards']} unique wards, {stats['matched']} matched")
        
        print("\n" + "="*60)
        print("OVERALL STATISTICS")
        print("="*60)
        print(f"States processed: {self.overall_stats['states_processed']}")
        print(f"Total rows: {self.overall_stats['total_rows']:,}")
        print(f"Total matched: {self.overall_stats['total_matched']:,}")
        print(f"Total unmatched: {self.overall_stats['total_unmatched']:,}")
        
        if self.overall_stats['total_rows'] > 0:
            match_rate = (self.overall_stats['total_matched'] / self.overall_stats['total_rows']) * 100
            print(f"Overall match rate: {match_rate:.1f}%")
        
        # Save summary to CSV
        summary_df = pd.DataFrame([
            {
                'State': state,
                'Total_Rows': stats['rows'],
                'Unique_Wards': stats['unique_wards'],
                'Matched_Wards': stats['matched'],
                'Match_Rate_%': (stats['matched'] / stats['unique_wards'] * 100) if stats['unique_wards'] > 0 else 0
            }
            for state, stats in results.items()
        ])
        
        summary_path = self.output_dir / 'cleaning_summary.csv'
        summary_df.to_csv(summary_path, index=False)
        print(f"\nSummary saved to: {summary_path}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Clean TPR ward names by matching with shapefile')
    parser.add_argument('--shapefile', default='complete_names_wards',
                       help='Path to shapefile directory (default: complete_names_wards)')
    parser.add_argument('--tpr-dir', default='tpr_data_by_state',
                       help='Directory containing TPR Excel files (default: tpr_data_by_state)')
    parser.add_argument('--output-dir', default='cleaned_tpr_data',
                       help='Output directory for cleaned files (default: cleaned_tpr_data)')
    parser.add_argument('--states', nargs='+',
                       help='States to process (names or numbers, e.g., "1-18" or "Kaduna Lagos")')
    
    args = parser.parse_args()
    
    # Parse state range if provided
    states_to_process = None
    if args.states:
        states_to_process = []
        for item in args.states:
            if '-' in item:
                # Handle range like "1-18"
                try:
                    start, end = item.split('-')
                    states_to_process.extend(range(int(start), int(end) + 1))
                except:
                    states_to_process.append(item)
            elif item.isdigit():
                states_to_process.append(int(item))
            else:
                states_to_process.append(item)
    
    # Create cleaner and process
    try:
        cleaner = ComprehensiveTPRCleaner(
            shapefile_path=args.shapefile,
            tpr_data_dir=args.tpr_dir,
            output_dir=args.output_dir
        )
        
        results = cleaner.process_states(states_to_process)
        
        print("\n✅ Cleaning complete!")
        print(f"Cleaned files saved to: {args.output_dir}/")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\nPlease ensure:")
        print("1. Shapefile is in 'complete_names_wards/' directory")
        print("2. TPR Excel files are in 'tpr_data_by_state/' directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()