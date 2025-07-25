"""ITN Distribution Pipeline for ChatMRPT."""
import logging
import pandas as pd
import geopandas as gpd
import numpy as np
import os
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import plotly.graph_objects as go
from pandas.api.types import is_datetime64_any_dtype
from app.data.population_data.itn_population_loader import get_population_loader
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

logger = logging.getLogger(__name__)

def detect_state(data_handler) -> str:
    """Detect state from shapefile or session data."""
    # State code to name mapping
    state_mapping = {
        'KN': 'Kano',
        'OS': 'Osun',
        'KT': 'Katsina',
        'KB': 'Kebbi',
        'SO': 'Sokoto',
        'ZA': 'Zamfara',
        'JI': 'Jigawa',
        'AD': 'Adamawa',
        'DT': 'Delta',
        'KD': 'Kaduna',
        'KW': 'Kwara',
        'NG': 'Niger',
        'TR': 'Taraba',
        'YB': 'Yobe'
    }
    
    # Check shapefile data first
    if hasattr(data_handler, 'shapefile_data') and data_handler.shapefile_data is not None:
        # Check for State column
        if 'State' in data_handler.shapefile_data.columns:
            state = data_handler.shapefile_data['State'].iloc[0]
            if pd.notna(state):
                return state
        # Check for StateCode column
        if 'StateCode' in data_handler.shapefile_data.columns:
            state_code = data_handler.shapefile_data['StateCode'].iloc[0]
            if pd.notna(state_code) and state_code in state_mapping:
                return state_mapping[state_code]
    
    # Check CSV data
    if hasattr(data_handler, 'csv_data') and data_handler.csv_data is not None:
        # Check for State column
        if 'State' in data_handler.csv_data.columns:
            state = data_handler.csv_data['State'].iloc[0]
            if pd.notna(state):
                return state
        # Check for StateCode column
        if 'StateCode' in data_handler.csv_data.columns:
            state_code = data_handler.csv_data['StateCode'].iloc[0]
            if pd.notna(state_code) and state_code in state_mapping:
                return state_mapping[state_code]
    
    # Check unified dataset as another fallback
    if hasattr(data_handler, 'unified_dataset') and data_handler.unified_dataset is not None:
        if 'StateCode' in data_handler.unified_dataset.columns:
            state_code = data_handler.unified_dataset['StateCode'].iloc[0]
            if pd.notna(state_code) and state_code in state_mapping:
                logger.info(f"Detected state from unified dataset: {state_mapping[state_code]}")
                return state_mapping[state_code]
    
    # Try to detect from session or file paths
    try:
        from flask import session
        if 'state_name' in session:
            state = session['state_name']
            logger.info(f"Detected state from session: {state}")
            return state
    except:
        pass
    
    # Log error - state detection failed
    logger.error("Could not detect state from data. State detection is required for ITN planning.")
    return None  # Return None to indicate detection failure

def load_population_data(state: str) -> Optional[pd.DataFrame]:
    """Load and aggregate population data for the state."""
    loader = get_population_loader()
    
    # Try new format first
    pop_df = loader.load_state_population(state)
    
    if pop_df is not None:
        # New format data is already clean with WardName, LGA, Population
        logger.info(f"Using new cleaned population data for {state}")
        
        # Create output format matching expected structure
        ward_population = pop_df.copy()
        
        # Ensure we have the expected column names
        if 'Ward' in ward_population.columns and 'WardName' not in ward_population.columns:
            ward_population = ward_population.rename(columns={'Ward': 'WardName'})
        if 'LGA' in ward_population.columns and 'AdminLevel2' not in ward_population.columns:
            ward_population['AdminLevel2'] = ward_population['LGA']
        
        # Add dummy coordinates for now (will be matched from shapefile)
        if 'AvgLatitude' not in ward_population.columns:
            ward_population['AvgLatitude'] = np.nan
        if 'AvgLongitude' not in ward_population.columns:
            ward_population['AvgLongitude'] = np.nan
        
        # Add lowercase version for case-insensitive matching
        ward_population['WardName_lower'] = ward_population['WardName'].str.lower()
        
        logger.info(f"Loaded population data for {len(ward_population)} wards in {state}")
        logger.info(f"Total population: {ward_population['Population'].sum():,.0f}")
        
        return ward_population
    
    # Fall back to old format processing
    logger.info(f"New format not available for {state}, trying old format")
    
    # Check both xlsx and csv formats
    xlsx_path = f'app/data/population_data/pbi_distribution_{state}.xlsx'
    csv_path = f'app/data/population_data/pbi_distribution_{state}.csv'
    
    pop_data = None
    if os.path.exists(xlsx_path):
        pop_data = pd.read_excel(xlsx_path)
    elif os.path.exists(csv_path):
        # Try different encodings for CSV
        try:
            pop_data = pd.read_csv(csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                pop_data = pd.read_csv(csv_path, encoding='latin-1')
            except:
                pop_data = pd.read_csv(csv_path, encoding='cp1252')
    else:
        logger.warning(f"No population data for {state}")
        return None
    
    # Aggregate by ward (AdminLevel3 = WardName) and LGA (AdminLevel2)
    # Each row is a distribution point, we need to sum by ward
    # But we also need to preserve LGA information and coordinates for duplicate ward names
    ward_population = pop_data.groupby(['AdminLevel3', 'AdminLevel2']).agg({
        'N_FamilyMembers': 'sum',
        'AvgLatitude': 'mean',
        'AvgLongitude': 'mean'
    }).reset_index()
    ward_population.columns = ['WardName', 'AdminLevel2', 'Population', 'AvgLatitude', 'AvgLongitude']
    
    # Add lowercase version for case-insensitive matching
    ward_population['WardName_lower'] = ward_population['WardName'].str.lower()
    
    # Identify duplicate ward names in population data
    duplicate_mask = ward_population.duplicated(subset=['WardName'], keep=False)
    duplicate_wards = ward_population[duplicate_mask]
    unique_wards = ward_population[~duplicate_mask]
    
    if len(duplicate_wards) > 0:
        logger.info(f"Found {len(duplicate_wards)} duplicate ward entries across LGAs in population data")
        dup_ward_names = duplicate_wards['WardName'].unique()
        logger.info(f"Duplicate ward names: {list(dup_ward_names)[:10]}")
    
    logger.info(f"Loaded population data for {len(ward_population)} ward-LGA combinations in {state}")
    logger.info(f"  Unique wards: {len(unique_wards)}, Duplicate entries: {len(duplicate_wards)}")
    
    # Return the full dataset with coordinates
    return ward_population

def normalize_ward_name(ward_name: str) -> str:
    """
    Normalize ward name for better matching.
    
    Args:
        ward_name: Original ward name
        
    Returns:
        Normalized ward name
    """
    if pd.isna(ward_name):
        return ""
        
    # Convert to lowercase
    normalized = str(ward_name).lower().strip()
    
    # Remove content in parentheses
    normalized = normalized.split('(')[0].strip()
    
    # Replace roman numerals with numbers (order matters!)
    # Using regex to match word boundaries
    roman_replacements = [
        (r'\bviii\b', '8'), (r'\bvii\b', '7'), (r'\bvi\b', '6'), 
        (r'\biv\b', '4'), (r'\biii\b', '3'), (r'\bii\b', '2'), 
        (r'\bix\b', '9'), (r'\bv\b', '5'), (r'\bi\b', '1')
    ]
    for pattern, replacement in roman_replacements:
        normalized = re.sub(pattern, replacement, normalized)
    
    # Remove common suffixes
    suffixes = [' ward', ' wards']
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
    
    # Replace common separators with space
    normalized = normalized.replace('/', ' ').replace('-', ' ').replace('_', ' ')
    
    # Remove extra spaces
    normalized = ' '.join(normalized.split())
    
    return normalized

def fuzzy_match_ward_names(analysis_wards: List[str], population_wards: List[str], 
                          threshold: int = 80) -> Dict[str, Tuple[str, int]]:
    """
    Perform fuzzy matching between analysis ward names and population ward names.
    
    Args:
        analysis_wards: List of ward names from analysis data
        population_wards: List of ward names from population data
        threshold: Minimum matching score (0-100)
        
    Returns:
        Dictionary mapping analysis ward names to (matched_population_ward, score)
    """
    matches = {}
    unmatched = []
    
    # Normalize all ward names
    pop_ward_dict = {normalize_ward_name(w): w for w in population_wards}
    pop_normalized = list(pop_ward_dict.keys())
    
    for ward in analysis_wards:
        normalized_ward = normalize_ward_name(ward)
        
        # First try exact match
        if normalized_ward in pop_ward_dict:
            matches[ward] = (pop_ward_dict[normalized_ward], 100)
            continue
        
        # Try fuzzy matching
        best_match = process.extractOne(normalized_ward, pop_normalized, 
                                       scorer=fuzz.token_sort_ratio)
        
        if best_match and best_match[1] >= threshold:
            matched_original = pop_ward_dict[best_match[0]]
            matches[ward] = (matched_original, best_match[1])
        else:
            # Try partial ratio for substring matches
            best_partial = process.extractOne(normalized_ward, pop_normalized, 
                                            scorer=fuzz.partial_ratio)
            if best_partial and best_partial[1] >= 90:  # Higher threshold for partial matches
                matched_original = pop_ward_dict[best_partial[0]]
                matches[ward] = (matched_original, best_partial[1])
            else:
                unmatched.append(ward)
    
    if unmatched:
        logger.warning(f"Could not match {len(unmatched)} wards: {unmatched[:5]}...")
    
    return matches

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on Earth (in km)."""
    from math import radians, cos, sin, asin, sqrt
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    return c * r

def calculate_nets_needed(population: float, avg_household_size: float) -> int:
    """Calculate nets needed: 1 per 1.8 people, min 1 per household."""
    households = np.ceil(population / avg_household_size)
    return int(np.ceil(max(population / 1.8, households)))

def calculate_itn_distribution(data_handler, session_id: str, total_nets: int = 10000, avg_household_size: float = 5.0, urban_threshold: float = 30.0, method: str = 'composite') -> Dict[str, Any]:
    """Perform two-phase ITN distribution calculation."""
    state = detect_state(data_handler)
    
    if state is None:
        return {
            'status': 'error', 
            'message': 'Could not detect state from the data. Please ensure your data includes state information (State or StateCode column).'
        }
    
    logger.info(f"Detected state: {state}")
    
    pop_data = load_population_data(state)
    
    # Use unified dataset if available - it has all the data we need
    if hasattr(data_handler, 'unified_dataset') and data_handler.unified_dataset is not None:
        logger.info("Using unified dataset for ITN planning")
        # Get relevant columns from unified dataset
        if method == 'composite':
            rank_col = 'composite_rank'
            score_col = 'composite_score'
            category_col = 'composite_category'
        else:
            rank_col = 'pca_rank'
            score_col = 'pca_score' 
            category_col = 'pca_category'
        
        # Extract rankings with all necessary data from unified dataset
        required_cols = ['WardName', score_col, rank_col, category_col]
        if 'urbanPercentage' in data_handler.unified_dataset.columns:
            required_cols.append('urbanPercentage')
        
        rankings = data_handler.unified_dataset[required_cols].copy()
        rankings = rankings.rename(columns={
            score_col: 'score',
            rank_col: 'overall_rank',
            category_col: 'vulnerability_category'
        })
        
        # Fix dtype mismatch - ensure numeric columns are numeric
        rankings['score'] = pd.to_numeric(rankings['score'], errors='coerce')
        rankings['overall_rank'] = pd.to_numeric(rankings['overall_rank'], errors='coerce')
        rankings = rankings.dropna(subset=['score'])  # Drop any rows that became NaN
    else:
        # Fall back to original approach
        if method == 'composite':
            rankings = data_handler.vulnerability_rankings.copy()
        else:
            rankings = data_handler.vulnerability_rankings_pca.copy()
    
    shp_data = data_handler.shapefile_data
    
    # Merge population if available
    if pop_data is not None:
        logger.info(f"Starting fuzzy matching between {len(rankings)} ranking wards and {len(pop_data)} population wards")
        
        # Get unique ward names from both datasets
        ranking_ward_names = rankings['WardName'].unique().tolist()
        pop_ward_names = pop_data['WardName'].unique().tolist()
        
        # Perform fuzzy matching
        matches = fuzzy_match_ward_names(ranking_ward_names, pop_ward_names, threshold=75)
        
        # Create a mapping dataframe
        match_df = pd.DataFrame([
            {'WardName': analysis_ward, 'PopWardName': pop_ward, 'MatchScore': score}
            for analysis_ward, (pop_ward, score) in matches.items()
        ])
        
        # Log matching results
        logger.info(f"Fuzzy matching results: {len(matches)} out of {len(ranking_ward_names)} wards matched")
        if len(match_df) > 0:
            avg_score = match_df['MatchScore'].mean()
            logger.info(f"Average match score: {avg_score:.1f}")
            
            # Show some examples of matches
            examples = match_df.nlargest(5, 'MatchScore').head(3)
            for _, row in examples.iterrows():
                logger.info(f"  '{row['WardName']}' -> '{row['PopWardName']}' (score: {row['MatchScore']})")
        
        # Merge the matching results back to rankings
        rankings = rankings.merge(match_df, on='WardName', how='left')
        
        # Now merge with population data using the matched names
        # Rename population ward column for merging
        pop_data_renamed = pop_data.rename(columns={'WardName': 'PopWardName'})
        
        # Merge population data
        rankings = rankings.merge(
            pop_data_renamed[['PopWardName', 'Population']],
            on='PopWardName',
            how='left'
        )
        
        
        # Check if we have any matches
        matched_count = rankings['Population'].notna().sum()
        logger.info(f"Matched population data for {matched_count} out of {len(rankings)} wards")
        
        # If no matches, try to understand why
        if matched_count == 0:
            logger.warning(f"No matches found. Checking for common ward names...")
            rankings_wards = set(rankings['WardName'].str.lower())
            pop_wards = set(pop_data['WardName'].str.lower())
            common_wards = rankings_wards.intersection(pop_wards)
            logger.warning(f"Common ward names: {len(common_wards)} - {list(common_wards)[:5]}")
        
        # Remove wards without population data
        rankings = rankings[rankings['Population'].notna()]
        
        if len(rankings) == 0:
            return {'status': 'error', 'message': 'No ward names matched between ranking data and population data. Please check ward name consistency.'}
    else:
        # Get list of available states
        loader = get_population_loader()
        available_states = loader.get_available_states()
        if available_states:
            states_list = ', '.join(available_states)
            return {'status': 'error', 'message': f'Population data not available for {state}. Available states with population data: {states_list}'}
        else:
            return {'status': 'error', 'message': f'Population data not available for {state}. No population data files found in the system.'}
    
    # FULL COVERAGE STRATEGY: Give 100% coverage to highest risk wards until nets run out
    # Handle both 'UrbanPercent' and 'urbanPercentage' column names
    urban_col = 'UrbanPercent' if 'UrbanPercent' in rankings.columns else 'urbanPercentage'
    if urban_col not in rankings.columns:
        logger.warning(f"No urban percentage column found. Available columns: {rankings.columns.tolist()}")
        # Use a default value if urban percentage is not available
        rankings['urban_pct'] = 50.0  # Default to 50% urban
        urban_col = 'urban_pct'
    
    # Sort ALL wards by risk rank (highest risk first)
    rankings_sorted = rankings.sort_values('overall_rank')
    rankings_sorted['nets_needed'] = rankings_sorted['Population'].apply(lambda p: calculate_nets_needed(p, avg_household_size))
    
    # Allocate nets - full coverage to each ward until we run out
    allocated = 0
    wards_with_allocation = []
    
    for idx, row in rankings_sorted.iterrows():
        nets_for_this_ward = row['nets_needed']
        
        # Can we fully cover this ward?
        if allocated + nets_for_this_ward <= total_nets:
            # Yes - give full coverage
            row_copy = row.copy()
            row_copy['nets_allocated'] = nets_for_this_ward
            row_copy['coverage_percent'] = 100.0
            row_copy['allocation_phase'] = 'Full Coverage'
            wards_with_allocation.append(row_copy)
            allocated += nets_for_this_ward
            logger.info(f"Allocated {nets_for_this_ward} nets to {row['WardName']} (rank {row['overall_rank']}, pop {row['Population']:.0f})")
        else:
            # No more full coverage possible
            remaining = total_nets - allocated
            if remaining > 0:
                # Give partial coverage to this last ward
                row_copy = row.copy()
                row_copy['nets_allocated'] = remaining
                row_copy['coverage_percent'] = (remaining / nets_for_this_ward) * 100
                row_copy['allocation_phase'] = 'Partial Coverage (Last Ward)'
                wards_with_allocation.append(row_copy)
                allocated = total_nets
                logger.info(f"Allocated remaining {remaining} nets to {row['WardName']} ({row_copy['coverage_percent']:.1f}% coverage)")
            break
    
    # Create the prioritized dataframe from wards that got allocations
    if wards_with_allocation:
        prioritized = pd.DataFrame(wards_with_allocation)
        # Separate rural vs urban for stats
        prioritized_rural = prioritized[prioritized[urban_col] < urban_threshold]
        prioritized_urban = prioritized[prioritized[urban_col] >= urban_threshold]
    else:
        prioritized = pd.DataFrame()
        prioritized_rural = pd.DataFrame()
        prioritized_urban = pd.DataFrame()
    
    # No reprioritized phase in full coverage strategy
    reprioritized = pd.DataFrame()
    
    # Calculate total allocated nets
    total_allocated = prioritized['nets_allocated'].sum()
    if not reprioritized.empty:
        total_allocated += reprioritized['nets_allocated'].sum()
    
    # Calculate population coverage
    total_population = rankings['Population'].sum()
    prioritized['population_covered'] = prioritized['nets_allocated'] * 1.8  # 1 net covers 1.8 people
    covered_population = prioritized['population_covered'].sum()
    
    if not reprioritized.empty:
        reprioritized['population_covered'] = reprioritized['nets_allocated'] * 1.8
        covered_population += reprioritized['population_covered'].sum()
    
    # Convert any datetime columns to strings to avoid JSON serialization issues
    for df in [prioritized, reprioritized]:
        if not df.empty:
            for col in df.select_dtypes(include=['datetime64']).columns:
                df[col] = df[col].astype(str)
    
    # Stats - updated for full coverage strategy
    fully_covered_wards = len(prioritized[prioritized['coverage_percent'] == 100.0]) if not prioritized.empty else 0
    partially_covered_wards = len(prioritized[prioritized['coverage_percent'] < 100.0]) if not prioritized.empty else 0
    
    # Add ward coverage statistics
    ward_coverage_stats = {}
    if not prioritized.empty:
        ward_coverage_stats = {
            'avg_coverage_percent': round(prioritized['coverage_percent'].mean(), 1),
            'min_coverage_percent': round(prioritized['coverage_percent'].min(), 1),
            'max_coverage_percent': round(prioritized['coverage_percent'].max(), 1)
        }
    
    stats = {
        'total_nets': total_nets,
        'allocated': int(total_allocated),
        'remaining': int(total_nets - total_allocated),
        'coverage_percent': round((covered_population / total_population) * 100, 1) if total_population > 0 else 0,
        'prioritized_wards': len(prioritized),
        'fully_covered_wards': fully_covered_wards,
        'partially_covered_wards': partially_covered_wards,
        'reprioritized_wards': 0,  # No longer used in full coverage strategy
        'total_population': int(total_population),
        'covered_population': int(covered_population),
        'ward_coverage_stats': ward_coverage_stats
    }
    
    # Generate map
    map_path = generate_itn_map(shp_data, prioritized, reprioritized, 
                               session_id=session_id, urban_threshold=urban_threshold, 
                               total_nets=total_nets, avg_household_size=avg_household_size, 
                               method=method, stats=stats)
    
    # Save results for export (modular addition - doesn't affect existing functionality)
    try:
        results_to_save = {
            'status': 'success',
            'stats': stats,
            'method': method,
            'urban_threshold': urban_threshold,
            'avg_household_size': avg_household_size,
            'total_nets': total_nets,
            'timestamp': datetime.now().isoformat(),
            'prioritized': prioritized.to_dict('records'),
            'reprioritized': reprioritized.to_dict('records') if not reprioritized.empty else [],
            'map_path': map_path
        }
        
        # Save to session folder
        results_path = f"instance/uploads/{session_id}/itn_distribution_results.json"
        with open(results_path, 'w') as f:
            json.dump(results_to_save, f, indent=2, default=str)
        logger.info(f"Saved ITN distribution results to {results_path}")
    except Exception as e:
        logger.warning(f"Failed to save ITN results for export: {e}")
        # Don't fail the main function if saving fails
    
    return {
        'status': 'success',
        'stats': stats,
        'prioritized': prioritized,
        'reprioritized': reprioritized,
        'map_path': map_path
    }

def generate_itn_map(shp_data: gpd.GeoDataFrame, prioritized: pd.DataFrame, reprioritized: pd.DataFrame, 
                     session_id: str, urban_threshold: float = 30.0, total_nets: int = 10000, 
                     avg_household_size: float = 5.0, method: str = 'composite', stats: Dict[str, Any] = None) -> str:
    """Generate interactive Plotly map for ITN distribution with threshold info."""
    # Ensure we have the visualization directory
    os.makedirs('app/static/visualizations', exist_ok=True)
    
    # Merge allocation data with shapefile for visualization - deep copy to avoid modifying original
    shp_data = shp_data.copy(deep=True)
    
    # Ensure shp_data is a proper GeoDataFrame
    if not isinstance(shp_data, gpd.GeoDataFrame):
        logger.error("shp_data is not a GeoDataFrame!")
        return None
    
    # Add lowercase column for merging
    shp_data['WardName_lower'] = shp_data['WardName'].str.lower()
    prioritized['WardName_lower'] = prioritized['WardName'].str.lower()
    
    # Merge prioritized allocations - GeoDataFrame.merge preserves geometry automatically
    shp_data = shp_data.merge(
        prioritized[['WardName_lower', 'nets_allocated', 'nets_needed', 'Population']],
        on='WardName_lower',
        how='left',
        suffixes=('', '_prioritized')
    )
    
    # Track allocation phase for hover text - using new full coverage strategy
    shp_data['allocation_phase'] = ''
    
    # Get allocation phase and coverage info from prioritized data
    if not prioritized.empty and 'allocation_phase' in prioritized.columns:
        # Merge with allocation phase and coverage percent from prioritized
        phase_cols = ['WardName_lower', 'allocation_phase']
        if 'coverage_percent' in prioritized.columns:
            phase_cols.append('coverage_percent')
        
        phase_data = prioritized[phase_cols].copy()
        shp_data = shp_data.merge(
            phase_data,
            on='WardName_lower',
            how='left',
            suffixes=('', '_from_prioritized')
        )
        
        # Use the allocation phase from prioritized data
        if 'allocation_phase_from_prioritized' in shp_data.columns:
            shp_data['allocation_phase'] = shp_data['allocation_phase_from_prioritized'].fillna('')
            shp_data = shp_data.drop(columns=['allocation_phase_from_prioritized'])
        
        # Use coverage percent from prioritized if available
        if 'coverage_percent_from_prioritized' in shp_data.columns:
            shp_data['coverage_percent'] = shp_data['coverage_percent_from_prioritized'].fillna(0)
            shp_data = shp_data.drop(columns=['coverage_percent_from_prioritized'])
    else:
        # Fallback logic
        shp_data.loc[shp_data['WardName_lower'].isin(prioritized['WardName_lower']), 'allocation_phase'] = 'Allocated'
    
    # Mark unallocated wards
    shp_data.loc[(shp_data['allocation_phase'] == '') & (shp_data['nets_allocated'] == 0), 'allocation_phase'] = 'Not Allocated'
    
    # Fill NaN values
    shp_data['nets_allocated'] = shp_data['nets_allocated'].fillna(0)
    
    # Only calculate coverage_percent if not already set from prioritized data
    if 'coverage_percent' not in shp_data.columns or shp_data['coverage_percent'].isna().all():
        shp_data['coverage_percent'] = (shp_data['nets_allocated'] * 1.8 / shp_data['Population'] * 100).fillna(0)
        shp_data['coverage_percent'] = shp_data['coverage_percent'].clip(upper=100)
    else:
        # For wards without coverage_percent, calculate it
        no_coverage_mask = shp_data['coverage_percent'].isna() | (shp_data['coverage_percent'] == 0)
        shp_data.loc[no_coverage_mask, 'coverage_percent'] = (
            shp_data.loc[no_coverage_mask, 'nets_allocated'] * 1.8 / 
            shp_data.loc[no_coverage_mask, 'Population'] * 100
        ).fillna(0).clip(upper=100)
    
    # Add urban percentage info for hover text
    # Get urban percentage from the original data
    if 'UrbanPercent' in shp_data.columns:
        shp_data['urban_pct_display'] = shp_data['UrbanPercent']
    elif 'urbanPercentage' in shp_data.columns:
        shp_data['urban_pct_display'] = shp_data['urbanPercentage']
    else:
        # Try to get from the prioritized data
        if 'UrbanPercent' in prioritized.columns:
            urban_col = 'UrbanPercent'
        elif 'urbanPercentage' in prioritized.columns:
            urban_col = 'urbanPercentage' 
        else:
            urban_col = None
            
        if urban_col:
            urban_data = prioritized[['WardName', urban_col]].copy()
            urban_data['WardName_lower'] = urban_data['WardName'].str.lower()
            shp_data = shp_data.merge(
                urban_data[['WardName_lower', urban_col]],
                on='WardName_lower',
                how='left',
                suffixes=('', '_from_prioritized')
            )
            # Also get from reprioritized if available
            if not reprioritized.empty and urban_col in reprioritized.columns:
                urban_data_repri = reprioritized[['WardName', urban_col]].copy()
                urban_data_repri['WardName_lower'] = urban_data_repri['WardName'].str.lower()
                shp_data = shp_data.merge(
                    urban_data_repri[['WardName_lower', urban_col]],
                    on='WardName_lower',
                    how='left',
                    suffixes=('', '_from_reprioritized')
                )
                # Combine both sources
                shp_data['urban_pct_display'] = shp_data[urban_col].fillna(shp_data[urban_col + '_from_reprioritized'])
            else:
                shp_data['urban_pct_display'] = shp_data[urban_col]
        else:
            shp_data['urban_pct_display'] = np.nan
    
    # Ensure we have valid geometry data
    if 'geometry' not in shp_data.columns:
        logger.error("No geometry column found in shapefile data after merging!")
        return None
    
    # Remove any rows with invalid geometry
    shp_data = shp_data[shp_data['geometry'].notna()]
    if len(shp_data) == 0:
        logger.error("No valid geometries found in shapefile data!")
        return None
    
    # Get map center from shapefile bounds
    bounds = shp_data.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # Log some debugging info
    logger.info(f"Creating ITN map with {len(shp_data)} wards")
    logger.info(f"Nets allocated range: {shp_data['nets_allocated'].min()} to {shp_data['nets_allocated'].max()}")
    logger.info(f"Map center: lat={center_lat}, lon={center_lon}")
    
    # Convert any datetime/timestamp columns to strings to avoid JSON serialization issues
    for col in shp_data.columns:
        if col == 'geometry':
            continue  # Skip geometry column
        
        # Check for datetime columns using pandas API
        if is_datetime64_any_dtype(shp_data[col]):
            logger.info(f"Converting datetime column '{col}' to string for JSON serialization")
            shp_data[col] = shp_data[col].astype(str)
        elif shp_data[col].dtype == 'object':
            # Check if object column contains timestamp objects
            try:
                sample_vals = shp_data[col].dropna()
                if len(sample_vals) > 0:
                    sample_val = sample_vals.iloc[0]
                    # More comprehensive timestamp detection
                    if (hasattr(sample_val, 'timestamp') or 
                        'Timestamp' in str(type(sample_val)) or
                        isinstance(sample_val, pd.Timestamp) or
                        str(type(sample_val)) == "<class 'pandas._libs.tslibs.timestamps.Timestamp'>"):
                        logger.info(f"Converting timestamp column '{col}' to string for JSON serialization")
                        shp_data[col] = shp_data[col].astype(str)
            except Exception as e:
                logger.debug(f"Error checking column '{col}': {e}")
                # If any error, convert to string to be safe
                try:
                    shp_data[col] = shp_data[col].astype(str)
                except:
                    pass
    
    # Create plotly figure
    fig = go.Figure()
    
    # Filter out null geometries before creating map
    valid_geometry_mask = ~shp_data.geometry.isnull()
    shp_data_valid = shp_data[valid_geometry_mask].copy()
    
    if len(shp_data_valid) == 0:
        logger.error("No valid geometries found in shapefile data")
        return None
    
    # Create separate traces for covered and uncovered areas for better visual distinction
    covered_mask = shp_data_valid['nets_allocated'] > 0
    uncovered_mask = shp_data_valid['nets_allocated'] == 0
    
    # Add uncovered areas first (so they appear behind covered areas)
    if uncovered_mask.any():
        uncovered_data = shp_data_valid[uncovered_mask]
        fig.add_trace(go.Choroplethmapbox(
            geojson=uncovered_data.geometry.__geo_interface__,
            locations=uncovered_data.index,
            z=[0] * len(uncovered_data),  # All zeros for consistent gray color
            colorscale=[[0, '#f0f0f0'], [1, '#f0f0f0']],  # Light gray
            text=uncovered_data['WardName'],
            hovertemplate='<b>%{text}</b><br>' +
                          '─────────────────<br>' +
                          '<b>Status:</b> No nets allocated<br>' +
                          '<b>Urban %:</b> %{customdata[3]:.1f}%<br>' +
                          '<b>Population:</b> %{customdata[0]:,.0f}<br>' +
                          '<extra></extra>',
            customdata=np.column_stack((
                uncovered_data['Population'].fillna(0),
                uncovered_data['coverage_percent'],
                uncovered_data['allocation_phase'],
                uncovered_data['urban_pct_display'].fillna(0)
            )),
            marker_opacity=0.3,  # Much lower opacity for uncovered areas
            marker_line_width=0.5,
            marker_line_color='#cccccc',
            showscale=False,
            name='No Allocation'
        ))
    
    # Add covered areas with prominent colors
    if covered_mask.any():
        covered_data = shp_data_valid[covered_mask]
        fig.add_trace(go.Choroplethmapbox(
            geojson=covered_data.geometry.__geo_interface__,
            locations=covered_data.index,
            z=covered_data['nets_allocated'],
            colorscale='Plasma',  # Purple to Pink to Yellow
            reversescale=False,   # Yellow for high allocation
            text=covered_data['WardName'],
            hovertemplate='<b>%{text}</b><br>' +
                          '─────────────────<br>' +
                          '<b>Allocation Status:</b> %{customdata[2]}<br>' +
                          '<b>Urban %:</b> %{customdata[3]:.1f}%<br>' +
                          '<b>Threshold:</b> ' + str(urban_threshold) + '%<br>' +
                          '─────────────────<br>' +
                          '<b>Nets Allocated:</b> %{z:,.0f}<br>' +
                          '<b>Population:</b> %{customdata[0]:,.0f}<br>' +
                          '<b>Coverage:</b> %{customdata[1]:.1f}%<br>' +
                          '<extra></extra>',
            customdata=np.column_stack((
                covered_data['Population'].fillna(0),
                covered_data['coverage_percent'],
                covered_data['allocation_phase'],
                covered_data['urban_pct_display'].fillna(0)
            )),
            marker_opacity=0.9,  # High opacity for covered areas
            marker_line_width=1.5,
            marker_line_color='white',
            showscale=True,
            colorbar=dict(
                title="Nets<br>Allocated",
                thickness=15,
                len=0.7,
                x=0.98,
                y=0.5
            ),
            name='Allocated'
        ))
    
    # Add annotations for threshold info
    annotations = [
        dict(
            text=f"<b>Allocation Strategy</b><br>" +
                 f"<b>Phase 1:</b> Rural wards (urban < {urban_threshold}%) get 100% coverage<br>" +
                 f"<b>Phase 2:</b> Remaining nets go to urban wards (urban ≥ {urban_threshold}%)<br>" +
                 f"<i>Hover over wards to see their allocation phase</i>",
            showarrow=False,
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            xanchor="left", yanchor="top",
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="black",
            borderwidth=1,
            font=dict(size=11)
        ),
        dict(
            text=f"<b>Distribution Summary</b><br>" +
                 f"Total Nets: {total_nets:,}<br>" +
                 f"Allocated: {stats['allocated']:,}<br>" +
                 f"Coverage: {stats['coverage_percent']}%" if stats else f"Total Nets: {total_nets:,}",
            showarrow=False,
            xref="paper", yref="paper",
            x=0.98, y=0.98,
            xanchor="right", yanchor="top",
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="black",
            borderwidth=1,
            font=dict(size=11)
        )
    ]
    
    # Update layout
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=8,
            bearing=0,
            pitch=0
        ),
        margin={"r": 0, "t": 60, "l": 0, "b": 0},
        title=dict(
            text=f"ITN Distribution Plan<br><sub>Highlighted areas receive bed nets | Faded areas have no allocation</sub>",
            x=0.5,
            xanchor='center',
            font=dict(size=18)
        ),
        height=700,
        annotations=annotations,
        showlegend=False
    )
    
    # Save map in session folder for better organization
    # Create visualizations directory if it doesn't exist
    viz_dir = f'instance/uploads/{session_id}/visualizations'
    os.makedirs(viz_dir, exist_ok=True)
    
    # Save map in session visualizations folder
    filename = f'itn_distribution_map_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    path = os.path.join(viz_dir, filename)
    
    # First save the figure normally
    fig.write_html(path, include_plotlyjs='cdn')
    
    # Then add the threshold control by modifying the saved HTML
    with open(path, 'r') as f:
        html_content = f.read()
    
    # Add custom CSS for threshold control
    custom_css = """
        <style>
            .threshold-control {
                position: absolute;
                top: 80px;
                left: 20px;
                background: rgba(255, 255, 255, 0.9);
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                z-index: 1000;
            }
            .threshold-control input {
                width: 60px;
                padding: 5px;
                margin: 0 10px;
            }
            .threshold-control button {
                background: #1f77b4;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                cursor: pointer;
            }
            .threshold-control button:hover {
                background: #1a5490;
            }
        </style>
    """
    
    # Add threshold control HTML
    threshold_control = f"""
        <div class="threshold-control">
            <label><b>Urban Threshold:</b></label>
            <input type="number" id="thresholdInput" value="{urban_threshold}" min="0" max="100" step="5">%
            <button onclick="updateThreshold()">Update</button>
        </div>
    """
    
    # Add update function
    update_script = f"""
        <script>
            function updateThreshold() {{
                var newThreshold = document.getElementById('thresholdInput').value;
                var button = event.target;
                button.disabled = true;
                button.textContent = 'Updating...';
                
                // Call backend API to update distribution
                fetch('/api/itn/update-distribution', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        urban_threshold: parseFloat(newThreshold),
                        total_nets: {total_nets},
                        avg_household_size: {avg_household_size},
                        method: '{method}'
                    }})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.status === 'success') {{
                        // Reload page with new map
                        window.location.reload();
                    }} else {{
                        alert('Error: ' + data.message);
                        button.disabled = false;
                        button.textContent = 'Update';
                    }}
                }})
                .catch(error => {{
                    alert('Error updating distribution: ' + error);
                    button.disabled = false;
                    button.textContent = 'Update';
                }});
            }}
        </script>
    """
    
    # Insert custom elements into the HTML
    html_content = html_content.replace('</head>', custom_css + '</head>')
    html_content = html_content.replace('<body>', '<body>' + threshold_control)
    html_content = html_content.replace('</body>', update_script + '</body>')
    
    # Write the modified HTML back
    with open(path, 'w') as f:
        f.write(html_content)
    
    # Return path to serve the file
    return f'/serve_viz_file/{session_id}/visualizations/{filename}'