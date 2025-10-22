#!/usr/bin/env python3
"""
Advanced Ward Matching Techniques
Extracting every last match using sophisticated methods
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
import re
from fuzzywuzzy import fuzz, process
from difflib import SequenceMatcher
import numpy as np
from collections import defaultdict
import warnings

warnings.filterwarnings('ignore')

class AdvancedWardMatcher:
    def __init__(self):
        """Initialize advanced matcher with multiple techniques"""
        self.gdf = gpd.read_file('www/complete_names_wards/wards.shp')
        self.final_dir = Path('www/final_cleaned_tpr_data')
        self.techniques_used = defaultdict(list)
        
    def technique_1_lga_context_matching(self, state_name, df):
        """Use LGA context to disambiguate ward names"""
        print("\n🔧 Technique 1: LGA Context Matching")
        
        mappings = {}
        state_gdf = self.gdf[self.gdf['StateName'] == state_name]
        
        if 'LGA' not in df.columns or 'LGAName' not in state_gdf.columns:
            print("  ⚠ LGA data not available")
            return mappings
        
        unmatched = df[df['Match_Status'] == 'Unmatched']['WardName_Original'].unique()
        
        for ward in unmatched:
            # Get the LGA for this ward from TPR data
            ward_rows = df[df['WardName_Original'] == ward]
            if len(ward_rows) > 0:
                tpr_lga = ward_rows.iloc[0]['LGA']
                
                # Clean LGA name
                clean_lga = re.sub(r'^[a-z]{2}\s+', '', str(tpr_lga))
                clean_lga = clean_lga.replace(' Local Government Area', '').strip()
                
                # Find similar LGA in shapefile
                for sf_lga in state_gdf['LGAName'].unique():
                    if fuzz.ratio(clean_lga.lower(), str(sf_lga).lower()) > 85:
                        # Get wards in this LGA
                        lga_wards = state_gdf[state_gdf['LGAName'] == sf_lga]['WardName'].unique()
                        
                        # Clean ward name
                        clean_ward = re.sub(r'^[a-z]{2}\s+', '', ward)
                        clean_ward = clean_ward.replace(' Ward', '').strip()
                        if '(' in clean_ward:
                            clean_ward = clean_ward[:clean_ward.find('(')].strip()
                        
                        # Find best match within this LGA
                        if len(lga_wards) > 0:
                            best = process.extractOne(clean_ward, lga_wards, scorer=fuzz.token_sort_ratio)
                            if best and best[1] >= 70:
                                mappings[ward] = best[0]
                                self.techniques_used['lga_context'].append(ward)
                                print(f"  ✓ LGA match: '{ward}' -> '{best[0]}' (LGA: {sf_lga})")
                                break
        
        return mappings
    
    def technique_2_phonetic_matching(self, state_name, df):
        """Use phonetic similarity for matching"""
        print("\n🔧 Technique 2: Phonetic Matching")
        
        import jellyfish  # For phonetic algorithms
        
        mappings = {}
        state_wards = self.gdf[self.gdf['StateName'] == state_name]['WardName'].unique()
        unmatched = df[df['Match_Status'] == 'Unmatched']['WardName_Original'].unique()
        
        for ward in unmatched:
            if ward in mappings:
                continue
                
            # Clean ward name
            clean_ward = re.sub(r'^[a-z]{2}\s+', '', ward)
            clean_ward = clean_ward.replace(' Ward', '').replace('(', '').replace(')', '').strip()
            
            # Generate phonetic codes
            try:
                ward_soundex = jellyfish.soundex(clean_ward)
                ward_metaphone = jellyfish.metaphone(clean_ward)
                
                best_match = None
                best_score = 0
                
                for sf_ward in state_wards:
                    sf_soundex = jellyfish.soundex(sf_ward)
                    sf_metaphone = jellyfish.metaphone(sf_ward)
                    
                    # Check phonetic similarity
                    if ward_soundex == sf_soundex or ward_metaphone == sf_metaphone:
                        # Verify with fuzzy match
                        fuzz_score = fuzz.ratio(clean_ward.lower(), sf_ward.lower())
                        if fuzz_score > best_score and fuzz_score >= 60:
                            best_score = fuzz_score
                            best_match = sf_ward
                
                if best_match:
                    mappings[ward] = best_match
                    self.techniques_used['phonetic'].append(ward)
                    print(f"  ✓ Phonetic: '{ward}' -> '{best_match}' (score: {best_score})")
            except:
                pass
        
        return mappings
    
    def technique_3_word_reordering(self, state_name, df):
        """Match wards with reordered words"""
        print("\n🔧 Technique 3: Word Reordering")
        
        mappings = {}
        state_wards = self.gdf[self.gdf['StateName'] == state_name]['WardName'].unique()
        unmatched = df[df['Match_Status'] == 'Unmatched']['WardName_Original'].unique()
        
        for ward in unmatched:
            if ward in mappings:
                continue
                
            # Clean and split into words
            clean_ward = re.sub(r'^[a-z]{2}\s+', '', ward)
            clean_ward = clean_ward.replace(' Ward', '').replace('/', ' ').strip()
            ward_words = set(clean_ward.lower().split())
            
            if len(ward_words) > 1:
                for sf_ward in state_wards:
                    sf_words = set(sf_ward.lower().replace('/', ' ').split())
                    
                    # Check if same words, different order
                    if ward_words == sf_words:
                        mappings[ward] = sf_ward
                        self.techniques_used['reordering'].append(ward)
                        print(f"  ✓ Reordered: '{ward}' -> '{sf_ward}'")
                        break
                    
                    # Check if most words match
                    common = ward_words.intersection(sf_words)
                    if len(common) >= min(len(ward_words), len(sf_words)) - 1 and len(common) >= 2:
                        mappings[ward] = sf_ward
                        self.techniques_used['reordering'].append(ward)
                        print(f"  ✓ Partial reorder: '{ward}' -> '{sf_ward}'")
                        break
        
        return mappings
    
    def technique_4_abbreviation_expansion(self, state_name, df):
        """Expand common abbreviations"""
        print("\n🔧 Technique 4: Abbreviation Expansion")
        
        # Common abbreviations in Nigerian ward names
        abbreviations = {
            'st': 'saint',
            's/': 'sabon',
            'n/': 'new',
            't/': 'tungan',
            'u/': 'unguwan',
            'ung': 'unguwan',
            'tud': 'tudun',
            's/g': 'sabon gari',
            'g/': 'gidan',
            'k/': 'kasuwan',
            'r/': 'ruwan',
            'd/': 'dan'
        }
        
        mappings = {}
        state_wards = self.gdf[self.gdf['StateName'] == state_name]['WardName'].unique()
        unmatched = df[df['Match_Status'] == 'Unmatched']['WardName_Original'].unique()
        
        for ward in unmatched:
            if ward in mappings:
                continue
                
            # Clean and expand abbreviations
            clean_ward = re.sub(r'^[a-z]{2}\s+', '', ward.lower())
            clean_ward = clean_ward.replace(' ward', '').strip()
            
            expanded = clean_ward
            for abbr, full in abbreviations.items():
                expanded = expanded.replace(abbr, full)
            
            if expanded != clean_ward:
                # Try to match expanded version
                best = process.extractOne(expanded, state_wards, scorer=fuzz.token_sort_ratio)
                if best and best[1] >= 75:
                    mappings[ward] = best[0]
                    self.techniques_used['abbreviation'].append(ward)
                    print(f"  ✓ Expanded: '{ward}' -> '{best[0]}' (via '{expanded}')")
        
        return mappings
    
    def technique_5_special_character_normalization(self, state_name, df):
        """Normalize special characters and punctuation"""
        print("\n🔧 Technique 5: Special Character Normalization")
        
        mappings = {}
        state_wards = self.gdf[self.gdf['StateName'] == state_name]['WardName'].unique()
        unmatched = df[df['Match_Status'] == 'Unmatched']['WardName_Original'].unique()
        
        # Create normalized versions of shapefile wards
        normalized_map = {}
        for sf_ward in state_wards:
            # Normalize: remove special chars, standardize spaces
            normalized = re.sub(r'[^\w\s]', '', sf_ward.lower())
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            normalized_map[normalized] = sf_ward
        
        for ward in unmatched:
            if ward in mappings:
                continue
                
            # Normalize TPR ward
            clean_ward = re.sub(r'^[a-z]{2}\s+', '', ward.lower())
            clean_ward = clean_ward.replace(' ward', '').strip()
            normalized_ward = re.sub(r'[^\w\s]', '', clean_ward)
            normalized_ward = re.sub(r'\s+', ' ', normalized_ward).strip()
            
            # Check for exact match after normalization
            if normalized_ward in normalized_map:
                mappings[ward] = normalized_map[normalized_ward]
                self.techniques_used['normalization'].append(ward)
                print(f"  ✓ Normalized: '{ward}' -> '{normalized_map[normalized_ward]}'")
        
        return mappings
    
    def technique_6_substring_matching(self, state_name, df):
        """Match based on significant substrings"""
        print("\n🔧 Technique 6: Substring Matching")
        
        mappings = {}
        state_wards = self.gdf[self.gdf['StateName'] == state_name]['WardName'].unique()
        unmatched = df[df['Match_Status'] == 'Unmatched']['WardName_Original'].unique()
        
        for ward in unmatched:
            if ward in mappings:
                continue
                
            # Clean ward
            clean_ward = re.sub(r'^[a-z]{2}\s+', '', ward)
            clean_ward = clean_ward.replace(' Ward', '').strip()
            
            # Skip if too short
            if len(clean_ward) < 5:
                continue
            
            # Find wards that contain this as substring or vice versa
            for sf_ward in state_wards:
                if len(sf_ward) < 5:
                    continue
                    
                # Check both directions
                if (clean_ward.lower() in sf_ward.lower() or 
                    sf_ward.lower() in clean_ward.lower()):
                    
                    # Verify it's a significant match
                    overlap_ratio = len(set(clean_ward.lower()) & set(sf_ward.lower())) / \
                                   min(len(set(clean_ward.lower())), len(set(sf_ward.lower())))
                    
                    if overlap_ratio >= 0.7:
                        mappings[ward] = sf_ward
                        self.techniques_used['substring'].append(ward)
                        print(f"  ✓ Substring: '{ward}' -> '{sf_ward}'")
                        break
        
        return mappings
    
    def process_state_advanced(self, state_name):
        """Apply all advanced techniques to a state"""
        print(f"\n{'='*60}")
        print(f"ADVANCED MATCHING: {state_name}")
        print('='*60)
        
        # Load the final file
        file_path = self.final_dir / f'{state_name.lower()}_tpr_final.csv'
        if not file_path.exists():
            print(f"  ⚠ File not found: {file_path}")
            return None
        
        df = pd.read_csv(file_path)
        
        # Check current status
        if 'Match_Status' not in df.columns:
            print(f"  ⚠ No Match_Status column")
            return None
        
        unmatched_before = len(df[df['Match_Status'] == 'Unmatched'])
        if unmatched_before == 0:
            print(f"  ✓ Already 100% matched!")
            return df
        
        print(f"  Current unmatched: {unmatched_before}")
        
        # Apply techniques in order
        all_mappings = {}
        
        # Install jellyfish if needed for phonetic matching
        try:
            import jellyfish
        except ImportError:
            import subprocess
            subprocess.check_call(['chatmrpt_venv_new/bin/pip', 'install', 'jellyfish', '--quiet'])
            import jellyfish
        
        # Apply each technique
        techniques = [
            self.technique_1_lga_context_matching,
            self.technique_2_phonetic_matching,
            self.technique_3_word_reordering,
            self.technique_4_abbreviation_expansion,
            self.technique_5_special_character_normalization,
            self.technique_6_substring_matching
        ]
        
        for technique in techniques:
            try:
                mappings = technique(state_name, df)
                all_mappings.update(mappings)
                
                # Update df with new mappings
                for orig, mapped in mappings.items():
                    mask = df['WardName_Original'] == orig
                    df.loc[mask, 'WardName'] = mapped
                    df.loc[mask, 'Match_Status'] = 'Matched'
            except Exception as e:
                print(f"  ⚠ Error in {technique.__name__}: {e}")
        
        # Calculate improvement
        unmatched_after = len(df[df['Match_Status'] == 'Unmatched'])
        improvement = unmatched_before - unmatched_after
        
        if improvement > 0:
            print(f"\n  🎯 Improved by {improvement} matches!")
            print(f"  Remaining unmatched: {unmatched_after}")
            
            # Save advanced version
            output_path = self.final_dir / f'{state_name.lower()}_tpr_advanced.csv'
            df.to_csv(output_path, index=False)
            print(f"  ✓ Saved: {output_path}")
        else:
            print(f"  No additional matches found")
        
        return df
    
    def run_advanced_matching(self):
        """Run advanced matching on all states needing improvement"""
        print("ADVANCED WARD MATCHING SYSTEM")
        print("="*80)
        
        # Focus on states with <95% match rate
        target_states = []
        
        # Check which states need improvement
        summary_path = self.final_dir / 'cleaning_summary.csv'
        if summary_path.exists():
            summary_df = pd.read_csv(summary_path)
            target_states = summary_df[summary_df['Match_Rate_%'] < 95]['State'].str.lower().tolist()
        
        if not target_states:
            # Process all if no summary
            target_states = ['rivers', 'ogun', 'niger', 'kogi', 'kebbi', 'kwara', 'katsina']
        
        print(f"Target states for improvement: {', '.join(target_states)}")
        
        total_improvements = 0
        for state in target_states:
            result = self.process_state_advanced(state.title())
            if result is not None:
                improvement = len(result[result['Match_Status'] == 'Matched']) - \
                             len(pd.read_csv(self.final_dir / f'{state}_tpr_final.csv')[
                                 pd.read_csv(self.final_dir / f'{state}_tpr_final.csv')['Match_Status'] == 'Matched'])
                total_improvements += max(0, improvement)
        
        # Summary of techniques used
        print("\n" + "="*80)
        print("TECHNIQUES SUMMARY")
        print("="*80)
        for technique, wards in self.techniques_used.items():
            if wards:
                print(f"{technique}: {len(wards)} matches")
        
        print(f"\nTotal new matches found: {total_improvements}")
        
        return total_improvements


def main():
    """Run advanced matching"""
    # Install jellyfish
    import subprocess
    subprocess.check_call(['chatmrpt_venv_new/bin/pip', 'install', 'jellyfish', '--quiet'])
    
    matcher = AdvancedWardMatcher()
    improvements = matcher.run_advanced_matching()
    
    print("\n✅ ADVANCED MATCHING COMPLETE!")
    print(f"Total improvements: {improvements} new matches")


if __name__ == "__main__":
    main()