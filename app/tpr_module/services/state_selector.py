"""
State Selector Service for TPR Module.

This service handles state selection with fuzzy matching and 
extraction of state-specific data from the master Nigerian shapefile.
"""

import os
import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from difflib import get_close_matches
import json

logger = logging.getLogger(__name__)

class StateSelector:
    """Handle state selection and data extraction."""
    
    def __init__(self, shapefile_path: str = None):
        """
        Initialize the state selector.
        
        Args:
            shapefile_path: Path to master Nigerian shapefile
        """
        if shapefile_path is None:
            # Look for Nigerian shapefile in common locations
            possible_paths = [
                'www/ward_shape.shp',
                'instance/uploads/ward_shape.shp',
                'app/sample_data/nigeria_wards.shp'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    shapefile_path = path
                    break
            
            if shapefile_path is None:
                logger.warning("No Nigerian shapefile found in default locations")
        
        self.shapefile_path = shapefile_path
        self.shapefile_data = None
        self.states_available = []
        self.state_mapping = {}
        
        # Initialize if shapefile provided
        if self.shapefile_path and os.path.exists(self.shapefile_path):
            self._load_shapefile()
    
    def _load_shapefile(self):
        """Load and analyze the master shapefile."""
        try:
            logger.info(f"Loading shapefile from: {self.shapefile_path}")
            self.shapefile_data = gpd.read_file(self.shapefile_path)
            
            # Identify state column
            state_column = self._identify_state_column()
            
            if state_column:
                # Extract unique states
                self.states_available = sorted(
                    self.shapefile_data[state_column].dropna().unique().tolist()
                )
                
                # Create normalized mapping for fuzzy matching
                for state in self.states_available:
                    normalized = self._normalize_state_name(state)
                    self.state_mapping[normalized] = state
                
                logger.info(f"Loaded {len(self.states_available)} states from shapefile")
            else:
                logger.warning("Could not identify state column in shapefile")
                
        except Exception as e:
            logger.error(f"Error loading shapefile: {str(e)}")
    
    def _identify_state_column(self) -> Optional[str]:
        """Identify which column contains state names."""
        if self.shapefile_data is None:
            return None
        
        # Common state column names
        possible_columns = [
            'State', 'STATE', 'state', 'StateName', 'state_name',
            'Admin1', 'admin1', 'ADM1_EN', 'NAME_1'
        ]
        
        for col in possible_columns:
            if col in self.shapefile_data.columns:
                # Check if it contains state-like values
                values = self.shapefile_data[col].dropna().unique()
                if len(values) >= 20 and len(values) <= 50:  # Nigeria has 36 states + FCT
                    return col
        
        # If not found, try to identify by content
        for col in self.shapefile_data.columns:
            if self.shapefile_data[col].dtype == 'object':
                values = self.shapefile_data[col].dropna().unique()
                # Check if values look like Nigerian states
                if any('Lagos' in str(v) or 'Kano' in str(v) for v in values):
                    if len(values) >= 20 and len(values) <= 50:
                        return col
        
        return None
    
    def _normalize_state_name(self, state_name: str) -> str:
        """Normalize state name for matching."""
        if not state_name:
            return ""
        
        # Convert to string and clean
        normalized = str(state_name).strip().upper()
        
        # Remove common suffixes
        normalized = normalized.replace(' STATE', '')
        normalized = normalized.replace(' ST', '')
        normalized = normalized.replace(' ST.', '')
        
        # Handle FCT special case
        if 'FEDERAL CAPITAL' in normalized or 'FCT' in normalized:
            normalized = 'FCT'
        
        return normalized
    
    def get_available_states(self) -> List[str]:
        """Get list of available states."""
        return self.states_available.copy()
    
    def match_state(self, user_input: str) -> Tuple[Optional[str], float]:
        """
        Match user input to available state names.
        
        Args:
            user_input: User's state input
            
        Returns:
            Tuple of (matched_state, confidence_score)
        """
        if not user_input:
            return None, 0.0
        
        # Normalize input
        normalized_input = self._normalize_state_name(user_input)
        
        # Exact match
        if normalized_input in self.state_mapping:
            return self.state_mapping[normalized_input], 1.0
        
        # Fuzzy match
        matches = get_close_matches(
            normalized_input, 
            self.state_mapping.keys(), 
            n=1, 
            cutoff=0.6
        )
        
        if matches:
            matched_normalized = matches[0]
            # Calculate simple similarity score
            score = len(set(normalized_input) & set(matched_normalized)) / \
                   max(len(normalized_input), len(matched_normalized))
            return self.state_mapping[matched_normalized], score
        
        return None, 0.0
    
    def extract_state_data(self, state_name: str) -> Optional[gpd.GeoDataFrame]:
        """
        Extract data for a specific state.
        
        Args:
            state_name: Name of the state
            
        Returns:
            GeoDataFrame with state data or None
        """
        if self.shapefile_data is None:
            logger.error("No shapefile loaded")
            return None
        
        state_column = self._identify_state_column()
        if not state_column:
            logger.error("Could not identify state column")
            return None
        
        # Filter for state
        state_data = self.shapefile_data[
            self.shapefile_data[state_column].str.contains(
                state_name, case=False, na=False
            )
        ].copy()
        
        if state_data.empty:
            # Try normalized matching
            normalized = self._normalize_state_name(state_name)
            for idx, row in self.shapefile_data.iterrows():
                if self._normalize_state_name(row[state_column]) == normalized:
                    state_data = self.shapefile_data.iloc[[idx]].copy()
                    break
        
        if not state_data.empty:
            logger.info(f"Extracted {len(state_data)} wards for {state_name}")
            return state_data
        else:
            logger.warning(f"No data found for state: {state_name}")
            return None
    
    def get_state_metadata(self, state_name: str) -> Dict[str, Any]:
        """
        Get metadata about a state.
        
        Args:
            state_name: Name of the state
            
        Returns:
            Dictionary with state metadata
        """
        state_data = self.extract_state_data(state_name)
        
        if state_data is None or state_data.empty:
            return {
                'state': state_name,
                'found': False
            }
        
        # Extract metadata
        metadata = {
            'state': state_name,
            'found': True,
            'ward_count': len(state_data),
            'lga_count': 0,
            'bounds': None,
            'area_km2': None
        }
        
        # Count LGAs if column exists
        lga_columns = ['LGA', 'lga', 'LGAName', 'lga_name', 'LGA_NAME']
        for col in lga_columns:
            if col in state_data.columns:
                metadata['lga_count'] = state_data[col].nunique()
                break
        
        # Get bounds
        try:
            bounds = state_data.total_bounds  # minx, miny, maxx, maxy
            metadata['bounds'] = {
                'min_lon': bounds[0],
                'min_lat': bounds[1],
                'max_lon': bounds[2],
                'max_lat': bounds[3]
            }
        except:
            pass
        
        # Calculate area
        try:
            # Project to equal area projection for Nigeria
            state_data_proj = state_data.to_crs('EPSG:26392')  # Nigeria West Belt
            metadata['area_km2'] = state_data_proj.geometry.area.sum() / 1_000_000
        except:
            pass
        
        return metadata
    
    def validate_state_selection(self, state_name: str, 
                               tpr_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate that selected state matches TPR data.
        
        Args:
            state_name: Selected state name
            tpr_data: TPR data DataFrame
            
        Returns:
            Validation result
        """
        result = {
            'valid': False,
            'message': '',
            'state_in_shapefile': False,
            'state_in_tpr': False,
            'ward_match_count': 0
        }
        
        # Check if state exists in shapefile
        state_shapefile = self.extract_state_data(state_name)
        if state_shapefile is not None and not state_shapefile.empty:
            result['state_in_shapefile'] = True
        
        # Check if state exists in TPR data
        if 'State' in tpr_data.columns:
            tpr_states = tpr_data['State'].dropna().unique()
            normalized_state = self._normalize_state_name(state_name)
            
            for tpr_state in tpr_states:
                if self._normalize_state_name(tpr_state) == normalized_state:
                    result['state_in_tpr'] = True
                    break
        
        # If both exist, check ward matching
        if result['state_in_shapefile'] and result['state_in_tpr']:
            # Get ward names from both sources
            ward_col_shapefile = None
            for col in ['WardName', 'Ward', 'ward', 'WARD', 'ward_name']:
                if col in state_shapefile.columns:
                    ward_col_shapefile = col
                    break
            
            ward_col_tpr = None  
            for col in ['Ward', 'WardName', 'ward', 'ward_name']:
                if col in tpr_data.columns:
                    ward_col_tpr = col
                    break
            
            if ward_col_shapefile and ward_col_tpr:
                shapefile_wards = set(
                    state_shapefile[ward_col_shapefile].dropna().str.upper()
                )
                
                # Filter TPR data for state
                state_tpr = tpr_data[
                    tpr_data['State'].str.contains(state_name, case=False, na=False)
                ]
                tpr_wards = set(
                    state_tpr[ward_col_tpr].dropna().str.upper()
                )
                
                # Count matches
                result['ward_match_count'] = len(shapefile_wards & tpr_wards)
                
                if result['ward_match_count'] > 0:
                    result['valid'] = True
                    result['message'] = f"Successfully matched {result['ward_match_count']} wards"
                else:
                    result['message'] = "No matching wards found between TPR data and shapefile"
            else:
                result['message'] = "Could not identify ward columns for matching"
        else:
            if not result['state_in_shapefile']:
                result['message'] = f"State '{state_name}' not found in shapefile"
            elif not result['state_in_tpr']:
                result['message'] = f"State '{state_name}' not found in TPR data"
        
        return result
    
    def suggest_states(self, partial_input: str, max_suggestions: int = 5) -> List[str]:
        """
        Suggest states based on partial input.
        
        Args:
            partial_input: Partial state name
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of suggested state names
        """
        if not partial_input:
            return self.states_available[:max_suggestions]
        
        normalized_input = self._normalize_state_name(partial_input)
        suggestions = []
        
        # First, add states that start with the input
        for state in self.states_available:
            if self._normalize_state_name(state).startswith(normalized_input):
                suggestions.append(state)
                if len(suggestions) >= max_suggestions:
                    return suggestions
        
        # Then, add states that contain the input
        for state in self.states_available:
            if normalized_input in self._normalize_state_name(state) and state not in suggestions:
                suggestions.append(state)
                if len(suggestions) >= max_suggestions:
                    return suggestions
        
        return suggestions


def test_state_selector():
    """Test the state selector functionality."""
    # Initialize selector
    selector = StateSelector()
    
    # Test available states
    print("Available states:")
    states = selector.get_available_states()
    if states:
        print(f"  Found {len(states)} states")
        print(f"  First 5: {states[:5]}")
    else:
        print("  No states found (shapefile may be missing)")
    
    # Test state matching
    test_inputs = ["Lagos", "kano", "FCT", "Oyo State", "Lag"]
    print("\nState matching tests:")
    for test_input in test_inputs:
        matched, score = selector.match_state(test_input)
        print(f"  '{test_input}' -> '{matched}' (score: {score:.2f})")
    
    # Test suggestions
    print("\nState suggestions:")
    for partial in ["La", "Ka", "O"]:
        suggestions = selector.suggest_states(partial, max_suggestions=3)
        print(f"  '{partial}' -> {suggestions}")
    
    # Test metadata extraction
    if states:
        test_state = states[0]
        print(f"\nMetadata for {test_state}:")
        metadata = selector.get_state_metadata(test_state)
        for key, value in metadata.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    test_state_selector()