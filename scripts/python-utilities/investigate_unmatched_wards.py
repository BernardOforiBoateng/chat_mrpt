#!/usr/bin/env python3
"""
Investigation script for unmatched wards
Analyzes why certain wards don't match and finds potential correspondences
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
import warnings
from fuzzywuzzy import fuzz, process
from collections import defaultdict

warnings.filterwarnings('ignore')

class UnmatchedWardsInvestigator:
    def __init__(self):
        """Initialize the investigator"""
        self.gdf = gpd.read_file('www/complete_names_wards/wards.shp')
        self.cleaned_dir = Path('www/cleaned_tpr_data')
        
    def analyze_unmatched_patterns(self):
        """Analyze patterns in unmatched wards across all states"""
        
        print("="*80)
        print("UNMATCHED WARDS INVESTIGATION REPORT")
        print("="*80)
        
        # Store all unmatched wards by state
        all_unmatched = defaultdict(list)
        
        # States with most issues
        problem_states = {}
        
        for cleaned_file in sorted(self.cleaned_dir.glob('*_tpr_cleaned.csv')):
            state_name = cleaned_file.stem.replace('_tpr_cleaned', '').title()
            df = pd.read_csv(cleaned_file)
            
            if 'Match_Status' in df.columns:
                unmatched = df[df['Match_Status'] == 'Unmatched']
                if len(unmatched) > 0:
                    unmatched_wards = unmatched['WardName_Original'].dropna().unique()
                    all_unmatched[state_name] = list(unmatched_wards)
                    
                    # Calculate unmatched percentage
                    total_unique = df['WardName_Original'].nunique()
                    unmatched_unique = len(unmatched_wards)
                    unmatched_pct = (unmatched_unique / total_unique) * 100
                    
                    if unmatched_pct > 10:  # States with >10% unmatched
                        problem_states[state_name] = {
                            'count': unmatched_unique,
                            'percentage': unmatched_pct,
                            'wards': unmatched_wards
                        }
        
        # Analyze problem states in detail
        print("\n📊 STATES WITH SIGNIFICANT MATCHING ISSUES (>10% unmatched):")
        print("-"*80)
        
        for state, info in sorted(problem_states.items(), key=lambda x: x[1]['percentage'], reverse=True):
            print(f"\n{state}: {info['percentage']:.1f}% unmatched ({info['count']} wards)")
            self.investigate_state_deeply(state, info['wards'][:10])  # Investigate top 10
            
        return all_unmatched
    
    def investigate_state_deeply(self, state_name, unmatched_wards):
        """Deep investigation of a specific state's unmatched wards"""
        
        # Get shapefile wards for this state
        shapefile_wards = self.gdf[self.gdf['StateName'] == state_name]['WardName'].dropna().unique()
        
        print(f"\n  Investigating {len(unmatched_wards)} sample unmatched wards:")
        
        for ward in unmatched_wards:
            # Clean the ward name
            cleaned = ward.replace(ward[:3] if ward[:3].endswith(' ') else '', '').strip()
            cleaned = cleaned.replace(' Ward', '').strip()
            
            # Find best matches in shapefile
            if len(shapefile_wards) > 0:
                matches = process.extract(cleaned, shapefile_wards, scorer=fuzz.token_sort_ratio, limit=3)
                
                print(f"\n  ❌ '{ward}'")
                print(f"     Cleaned: '{cleaned}'")
                print(f"     Potential matches in shapefile:")
                for match, score in matches:
                    if score >= 60:  # Show matches with 60%+ similarity
                        print(f"       - '{match}' (similarity: {score}%)")
                    
                # Check for LGA-based disambiguation
                if '(' in ward and ')' in ward:
                    lga_hint = ward[ward.find('(')+1:ward.find(')')]
                    print(f"     LGA hint: '{lga_hint}'")
                    
                    # Check if there are wards with similar names in different LGAs
                    base_name = ward[:ward.find('(')].strip().replace(ward[:3] if ward[:3].endswith(' ') else '', '').replace(' Ward', '').strip()
                    similar_in_shapefile = [w for w in shapefile_wards if base_name.upper() in w.upper() or w.upper() in base_name.upper()]
                    if similar_in_shapefile:
                        print(f"     Similar names in shapefile: {similar_in_shapefile[:3]}")
    
    def analyze_rivers_special_case(self):
        """Special investigation for Rivers state (12.5% match rate)"""
        
        print("\n" + "="*80)
        print("SPECIAL INVESTIGATION: RIVERS STATE")
        print("="*80)
        
        # Load Rivers cleaned data
        rivers_df = pd.read_csv('www/cleaned_tpr_data/rivers_tpr_cleaned.csv')
        
        # Get unique ward patterns
        rivers_wards_original = rivers_df['WardName_Original'].dropna().unique()
        
        # Analyze naming patterns
        patterns = defaultdict(int)
        for ward in rivers_wards_original:
            if 'Ward' in ward and any(char.isdigit() for char in ward):
                # Extract pattern like "Location Ward N"
                parts = ward.split('Ward')
                if len(parts) == 2 and parts[1].strip().isdigit():
                    location = parts[0].strip().replace('ri ', '')
                    patterns[location] += 1
        
        print("\nRivers State Ward Naming Pattern Analysis:")
        print("-"*40)
        print("Pattern detected: 'Location Ward N' (where N is a number)")
        print(f"Locations with numbered wards: {len(patterns)}")
        
        # Show top locations with numbered wards
        print("\nTop locations with numbered wards:")
        for location, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {location}: {count} numbered wards")
        
        # Get Rivers shapefile wards
        rivers_shapefile_wards = self.gdf[self.gdf['StateName'] == 'Rivers']['WardName'].dropna().unique()
        
        print(f"\nShapefile has {len(rivers_shapefile_wards)} wards for Rivers")
        print("Sample shapefile ward names:")
        for ward in sorted(rivers_shapefile_wards)[:20]:
            print(f"  - {ward}")
        
        # Check if shapefile uses different naming convention
        shapefile_has_numbers = sum(1 for w in rivers_shapefile_wards if any(char.isdigit() for char in w))
        print(f"\nShapefile wards with numbers: {shapefile_has_numbers}/{len(rivers_shapefile_wards)}")
        
        # Try to find pattern matches
        print("\nAttempting to match patterns:")
        sample_tpr_wards = rivers_wards_original[:10]
        for tpr_ward in sample_tpr_wards:
            location = tpr_ward.replace('ri ', '').replace(' Ward', '').split()[0] if ' Ward ' in tpr_ward else tpr_ward.replace('ri ', '')
            
            # Find shapefile wards containing this location name
            matches = [sw for sw in rivers_shapefile_wards if location.upper() in sw.upper() or sw.upper() in location.upper()]
            
            print(f"\n  TPR: '{tpr_ward}'")
            if matches:
                print(f"    Possible shapefile matches: {matches[:3]}")
            else:
                print(f"    No matches found for location '{location}'")
    
    def check_lga_consistency(self):
        """Check if LGA information could help with matching"""
        
        print("\n" + "="*80)
        print("LGA CONSISTENCY CHECK")
        print("="*80)
        
        # Sample check for states with LGA hints in ward names
        for cleaned_file in ['www/cleaned_tpr_data/kaduna_tpr_cleaned.csv', 
                             'www/cleaned_tpr_data/kano_tpr_cleaned.csv']:
            if Path(cleaned_file).exists():
                state_name = Path(cleaned_file).stem.replace('_tpr_cleaned', '').title()
                df = pd.read_csv(cleaned_file)
                
                print(f"\n{state_name} State LGA Analysis:")
                print("-"*40)
                
                # Check for LGA column
                if 'LGA' in df.columns:
                    unique_lgas = df['LGA'].dropna().unique()
                    print(f"TPR file has {len(unique_lgas)} unique LGAs")
                    
                    # Check shapefile LGAs
                    state_gdf = self.gdf[self.gdf['StateName'] == state_name]
                    if 'LGAName' in state_gdf.columns:
                        shapefile_lgas = state_gdf['LGAName'].dropna().unique()
                        print(f"Shapefile has {len(shapefile_lgas)} unique LGAs")
                        
                        # Compare LGAs
                        tpr_lgas_set = set(unique_lgas)
                        shapefile_lgas_set = set(shapefile_lgas)
                        
                        common_lgas = tpr_lgas_set.intersection(shapefile_lgas_set)
                        tpr_only = tpr_lgas_set - shapefile_lgas_set
                        shapefile_only = shapefile_lgas_set - tpr_lgas_set
                        
                        print(f"Common LGAs: {len(common_lgas)}")
                        if tpr_only:
                            print(f"LGAs only in TPR: {list(tpr_only)[:5]}")
                        if shapefile_only:
                            print(f"LGAs only in shapefile: {list(shapefile_only)[:5]}")
                        
                        # Check if using LGA could improve matching
                        if 'Match_Status' in df.columns:
                            unmatched_df = df[df['Match_Status'] == 'Unmatched']
                            if len(unmatched_df) > 0:
                                print("\nChecking if LGA+Ward combination could help:")
                                
                                # Take sample of unmatched wards
                                sample = unmatched_df.head(5)
                                for _, row in sample.iterrows():
                                    ward = row['WardName_Original']
                                    lga = row.get('LGA', 'Unknown')
                                    
                                    # Clean ward name
                                    cleaned_ward = ward.replace(ward[:3] if ward[:3].endswith(' ') else '', '').replace(' Ward', '').strip()
                                    
                                    # Look for this ward in the same LGA in shapefile
                                    if 'LGAName' in state_gdf.columns:
                                        lga_wards = state_gdf[state_gdf['LGAName'] == lga]['WardName'].dropna().unique()
                                        if len(lga_wards) > 0:
                                            best_match = process.extractOne(cleaned_ward, lga_wards, scorer=fuzz.token_sort_ratio)
                                            if best_match:
                                                print(f"  Ward: '{ward}' (LGA: {lga})")
                                                print(f"    Best match in same LGA: '{best_match[0]}' ({best_match[1]}%)")
    
    def generate_recommendations(self):
        """Generate recommendations for improving matching"""
        
        print("\n" + "="*80)
        print("RECOMMENDATIONS FOR IMPROVING MATCHING")
        print("="*80)
        
        recommendations = [
            "\n1. **Rivers State Special Handling**:",
            "   - Rivers uses 'Location Ward N' format (e.g., 'Port-Harcourt Ward 2')",
            "   - Shapefile might use different naming convention",
            "   - Recommendation: Create custom mapping table for Rivers wards",
            "",
            "2. **LGA-Based Disambiguation**:",
            "   - Many TPR wards include LGA hints in parentheses (e.g., 'Sabon Gari Ward (Kudan)')",
            "   - Use LGA information to distinguish between wards with same base name",
            "   - Recommendation: Implement LGA-aware matching algorithm",
            "",
            "3. **Common Pattern Issues**:",
            "   - Spelling variations: 'Nassarawa' vs 'Nasarawa'",
            "   - Compound names: 'Tudun Wada' vs 'Tudunwada'",
            "   - Roman numerals vs numbers: 'II' vs '2'",
            "   - Recommendation: Expand normalization rules",
            "",
            "4. **Missing Wards**:",
            "   - Some TPR wards might be new or renamed since shapefile creation",
            "   - Some might be health facility catchment areas, not official wards",
            "   - Recommendation: Verify with current administrative boundaries",
            "",
            "5. **Data Quality Issues**:",
            "   - Check for data entry errors in TPR files",
            "   - Verify shapefile is up-to-date with current ward boundaries",
            "   - Recommendation: Cross-reference with official government ward lists"
        ]
        
        for rec in recommendations:
            print(rec)
        
        return recommendations


def main():
    """Main investigation function"""
    investigator = UnmatchedWardsInvestigator()
    
    # Analyze unmatched patterns
    unmatched_by_state = investigator.analyze_unmatched_patterns()
    
    # Special investigation for Rivers state
    investigator.analyze_rivers_special_case()
    
    # Check LGA consistency
    investigator.check_lga_consistency()
    
    # Generate recommendations
    investigator.generate_recommendations()
    
    # Export detailed unmatched list
    print("\n" + "="*80)
    print("EXPORTING DETAILED UNMATCHED WARDS LIST")
    print("="*80)
    
    # Create comprehensive unmatched wards report
    all_unmatched_data = []
    for state, wards in unmatched_by_state.items():
        for ward in wards:
            all_unmatched_data.append({
                'State': state,
                'Unmatched_Ward': ward,
                'Cleaned_Version': ward.replace(ward[:3] if ward[:3].endswith(' ') else '', '').replace(' Ward', '').strip()
            })
    
    if all_unmatched_data:
        unmatched_df = pd.DataFrame(all_unmatched_data)
        output_path = 'www/unmatched_wards_analysis.csv'
        unmatched_df.to_csv(output_path, index=False)
        print(f"Detailed unmatched wards list saved to: {output_path}")
        print(f"Total unmatched unique wards across all states: {len(unmatched_df)}")


if __name__ == "__main__":
    main()