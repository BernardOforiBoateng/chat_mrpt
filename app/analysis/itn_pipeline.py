"""ITN Distribution Pipeline for ChatMRPT."""
import logging
import pandas as pd
import geopandas as gpd
import numpy as np
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import plotly.graph_objects as go
from pandas.api.types import is_datetime64_any_dtype
from app.data.population_data.itn_population_loader import get_population_loader

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
    
    # Check CSV data as fallback
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
    
    # Log warning and return default
    logger.warning("Could not detect state from data, defaulting to 'Kano'")
    return 'Kano'  # Default to Kano since that's most common in the system

def load_population_data(state: str) -> Optional[pd.DataFrame]:
    """Load and aggregate population data for the state."""
    loader = get_population_loader()
    
    # Try new format first
    pop_df = loader.load_state_population(state, use_new_format=True)
    
    if pop_df is not None:
        # New format data is already clean with Ward, LGA, Population
        logger.info(f"Using new cleaned population data for {state}")
        
        # Create output format matching old function's return
        ward_population = pop_df.copy()
        ward_population.columns = ['WardName', 'AdminLevel2', 'Population']
        
        # Add dummy coordinates for now (will be matched from shapefile)
        ward_population['AvgLatitude'] = np.nan
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
        # Extract original ward name from "WardName (WardCode)" format for duplicates
        rankings['WardName_original'] = rankings['WardName'].str.replace(r'\s*\([A-Z]{2}\d+\)$', '', regex=True)
        rankings['WardName_original_lower'] = rankings['WardName_original'].str.lower()
        
        # Identify which ward names have duplicates in rankings
        ward_counts = rankings.groupby('WardName_original')['WardName'].count()
        duplicate_ward_names = set(ward_counts[ward_counts > 1].index)
        
        # Also check which ward names have duplicates in population data
        pop_ward_counts = pop_data.groupby('WardName')['AdminLevel2'].count()
        pop_duplicate_names = set(pop_ward_counts[pop_ward_counts > 1].index)
        
        # Ward names that need coordinate matching (duplicates in either dataset)
        needs_coord_matching = duplicate_ward_names | pop_duplicate_names
        logger.info(f"Ward names needing coordinate matching: {len(needs_coord_matching)}")
        
        # Split rankings into two groups
        needs_coords_mask = rankings['WardName_original'].isin(needs_coord_matching)
        unique_wards = rankings[~needs_coords_mask].copy()
        duplicate_wards = rankings[needs_coords_mask].copy()
        
        logger.info(f"Matching strategy: {len(unique_wards)} unique wards (simple match), {len(duplicate_wards)} duplicate wards (coordinate match)")
        
        # 1. Simple matching for unique ward names
        if len(unique_wards) > 0:
            # Get population data for unique wards only
            pop_unique = pop_data[~pop_data['WardName'].isin(pop_duplicate_names)]
            
            unique_wards = unique_wards.merge(
                pop_unique[['WardName_lower', 'Population']],
                left_on='WardName_original_lower',
                right_on='WardName_lower',
                how='left'
            )
            
            # Handle known spelling variations for unmatched wards
            spelling_map = {
                'jauben kudu': 'jaube',
                'rigar duka': 'rugar duka'
            }
            
            for idx, row in unique_wards[unique_wards['Population'].isna()].iterrows():
                ward_lower = row['WardName_original_lower']
                if ward_lower in spelling_map:
                    alt_spelling = spelling_map[ward_lower]
                    pop_match = pop_unique[pop_unique['WardName_lower'] == alt_spelling]
                    if len(pop_match) > 0:
                        unique_wards.at[idx, 'Population'] = pop_match.iloc[0]['Population']
                        logger.info(f"Fuzzy matched: '{row['WardName']}' -> '{alt_spelling}'")
            
            unique_matched = unique_wards['Population'].notna().sum()
            logger.info(f"Simple matching: {unique_matched}/{len(unique_wards)} unique wards matched")
        
        # 2. Coordinate-based matching for duplicate ward names
        if len(duplicate_wards) > 0 and hasattr(data_handler, 'unified_dataset') and 'centroid_lat' in data_handler.unified_dataset.columns:
            # Get coordinates from unified dataset
            coord_info = data_handler.unified_dataset[['WardName', 'centroid_lat', 'centroid_lon']].copy()
            duplicate_wards = duplicate_wards.merge(coord_info, on='WardName', how='left')
            
            # Match each duplicate ward to nearest population ward
            duplicate_wards['Population'] = np.nan
            duplicate_wards['matched_pop_ward'] = ''
            duplicate_wards['match_distance_km'] = np.nan
            
            for idx, ward_row in duplicate_wards.iterrows():
                if pd.notna(ward_row['centroid_lat']) and pd.notna(ward_row['centroid_lon']):
                    # Get all population wards with same name
                    pop_candidates = pop_data[pop_data['WardName'].str.lower() == ward_row['WardName_original_lower']]
                    
                    if len(pop_candidates) > 0:
                        # Calculate distances to all candidates
                        distances = []
                        for _, pop_row in pop_candidates.iterrows():
                            if pd.notna(pop_row['AvgLatitude']) and pd.notna(pop_row['AvgLongitude']):
                                dist = haversine_distance(
                                    ward_row['centroid_lat'], ward_row['centroid_lon'],
                                    pop_row['AvgLatitude'], pop_row['AvgLongitude']
                                )
                                distances.append((dist, pop_row))
                        
                        if distances:
                            # Find nearest match
                            distances.sort(key=lambda x: x[0])
                            nearest_dist, nearest_pop = distances[0]
                            
                            # Accept match if within threshold (5km for most, 15km for Falgore special case)
                            threshold = 15.0 if 'falgore' in ward_row['WardName_original_lower'] else 5.0
                            if nearest_dist <= threshold:
                                duplicate_wards.at[idx, 'Population'] = nearest_pop['Population']
                                duplicate_wards.at[idx, 'matched_pop_ward'] = f"{nearest_pop['WardName']} ({nearest_pop['AdminLevel2']})"
                                duplicate_wards.at[idx, 'match_distance_km'] = nearest_dist
            
            coord_matched = duplicate_wards['Population'].notna().sum()
            logger.info(f"Coordinate matching: {coord_matched}/{len(duplicate_wards)} duplicate wards matched")
            
            # Log some examples of coordinate matches
            matched_examples = duplicate_wards[duplicate_wards['Population'].notna()].head(3)
            for _, ex in matched_examples.iterrows():
                logger.info(f"  {ex['WardName']} -> {ex['matched_pop_ward']} ({ex['match_distance_km']:.2f} km)")
        
        # Combine results
        if len(unique_wards) > 0 and len(duplicate_wards) > 0:
            rankings = pd.concat([unique_wards, duplicate_wards], ignore_index=True)
        elif len(unique_wards) > 0:
            rankings = unique_wards
        else:
            rankings = duplicate_wards
        
        # Calculate total matches
        total_matched = rankings['Population'].notna().sum()
        logger.info(f"Total matched: {total_matched}/{len(rankings)} ({(total_matched/len(rankings)*100):.1f}%)")
        
        # Log unmatched wards
        unmatched = rankings[rankings['Population'].isna()]['WardName'].tolist()
        if unmatched:
            logger.warning(f"Unmatched wards ({len(unmatched)}): {unmatched[:5]}...")
        
        # Drop helper columns
        cols_to_drop = ['WardName_lower', 'WardName_original', 'WardName_original_lower', 
                        'centroid_lat', 'centroid_lon', 'matched_pop_ward', 'match_distance_km']
        rankings = rankings.drop(columns=[col for col in cols_to_drop if col in rankings.columns])
        
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
        return {'status': 'error', 'message': 'Population data not available for this state. Please provide it or choose a supported state.'}
    
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
    
    # Add choropleth layer - use geometry.__geo_interface__ like working maps
    fig.add_trace(go.Choroplethmapbox(
        geojson=shp_data_valid.geometry.__geo_interface__,
        locations=shp_data_valid.index,
        z=shp_data_valid['nets_allocated'],
        colorscale='RdYlGn',  # Red to Yellow to Green
        reversescale=True,    # Green for high allocation
        text=shp_data_valid['WardName'],
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
            shp_data_valid['Population'].fillna(0),
            shp_data_valid['coverage_percent'],
            shp_data_valid['allocation_phase'],
            shp_data_valid['urban_pct_display'].fillna(0)
        )),
        marker_opacity=0.7,
        marker_line_width=1,
        marker_line_color='white',
        showscale=True,
        colorbar=dict(
            title="Nets<br>Allocated",
            thickness=15,
            len=0.7,
            x=0.98,
            y=0.5
        )
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
            text=f"ITN Distribution Plan<br><sub>Areas with urban percentage < {urban_threshold}% are prioritized</sub>",
            x=0.5,
            xanchor='center',
            font=dict(size=18)
        ),
        height=700,
        annotations=annotations,
        showlegend=False
    )
    
    # Save map properly using fig.write_html like working maps
    path = f'app/static/visualizations/itn_map_{session_id}.html'
    
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
    
    # Return web path
    return f'/static/visualizations/itn_map_{session_id}.html'