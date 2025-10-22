#!/usr/bin/env python3
"""
Smart Ward Matching System
Intelligently infers abbreviations and creates comprehensive mappings for all states
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
import re
from fuzzywuzzy import fuzz
from collections import defaultdict
import warnings

warnings.filterwarnings('ignore')

class SmartWardMatcher:
    def __init__(self):
        """Initialize the smart matcher"""
        self.gdf = gpd.read_file('www/complete_names_wards/wards.shp')
        self.cleaned_dir = Path('www/cleaned_tpr_data')
        self.mappings = {}
        
    def analyze_abbreviation_patterns(self, state_name):
        """Analyze and decode abbreviation patterns for a state"""
        
        # Get shapefile wards for this state
        state_wards = self.gdf[self.gdf['StateName'] == state_name]['WardName'].dropna().unique()
        
        # Identify abbreviated patterns (e.g., "Phward 1", "Aboward 2")
        abbreviated = {}
        for ward in state_wards:
            # Check for pattern like "XXXward N" or "Ward N"
            match = re.match(r'^([A-Za-z]+)(ward)\s*(\d+)$', ward, re.IGNORECASE)
            if match:
                prefix = match.group(1).lower()
                number = match.group(3)
                if prefix not in abbreviated:
                    abbreviated[prefix] = []
                abbreviated[prefix].append((ward, number))
        
        return abbreviated
    
    def infer_abbreviation(self, full_name, abbreviations):
        """Intelligently infer what abbreviation matches a full name"""
        
        # Clean the full name
        clean_name = full_name.lower().replace('-', '').replace('/', '').replace(' ', '')
        
        best_match = None
        best_score = 0
        
        for abbrev in abbreviations.keys():
            # Multiple matching strategies
            strategies = [
                # 1. First N letters match
                clean_name.startswith(abbrev),
                # 2. Abbreviation from first letters of each word
                self.get_initials(full_name).startswith(abbrev),
                # 3. Consonants match
                self.get_consonants(clean_name).startswith(abbrev),
                # 4. Key letters match
                self.get_key_letters(full_name).startswith(abbrev),
                # 5. Fuzzy match
                fuzz.partial_ratio(abbrev, clean_name) > 80
            ]
            
            score = sum(strategies)
            if score > best_score:
                best_score = score
                best_match = abbrev
        
        return best_match if best_score >= 2 else None
    
    def get_initials(self, text):
        """Get initials from text (e.g., 'Port Harcourt' -> 'ph')"""
        words = text.replace('-', ' ').replace('/', ' ').split()
        return ''.join(w[0].lower() for w in words if w)
    
    def get_consonants(self, text):
        """Get consonants from text (e.g., 'Emuoha' -> 'mh')"""
        text = text.lower()
        vowels = 'aeiou'
        return ''.join(c for c in text if c not in vowels and c.isalpha())[:3]
    
    def get_key_letters(self, text):
        """Get key letters for matching (first 3 chars)"""
        clean = re.sub(r'[^a-z]', '', text.lower())
        return clean[:3]
    
    def process_state(self, state_name, file_path):
        """Process a single state with smart matching"""
        
        print(f"\n{'='*60}")
        print(f"Processing {state_name}")
        print('='*60)
        
        # Load the cleaned file
        df = pd.read_csv(file_path)
        
        # Get shapefile wards for this state
        state_shapefile_wards = self.gdf[self.gdf['StateName'] == state_name]['WardName'].dropna().unique()
        
        # Analyze abbreviation patterns
        abbreviations = self.analyze_abbreviation_patterns(state_name)
        
        if abbreviations:
            print(f"\nDetected {len(abbreviations)} abbreviation patterns in shapefile")
            
        # Get unmatched wards
        if 'Match_Status' in df.columns:
            unmatched_df = df[df['Match_Status'] == 'Unmatched'].copy()
            
            if len(unmatched_df) == 0:
                print(f"✓ All wards already matched for {state_name}")
                return df, {}
            
            print(f"\nProcessing {len(unmatched_df['WardName_Original'].unique())} unmatched wards...")
            
            # Create mapping for this state
            state_mapping = {}
            
            for original_ward in unmatched_df['WardName_Original'].unique():
                # Clean the ward name
                cleaned = original_ward
                # Remove state prefix
                cleaned = re.sub(r'^[a-z]{2}\s+', '', cleaned)
                # Remove 'Ward' and extract parts
                
                match_found = False
                
                # Strategy 1: Direct number matching for abbreviated patterns
                if ' Ward ' in cleaned and abbreviations:
                    parts = cleaned.split(' Ward ')
                    location = parts[0].strip()
                    number = parts[1].strip() if len(parts) > 1 else ''
                    
                    # Try to infer abbreviation
                    inferred_abbrev = self.infer_abbreviation(location, abbreviations)
                    
                    if inferred_abbrev and number.isdigit():
                        # Find matching ward with this abbreviation and number
                        for ward, ward_num in abbreviations.get(inferred_abbrev, []):
                            if ward_num == number:
                                state_mapping[original_ward] = ward
                                print(f"  ✓ Matched: '{location} Ward {number}' -> '{ward}'")
                                match_found = True
                                break
                
                # Strategy 2: Fuzzy matching for non-abbreviated wards
                if not match_found:
                    # Clean for fuzzy matching
                    clean_ward = cleaned.replace(' Ward', '').strip()
                    if '(' in clean_ward:
                        # Extract base name before parentheses
                        clean_ward = clean_ward[:clean_ward.find('(')].strip()
                    
                    # Try fuzzy matching
                    best_match = None
                    best_score = 0
                    
                    for shapefile_ward in state_shapefile_wards:
                        score = fuzz.token_sort_ratio(clean_ward, shapefile_ward)
                        if score > best_score and score >= 75:
                            best_score = score
                            best_match = shapefile_ward
                    
                    if best_match:
                        state_mapping[original_ward] = best_match
                        if best_score < 100:
                            print(f"  ~ Fuzzy matched: '{cleaned}' -> '{best_match}' ({best_score}%)")
                        match_found = True
            
            # Apply the new mappings
            if state_mapping:
                print(f"\n✓ Created {len(state_mapping)} new mappings for {state_name}")
                
                # Update the dataframe
                for orig, mapped in state_mapping.items():
                    mask = df['WardName_Original'] == orig
                    df.loc[mask, 'WardName'] = mapped
                    df.loc[mask, 'Match_Status'] = 'Matched'
                
                self.mappings[state_name] = state_mapping
            
            return df, state_mapping
        
        return df, {}
    
    def process_all_states(self):
        """Process all states with smart matching"""
        
        print("SMART WARD MATCHING SYSTEM")
        print("="*80)
        
        overall_stats = {
            'total_improved': 0,
            'states_improved': []
        }
        
        # Process each state
        for file_path in sorted(self.cleaned_dir.glob('*_tpr_cleaned.csv')):
            # Skip the improved Rivers file if it exists
            if 'improved' in str(file_path):
                continue
                
            state_name = file_path.stem.replace('_tpr_cleaned', '').title()
            
            # Process the state
            improved_df, mapping = self.process_state(state_name, file_path)
            
            if mapping:
                # Save improved file
                output_path = file_path.parent / f"{state_name.lower()}_tpr_smart_matched.csv"
                improved_df.to_csv(output_path, index=False)
                
                # Calculate improvement
                original_unmatched = len(improved_df[improved_df['Match_Status'] == 'Unmatched']) if 'Match_Status' in improved_df.columns else 0
                
                print(f"  Remaining unmatched: {original_unmatched}")
                print(f"  Saved improved file: {output_path}")
                
                overall_stats['total_improved'] += len(mapping)
                overall_stats['states_improved'].append(state_name)
        
        # Save all mappings
        if self.mappings:
            all_mappings = []
            for state, mappings in self.mappings.items():
                for orig, mapped in mappings.items():
                    all_mappings.append({
                        'State': state,
                        'Original_Ward': orig,
                        'Mapped_Ward': mapped
                    })
            
            mappings_df = pd.DataFrame(all_mappings)
            mappings_df.to_csv('www/smart_ward_mappings.csv', index=False)
            print(f"\n✓ Saved all mappings to: www/smart_ward_mappings.csv")
        
        return overall_stats
    
    def validate_improvements(self):
        """Validate the improvements made"""
        
        print("\n" + "="*80)
        print("VALIDATION REPORT")
        print("="*80)
        
        total_original_unmatched = 0
        total_new_unmatched = 0
        
        for file_path in sorted(self.cleaned_dir.glob('*_tpr_smart_matched.csv')):
            state_name = file_path.stem.replace('_tpr_smart_matched', '').title()
            
            # Load improved file
            df = pd.read_csv(file_path)
            
            if 'Match_Status' in df.columns:
                matched = len(df[df['Match_Status'] == 'Matched'])
                unmatched = len(df[df['Match_Status'] == 'Unmatched'])
                total = len(df)
                
                match_rate = (matched / total) * 100
                
                print(f"\n{state_name}:")
                print(f"  Match rate: {match_rate:.1f}%")
                print(f"  Unmatched: {unmatched} rows")
                
                total_new_unmatched += unmatched
        
        print(f"\n{'='*80}")
        print(f"TOTAL REMAINING UNMATCHED: {total_new_unmatched} rows")
        
        return total_new_unmatched


def main():
    """Main execution"""
    matcher = SmartWardMatcher()
    
    # Process all states
    stats = matcher.process_all_states()
    
    print("\n" + "="*80)
    print("SMART MATCHING COMPLETE")
    print("="*80)
    print(f"Total new mappings created: {stats['total_improved']}")
    print(f"States improved: {len(stats['states_improved'])}")
    
    if stats['states_improved']:
        print(f"Improved states: {', '.join(stats['states_improved'])}")
    
    # Validate improvements
    remaining = matcher.validate_improvements()
    
    print("\n✓ Smart matching process complete!")
    print(f"Files saved with suffix: _tpr_smart_matched.csv")


if __name__ == "__main__":
    main()