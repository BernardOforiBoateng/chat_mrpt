"""
ITN Population Data Loader
Handles loading of cleaned ITN population data with Ward, LGA, and Population columns
"""

import os
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, List
from functools import lru_cache

logger = logging.getLogger(__name__)

class ITNPopulationLoader:
    """Loader for cleaned ITN population data"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent.parent
        self.new_data_path = self.base_path / "www" / "ITN" / "ITN"
        self.old_data_path = self.base_path / "app" / "data" / "population_data"
        self._cache = {}
        
    @lru_cache(maxsize=32)
    def get_available_states(self) -> List[str]:
        """Get list of available states with ITN population data"""
        states = []
        
        # Check new data location
        if self.new_data_path.exists():
            for file in self.new_data_path.glob("pbi_distribution_*_clean.xlsx"):
                state = file.stem.replace("pbi_distribution_", "").replace("_clean", "")
                states.append(state)
                
        return sorted(states)
    
    def load_state_population(self, state_name: str, use_new_format: bool = True) -> Optional[pd.DataFrame]:
        """
        Load population data for a specific state
        
        Args:
            state_name: Name of the state (e.g., 'Kaduna', 'Niger')
            use_new_format: Whether to use new cleaned format (default True)
            
        Returns:
            DataFrame with population data or None if not found
        """
        cache_key = f"{state_name}_{use_new_format}"
        
        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key].copy()
            
        try:
            if use_new_format:
                # Load new cleaned format
                file_path = self.new_data_path / f"pbi_distribution_{state_name}_clean.xlsx"
                if not file_path.exists():
                    logger.warning(f"New format population data not found for {state_name}")
                    return None
                    
                df = pd.read_excel(file_path)
                
                # Validate expected columns
                expected_cols = ['Ward', 'LGA', 'Population']
                if not all(col in df.columns for col in expected_cols):
                    logger.error(f"Missing expected columns in {state_name} data. Found: {df.columns.tolist()}")
                    return None
                    
                # Clean and standardize data
                df['Ward'] = df['Ward'].str.strip()
                df['LGA'] = df['LGA'].str.strip()
                df['Population'] = pd.to_numeric(df['Population'], errors='coerce')
                
                # Remove any rows with missing population
                df = df.dropna(subset=['Population'])
                
                logger.info(f"Loaded {len(df)} wards for {state_name} with total population: {df['Population'].sum():,.0f}")
                
            else:
                # Load old format (backward compatibility)
                file_path = self.old_data_path / f"pbi_distribution_{state_name}.xlsx"
                if not file_path.exists():
                    # Try CSV format for Kano
                    csv_path = self.old_data_path / f"pbi_distribution_{state_name}.csv"
                    if csv_path.exists():
                        file_path = csv_path
                    else:
                        logger.warning(f"Old format population data not found for {state_name}")
                        return None
                        
                # Load file based on extension
                if file_path.suffix == '.csv':
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                    
                # Process old format to extract ward population
                # This is a simplified approach - may need adjustment based on actual data
                logger.info(f"Processing old format data for {state_name}")
                
            # Cache the result
            self._cache[cache_key] = df
            return df.copy()
            
        except Exception as e:
            logger.error(f"Error loading population data for {state_name}: {str(e)}")
            return None
    
    def get_ward_populations(self, state_name: str, ward_names: List[str] = None) -> Dict[str, int]:
        """
        Get population data for specific wards
        
        Args:
            state_name: Name of the state
            ward_names: List of ward names to get population for (None for all)
            
        Returns:
            Dictionary mapping ward names to population
        """
        df = self.load_state_population(state_name)
        if df is None:
            return {}
            
        ward_pop = {}
        
        if ward_names is None:
            # Return all wards
            for _, row in df.iterrows():
                ward_pop[row['Ward']] = int(row['Population'])
        else:
            # Return specific wards
            df_filtered = df[df['Ward'].isin(ward_names)]
            for _, row in df_filtered.iterrows():
                ward_pop[row['Ward']] = int(row['Population'])
                
        return ward_pop
    
    def get_total_population(self, state_name: str) -> int:
        """Get total population for a state"""
        df = self.load_state_population(state_name)
        if df is None:
            return 0
            
        return int(df['Population'].sum())
    
    def match_ward_names(self, state_name: str, input_ward_names: List[str]) -> Dict[str, str]:
        """
        Match input ward names to standardized ward names in population data
        
        Args:
            state_name: Name of the state
            input_ward_names: List of ward names from user data
            
        Returns:
            Dictionary mapping input names to standardized names
        """
        df = self.load_state_population(state_name)
        if df is None:
            return {}
            
        standard_wards = df['Ward'].unique()
        mapping = {}
        
        for input_ward in input_ward_names:
            # Try exact match first
            if input_ward in standard_wards:
                mapping[input_ward] = input_ward
                continue
                
            # Try case-insensitive match
            input_lower = input_ward.lower().strip()
            for std_ward in standard_wards:
                if std_ward.lower().strip() == input_lower:
                    mapping[input_ward] = std_ward
                    break
                    
            # If no match found, log it
            if input_ward not in mapping:
                logger.warning(f"No match found for ward: {input_ward}")
                
        return mapping


# Singleton instance
_loader_instance = None

def get_population_loader() -> ITNPopulationLoader:
    """Get singleton instance of population loader"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = ITNPopulationLoader()
    return _loader_instance