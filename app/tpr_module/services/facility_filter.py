"""
Facility filter service for TPR data.
Filters and analyzes data by facility level with recommendations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FacilityFilter:
    """
    Filters facility data by level and provides recommendations.
    
    Facility levels in Nigeria:
    - Primary: Basic health centers, community clinics
    - Secondary: General hospitals, specialist clinics  
    - Tertiary: Teaching hospitals, federal medical centers
    """
    
    # Facility levels - both short and full names for flexibility
    FACILITY_LEVELS = ['Primary', 'Secondary', 'Tertiary']
    FACILITY_LEVEL_MAPPINGS = {
        'Primary': ['Primary', 'Primary Health Facility', 'PHC'],
        'Secondary': ['Secondary', 'Secondary Health Facility', 'General Hospital'],
        'Tertiary': ['Tertiary', 'Tertiary Health Facility', 'Teaching Hospital', 'Federal Medical Center']
    }
    
    # Recommendations based on data patterns
    RECOMMENDATIONS = {
        'Primary': {
            'threshold': 70,  # Recommend if >70% of data
            'reason': 'Primary facilities better reflect community-level transmission'
        },
        'Secondary': {
            'threshold': 20,  # Consider if >20% of data
            'reason': 'Secondary facilities provide district-level insights'
        },
        'Tertiary': {
            'threshold': 5,   # Usually too few for analysis
            'reason': 'Tertiary facilities serve referral cases, less representative'
        }
    }
    
    def __init__(self):
        """Initialize the facility filter."""
        self.facility_stats = {}
        self.recommendation = None
        
    def analyze_facility_distribution(self, data: pd.DataFrame, 
                                    state_name: str = None) -> Dict:
        """
        Analyze facility distribution and data completeness by level.
        
        Args:
            data: NMEP data DataFrame
            state_name: Optional state filter
            
        Returns:
            Dictionary with facility statistics and recommendation
        """
        logger.info(f"Analyzing facility distribution for {state_name or 'all states'}")
        
        # Store state name for summary generation
        self.state_name = state_name
        
        # Filter by state if specified
        if state_name and 'State_clean' in data.columns:
            data = data[data['State_clean'] == state_name].copy()
        
        # Get facility statistics
        self.facility_stats = self._calculate_facility_stats(data)
        
        # Generate recommendation
        self.recommendation = self._generate_recommendation()
        
        # Calculate data completeness by level
        completeness_by_level = self._calculate_completeness_by_level(data)
        
        return {
            'facility_distribution': self.facility_stats,
            'data_completeness': completeness_by_level,
            'recommendation': self.recommendation,
            'summary': self._generate_summary()
        }
    
    def _calculate_facility_stats(self, data: pd.DataFrame) -> Dict:
        """Calculate facility statistics by level."""
        stats = {}
        
        # Use standardized column name after mapping
        level_col = 'facility_level' if 'facility_level' in data.columns else 'level'
        
        if level_col not in data.columns:
            logger.error(f"No facility level column found. Available columns: {list(data.columns)[:20]}")
            return stats
        
        # Count unique facilities by level
        # Use standardized column names after mapping
        facility_col = 'facility' if 'facility' in data.columns else 'Health Faccility'
        
        if facility_col not in data.columns:
            logger.error(f"No facility column found. Available columns: {list(data.columns)[:10]}")
            return stats
        
        total_facilities = data[facility_col].nunique()
        total_records = len(data)
        
        for level in self.FACILITY_LEVELS:
            # Use mapping to handle different facility level formats
            level_variants = self.FACILITY_LEVEL_MAPPINGS.get(level, [level])
            level_data = data[data[level_col].isin(level_variants)]
            
            if len(level_data) > 0:
                facility_count = level_data[facility_col].nunique()
                record_count = len(level_data)
                
                stats[level] = {
                    'facility_count': facility_count,
                    'facility_percentage': round((facility_count / total_facilities) * 100, 1),
                    'record_count': record_count,
                    'record_percentage': round((record_count / total_records) * 100, 1),
                    'avg_records_per_facility': round(record_count / facility_count, 1)
                }
                
                # Get LGA coverage
                lga_col = 'lga' if 'lga' in data.columns else 'LGA'
                if lga_col in data.columns:
                    total_lgas = data[lga_col].nunique()
                    level_lgas = level_data[lga_col].nunique()
                    stats[level]['lga_coverage'] = {
                        'count': level_lgas,
                        'percentage': round((level_lgas / total_lgas) * 100, 1)
                    }
                
                # Get ward coverage
                ward_col = 'ward' if 'ward' in data.columns else 'Ward'
                if ward_col in data.columns:
                    total_wards = data[ward_col].nunique()
                    level_wards = level_data[ward_col].nunique()
                    stats[level]['ward_coverage'] = {
                        'count': level_wards,
                        'percentage': round((level_wards / total_wards) * 100, 1)
                    }
            else:
                stats[level] = {
                    'facility_count': 0,
                    'facility_percentage': 0.0,
                    'record_count': 0,
                    'record_percentage': 0.0
                }
        
        return stats
    
    def _calculate_completeness_by_level(self, data: pd.DataFrame) -> Dict:
        """Calculate data completeness for each facility level."""
        completeness = {}
        
        # Key columns to check
        test_columns = [
            'rdt_tested_u5', 'rdt_positive_u5',
            'micro_tested_u5', 'micro_positive_u5'
        ]
        
        # Use standardized column name
        level_col = 'facility_level' if 'facility_level' in data.columns else 'level'
        
        for level in self.FACILITY_LEVELS:
            # Use mapping to handle different facility level formats
            level_variants = self.FACILITY_LEVEL_MAPPINGS.get(level, [level])
            level_data = data[data[level_col].isin(level_variants)]
            
            if len(level_data) > 0:
                level_completeness = {}
                
                # Check each age group
                for age_suffix in ['u5', 'o5', 'pw']:
                    rdt_tested = f'rdt_tested_{age_suffix}'
                    rdt_positive = f'rdt_positive_{age_suffix}'
                    
                    if rdt_tested in level_data.columns:
                        # Calculate percentage of non-null values
                        tested_complete = (level_data[rdt_tested].notna().sum() / 
                                         len(level_data)) * 100
                        positive_complete = (level_data[rdt_positive].notna().sum() / 
                                           len(level_data)) * 100
                        
                        # Records with both values present
                        both_complete = (level_data[[rdt_tested, rdt_positive]].notna()
                                       .all(axis=1).sum() / len(level_data)) * 100
                        
                        level_completeness[age_suffix] = {
                            'tested': round(tested_complete, 1),
                            'positive': round(positive_complete, 1),
                            'both': round(both_complete, 1)
                        }
                
                # Overall completeness for the level
                if level_completeness:
                    all_values = []
                    for age_data in level_completeness.values():
                        all_values.append(age_data['both'])
                    level_completeness['overall'] = round(np.mean(all_values), 1)
                
                completeness[level] = level_completeness
            else:
                completeness[level] = {'overall': 0.0}
        
        return completeness
    
    def _generate_recommendation(self) -> Dict:
        """Generate facility level recommendation based on data distribution."""
        if not self.facility_stats:
            return {
                'recommended_level': None,
                'confidence': 'low',
                'reason': 'Insufficient data for recommendation'
            }
        
        # Check Primary facilities first (usually recommended)
        primary_stats = self.facility_stats.get('Primary', {})
        primary_pct = primary_stats.get('record_percentage', 0)
        
        if primary_pct >= self.RECOMMENDATIONS['Primary']['threshold']:
            return {
                'recommended_level': 'Primary',
                'confidence': 'high',
                'reason': self.RECOMMENDATIONS['Primary']['reason'],
                'data_percentage': primary_pct,
                'alternative': self._get_alternative_recommendation()
            }
        
        # Check Secondary if Primary is insufficient
        secondary_stats = self.facility_stats.get('Secondary', {})
        secondary_pct = secondary_stats.get('record_percentage', 0)
        
        if secondary_pct >= self.RECOMMENDATIONS['Secondary']['threshold']:
            return {
                'recommended_level': 'Secondary',
                'confidence': 'medium',
                'reason': self.RECOMMENDATIONS['Secondary']['reason'],
                'data_percentage': secondary_pct,
                'note': 'Consider combining with Primary facilities for better coverage'
            }
        
        # If neither Primary nor Secondary have enough data
        return {
            'recommended_level': 'All',
            'confidence': 'low',
            'reason': 'No single facility level has sufficient data coverage',
            'suggestion': 'Consider using all facility levels combined'
        }
    
    def _get_alternative_recommendation(self) -> Optional[str]:
        """Get alternative recommendation if user doesn't want primary."""
        secondary_pct = self.facility_stats.get('Secondary', {}).get('record_percentage', 0)
        
        if secondary_pct >= 10:  # At least 10% data
            return f"Secondary facilities ({secondary_pct:.1f}% of data) for district-level analysis"
        return None
    
    def _generate_summary(self) -> str:
        """Generate a conversational summary of facility analysis."""
        if not self.facility_stats:
            return "No facility data available for analysis."
        
        # Get state name from analysis
        state_name = getattr(self, 'state_name', 'this state')
        
        # Get stats for each level
        primary_stats = self.facility_stats.get('Primary', {})
        secondary_stats = self.facility_stats.get('Secondary', {})
        tertiary_stats = self.facility_stats.get('Tertiary', {})
        
        # Get record percentages (not facility percentages)
        primary_percent = primary_stats.get('record_percentage', 0)
        secondary_percent = secondary_stats.get('record_percentage', 0)
        tertiary_percent = tertiary_stats.get('record_percentage', 0)
        
        # Format the facility selection message to match specification
        summary = f"""For TPR analysis in {state_name}, I recommend focusing on Primary Health Facilities because:
- They represent {primary_percent:.0f}% of your {state_name} data
- Secondary facilities handle complicated cases that aren't representative of ward-level transmission
- Primary facilities better reflect community-level malaria burden in {state_name}

**Current Selection:**
- Primary facilities: {primary_stats.get('facility_count', 0):,} facilities across {primary_stats.get('ward_coverage', {}).get('count', 'N/A')} wards
- Good distribution: {primary_stats.get('avg_records_per_facility', 0):.0f} records per facility on average
- Coverage: {primary_stats.get('ward_coverage', {}).get('percentage', 0):.0f}% of wards have primary facilities

Do you want to:
1. Use Primary Health Facilities only (recommended)
2. Include Secondary facilities ({secondary_stats.get('facility_count', 0):,} facilities)
3. Include all facility types

Your choice?"""
        
        return summary
    
    def filter_by_level(self, data: pd.DataFrame, 
                       facility_level: str) -> pd.DataFrame:
        """
        Filter data to specific facility level.
        
        Args:
            data: NMEP data DataFrame
            facility_level: Level to filter ('Primary', 'Secondary', 'Tertiary', 'All')
            
        Returns:
            Filtered DataFrame
        """
        if facility_level == 'All':
            return data
        
        if facility_level not in self.FACILITY_LEVELS:
            logger.warning(f"Unknown facility level: {facility_level}")
            return data
        
        level_col = 'facility_level' if 'facility_level' in data.columns else 'level'
        
        # Use mapping to handle different facility level formats
        level_variants = self.FACILITY_LEVEL_MAPPINGS.get(facility_level, [facility_level])
        filtered_data = data[data[level_col].isin(level_variants)].copy()
        
        logger.info(f"Filtered to {len(filtered_data)} records for {facility_level} facilities")
        
        return filtered_data
    
    def get_facility_list(self, data: pd.DataFrame, 
                         facility_level: str = None) -> List[Dict]:
        """
        Get list of facilities with basic statistics.
        
        Args:
            data: NMEP data DataFrame
            facility_level: Optional level filter
            
        Returns:
            List of facility information dictionaries
        """
        if facility_level:
            data = self.filter_by_level(data, facility_level)
        
        facilities = []
        
        for facility_name in data['facility'].unique():
            facility_data = data[data['facility'] == facility_name]
            
            facility_info = {
                'name': facility_name,
                'level': facility_data[level_col].iloc[0] if level_col in facility_data else 'Unknown',
                'lga': facility_data['lga'].iloc[0] if 'lga' in facility_data else 'Unknown',
                'ward': facility_data['ward'].iloc[0] if 'ward' in facility_data else 'Unknown',
                'record_count': len(facility_data),
                'months_reporting': facility_data['period'].nunique() if 'period' in facility_data else 0
            }
            
            facilities.append(facility_info)
        
        # Sort by record count
        facilities.sort(key=lambda x: x['record_count'], reverse=True)
        
        return facilities