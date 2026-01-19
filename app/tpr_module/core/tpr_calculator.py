"""
TPR Calculator with RDT/Microscopy comparison logic.
Implements standard and alternative TPR calculation methods.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TPRResult:
    """Container for TPR calculation results."""
    ward_name: str
    lga: str
    tpr_value: float
    calculation_method: str  # 'standard' or 'alternative'
    numerator: float  # positive cases
    denominator: float  # tested cases or OPD
    facility_count: int
    data_completeness: float
    is_urban: bool = False
    urban_percentage: float = 0.0


class TPRCalculator:
    """
    Calculates Test Positivity Rate using NMEP data.
    
    Implements two methods:
    1. Standard: TPR = (Positive Cases / Tested Cases) * 100
       Where values are max(RDT, Microscopy) for both numerator and denominator
    2. Alternative: TPR = (Positive Cases / Outpatient Attendance) × 100
       Used for urban areas with TPR > 50%
    """
    
    def __init__(self):
        """Initialize the TPR calculator."""
        self.results = []
        self.problematic_wards = []
    
    
    def _calculate_single_tpr(self, row: Dict) -> Dict:
        """
        Calculate TPR for a single row of data.
        
        Args:
            row: Dictionary with test data
            
        Returns:
            Dictionary with TPR calculation results
        """
        # Extract values with proper column names
        rdt_tested = row.get('RDT_Tested', row.get('Persons tested for malaria by RDT', 0))
        rdt_positive = row.get('RDT_Positive', row.get('Persons tested positive for malaria by RDT', 0))
        micro_tested = row.get('Microscopy_Tested', row.get('Persons tested for malaria by Microscopy', 0))
        micro_positive = row.get('Microscopy_Positive', row.get('Persons tested positive for malaria by Microscopy', 0))
        outpatient = row.get('Outpatient_Attendance', row.get('Total number of all outpatient attendance', 0))
        
        # Handle missing values
        rdt_tested = 0 if pd.isna(rdt_tested) else rdt_tested
        rdt_positive = 0 if pd.isna(rdt_positive) else rdt_positive
        micro_tested = 0 if pd.isna(micro_tested) else micro_tested
        micro_positive = 0 if pd.isna(micro_positive) else micro_positive
        outpatient = 0 if pd.isna(outpatient) else outpatient
        
        # Apply max logic
        tested = max(rdt_tested, micro_tested)
        positive = max(rdt_positive, micro_positive)
        
        # Calculate TPR
        if tested > 0:
            tpr = (positive / tested) * 100
            
            # Check if alternative method should be used
            if tpr > 50 and outpatient > 0:
                # Use alternative calculation for high TPR
                tpr = (positive / outpatient) * 100
                method = 'alternative'
            else:
                method = 'standard'
            
            return {
                'tpr': round(tpr, 2),
                'tested': tested,
                'positive': positive,
                'method': method
            }
        else:
            return {
                'tpr': float('nan'),
                'tested': 0,
                'positive': 0,
                'method': 'no_data'
            }
        
    def calculate_ward_tpr(self, facility_data: pd.DataFrame, 
                          age_group: str = 'u5',
                          urban_threshold: float = 50.0) -> List[TPRResult]:
        """
        Calculate TPR for all wards in the dataset.
        
        Args:
            facility_data: DataFrame with facility-level data
            age_group: Age group to calculate for ('u5', 'o5', 'pw')
            urban_threshold: TPR threshold for urban areas (default 50%)
            
        Returns:
            List of TPRResult objects
        """
        logger.info(f"Calculating TPR for age group: {age_group}")
        
        # Make a copy and check for WardName column
        facility_data = facility_data.copy()
        
        # Use WardName if available (cleaned names), otherwise fall back to ward
        if 'WardName' in facility_data.columns:
            ward_col = 'WardName'
            logger.info("Using cleaned WardName column for grouping")
        else:
            ward_col = 'ward'
            logger.info("Using original ward column for grouping")
        
        # Ensure LGA column exists
        lga_col = 'LGA' if 'LGA' in facility_data.columns else 'lga'
        
        # Check if columns exist and are valid
        if ward_col not in facility_data.columns:
            raise ValueError(f"Ward column '{ward_col}' not found in data. Available columns: {list(facility_data.columns)[:20]}")
        if lga_col not in facility_data.columns:
            raise ValueError(f"LGA column '{lga_col}' not found in data. Available columns: {list(facility_data.columns)[:20]}")
        
        # Ensure columns are string type for groupby
        facility_data[ward_col] = facility_data[ward_col].astype(str)
        facility_data[lga_col] = facility_data[lga_col].astype(str)
        
        # Group by ward and LGA
        try:
            ward_groups = facility_data.groupby([ward_col, lga_col])
        except Exception as e:
            logger.error(f"Error grouping by {ward_col} and {lga_col}: {e}")
            logger.error(f"Data shape: {facility_data.shape}")
            logger.error(f"Ward column unique values: {facility_data[ward_col].nunique()}")
            logger.error(f"LGA column unique values: {facility_data[lga_col].nunique()}")
            raise
        
        results = []
        for (ward, lga), ward_data in ward_groups:
            # Calculate standard TPR
            tpr_result = self._calculate_standard_tpr(
                ward_data, ward, lga, age_group
            )
            
            # Check if this is an urban ward with high TPR
            if (tpr_result.is_urban and 
                tpr_result.tpr_value > urban_threshold):
                # Flag for alternative calculation
                self.problematic_wards.append(tpr_result)
            
            results.append(tpr_result)
        
        self.results = results
        
        # Return results as a dictionary for compatibility
        result_dict = {}
        for result in results:
            result_dict[result.ward_name] = {
                'tpr': result.tpr_value,
                'method': 'standard' if result.tpr_value <= 50 else 'alternative',
                'total_tested': result.denominator,  # TPRResult uses denominator
                'total_positive': result.numerator,  # TPRResult uses numerator
                'rdt_tested': getattr(result, 'rdt_tested', 0),
                'rdt_positive': getattr(result, 'rdt_positive', 0),
                'microscopy_tested': getattr(result, 'microscopy_tested', 0),
                'microscopy_positive': getattr(result, 'microscopy_positive', 0),
                'lga': result.lga
            }
        
        return result_dict
    
    def _check_if_urban(self, ward_data: pd.DataFrame) -> bool:
        """
        Check if ward is predominantly urban based on facility data.
        
        Args:
            ward_data: Facility data for a ward
            
        Returns:
            True if ward is urban
        """
        # Check if we have urban indicator column
        if 'urban' in ward_data.columns:
            # If any facility is marked as urban, consider the ward urban
            return ward_data['urban'].any()
        
        # Check facility names for urban indicators
        urban_keywords = ['urban', 'city', 'municipal', 'metro']
        facility_names = ward_data.get('facility', pd.Series()).str.lower()
        
        for keyword in urban_keywords:
            if facility_names.str.contains(keyword, na=False).any():
                return True
                
        return False
    
    def _calculate_urban_percentage(self, ward_data: pd.DataFrame) -> float:
        """
        Calculate percentage of urban facilities in ward.
        
        Args:
            ward_data: Facility data for a ward
            
        Returns:
            Percentage of urban facilities
        """
        if 'urban' in ward_data.columns:
            urban_count = ward_data['urban'].sum()
            total_count = len(ward_data)
            return (urban_count / total_count * 100) if total_count > 0 else 0.0
        
        return 0.0
    
    def _calculate_standard_tpr(self, ward_data: pd.DataFrame,
                               ward_name: str, lga: str,
                               age_group: str) -> TPRResult:
        """
        Calculate standard TPR using max(RDT, Microscopy) logic.
        
        Args:
            ward_data: Facility data for a single ward
            ward_name: Name of the ward
            lga: LGA name
            age_group: Age group identifier
            
        Returns:
            TPRResult object
        """
        # Handle all_ages case by summing across age groups
        if age_group == 'all_ages' or age_group == 'all':
            # Sum across all age groups
            rdt_tested_total = 0
            rdt_positive_total = 0
            micro_tested_total = 0
            micro_positive_total = 0
            
            for suffix in ['u5', 'o5', 'pw']:
                rdt_tested_col = f'rdt_tested_{suffix}'
                rdt_positive_col = f'rdt_positive_{suffix}'
                micro_tested_col = f'micro_tested_{suffix}'
                micro_positive_col = f'micro_positive_{suffix}'
                
                if rdt_tested_col in ward_data.columns:
                    rdt_tested_total += ward_data[rdt_tested_col].fillna(0).sum()
                    rdt_positive_total += ward_data[rdt_positive_col].fillna(0).sum()
                if micro_tested_col in ward_data.columns:
                    micro_tested_total += ward_data[micro_tested_col].fillna(0).sum()
                    micro_positive_total += ward_data[micro_positive_col].fillna(0).sum()
            
            # Calculate TPR for all ages combined
            if rdt_tested_total > 0:
                rdt_tpr = (rdt_positive_total / rdt_tested_total) * 100
            else:
                rdt_tpr = 0
                
            if micro_tested_total > 0:
                micro_tpr = (micro_positive_total / micro_tested_total) * 100
            else:
                micro_tpr = 0
            
            # Use max TPR
            tpr = max(rdt_tpr, micro_tpr)
            
            # Create TPRResult
            result = TPRResult(
                ward_name=ward_name,
                lga=lga,
                tpr_value=round(tpr, 1),
                calculation_method='standard',
                numerator=rdt_positive_total if rdt_tested_total > 0 else micro_positive_total,
                denominator=rdt_tested_total if rdt_tested_total > 0 else micro_tested_total,
                data_completeness=100 if (rdt_tested_total > 0 or micro_tested_total > 0) else 0,
                facility_count=len(ward_data),
                is_urban=self._check_if_urban(ward_data),
                urban_percentage=self._calculate_urban_percentage(ward_data)
            )
            
            return result
        
        # Get column names based on age group
        # The columns are already created by NMEP parser with lowercase names
        rdt_tested_col = f'rdt_tested_{age_group}'
        rdt_positive_col = f'rdt_positive_{age_group}'
        micro_tested_col = f'micro_tested_{age_group}'
        micro_positive_col = f'micro_positive_{age_group}'
        
        # Check if required columns exist
        if rdt_tested_col not in ward_data.columns:
            # Log available columns for debugging
            logger.warning(f"Required column '{rdt_tested_col}' not found. Available columns: {list(ward_data.columns)}")
            raise ValueError(f"Required column '{rdt_tested_col}' not found in data")
        
        # Debug logging
        logger.debug(f"Calculating TPR for ward {ward_name} with {len(ward_data)} facilities")
        logger.debug(f"Looking for columns: {rdt_tested_col}, {rdt_positive_col}, {micro_tested_col}, {micro_positive_col}")
        
        # Check if all required columns exist
        missing_cols = []
        for col in [rdt_positive_col, micro_tested_col, micro_positive_col]:
            if col not in ward_data.columns:
                missing_cols.append(col)
        
        if missing_cols:
            logger.warning(f"Missing columns for {ward_name}: {missing_cols}")
            logger.debug(f"Available columns with 'rdt' or 'micro': {[c for c in ward_data.columns if 'rdt' in c or 'micro' in c]}")
        
        # Aggregate by facility and month
        facility_tpr_values = []
        total_tested = 0
        total_positive = 0
        
        for _, facility_row in ward_data.iterrows():
            # Get test values with NaN checking
            rdt_tested = facility_row.get(rdt_tested_col, 0)
            rdt_positive = facility_row.get(rdt_positive_col, 0)
            micro_tested = facility_row.get(micro_tested_col, 0)
            micro_positive = facility_row.get(micro_positive_col, 0)
            
            # Convert to float and handle NaN
            rdt_tested = 0 if pd.isna(rdt_tested) else float(rdt_tested)
            rdt_positive = 0 if pd.isna(rdt_positive) else float(rdt_positive)
            micro_tested = 0 if pd.isna(micro_tested) else float(micro_tested)
            micro_positive = 0 if pd.isna(micro_positive) else float(micro_positive)
            
            # Apply max logic
            tested = max(rdt_tested, micro_tested)
            positive = max(rdt_positive, micro_positive)
            
            # Skip if no tests performed
            if tested > 0:
                total_tested += tested
                total_positive += positive
                facility_tpr = (positive / tested) * 100
                facility_tpr_values.append(facility_tpr)
        
        # Calculate ward-level TPR
        if total_tested > 0:
            ward_tpr = (total_positive / total_tested) * 100
            logger.debug(f"Ward {ward_name}: {total_positive}/{total_tested} = {ward_tpr:.1f}%")
        else:
            ward_tpr = 0.0
            logger.warning(f"Ward {ward_name}: No tests performed (total_tested=0)")
            logger.debug(f"Ward {ward_name} data sample: {ward_data[rdt_tested_col].head() if rdt_tested_col in ward_data.columns else 'Column not found'}")
        
        # Calculate data completeness
        total_records = len(ward_data)
        records_with_data = len(facility_tpr_values)
        completeness = (records_with_data / total_records) * 100 if total_records > 0 else 0
        
        # Check urban status (placeholder - would need urban data)
        is_urban = self._check_urban_status(ward_name, ward_data)
        urban_pct = ward_data.get('urban_percentage', 0).mean() if 'urban_percentage' in ward_data else 0
        
        # Only clean names if they haven't been cleaned already
        # If we're using WardName column, it's already cleaned
        if 'WardName' in ward_data.columns:
            cleaned_ward_name = ward_name  # Already cleaned
            cleaned_lga_name = lga  # Assume LGA is also clean
        else:
            cleaned_ward_name = self._clean_ward_name(ward_name)
            cleaned_lga_name = self._clean_lga_name(lga)
        
        return TPRResult(
            ward_name=cleaned_ward_name,
            lga=cleaned_lga_name,
            tpr_value=round(ward_tpr, 1),
            calculation_method='standard',
            numerator=total_positive,
            denominator=total_tested,
            facility_count=len(ward_data['facility'].unique()) if 'facility' in ward_data.columns else 0,
            data_completeness=round(completeness, 1),
            is_urban=is_urban,
            urban_percentage=urban_pct
        )
    
    def calculate_alternative_tpr(self, ward_data: pd.DataFrame,
                                 ward_name: str, lga: str,
                                 age_group: str = 'u5') -> TPRResult:
        """
        Calculate alternative TPR using outpatient attendance.
        
        TPR = (Positive Cases / Outpatient Attendance) × 100
        
        Args:
            ward_data: Facility data for a single ward
            ward_name: Name of the ward
            lga: LGA name
            age_group: Age group identifier
            
        Returns:
            TPRResult object
        """
        # Get column names
        rdt_positive_col = f'rdt_positive_{age_group}'
        micro_positive_col = f'micro_positive_{age_group}'
        
        # Use age-specific OPD if available, else total
        if age_group == 'u5' and 'outpatient_u5' in ward_data.columns:
            opd_col = 'outpatient_u5'
        else:
            opd_col = 'outpatient_total'
        
        # Aggregate data
        total_positive = 0
        total_opd = 0
        
        for _, facility_row in ward_data.iterrows():
            # Get positive cases (max of RDT and Microscopy)
            rdt_positive = facility_row.get(rdt_positive_col, 0) or 0
            micro_positive = facility_row.get(micro_positive_col, 0) or 0
            positive = max(rdt_positive, micro_positive)
            
            # Get OPD attendance
            opd = facility_row.get(opd_col, 0) or 0
            
            if opd > 0:
                total_positive += positive
                total_opd += opd
        
        # Calculate alternative TPR
        if total_opd > 0:
            alt_tpr = (total_positive / total_opd) * 100
        else:
            logger.warning(f"No OPD data for {ward_name}, cannot calculate alternative TPR")
            alt_tpr = 0.0
        
        # Only clean names if they haven't been cleaned already
        if 'WardName' in ward_data.columns:
            cleaned_ward_name = ward_name  # Already cleaned
            cleaned_lga_name = lga  # Assume LGA is also clean
        else:
            cleaned_ward_name = self._clean_ward_name(ward_name)
            cleaned_lga_name = self._clean_lga_name(lga)
        
        return TPRResult(
            ward_name=cleaned_ward_name,
            lga=cleaned_lga_name,
            tpr_value=round(alt_tpr, 1),
            calculation_method='alternative',
            numerator=total_positive,
            denominator=total_opd,
            facility_count=len(ward_data['facility'].unique()) if 'facility' in ward_data.columns else 0,
            data_completeness=100.0,  # Assuming OPD data is complete
            is_urban=True,
            urban_percentage=ward_data.get('urban_percentage', 0).mean()
        )
    
    def _check_urban_status(self, ward_name: str, ward_data: pd.DataFrame) -> bool:
        """
        Check if a ward is urban based on available indicators.
        
        Args:
            ward_name: Name of the ward
            ward_data: Ward data
            
        Returns:
            True if urban, False otherwise
        """
        # Check for urban indicators in ward name
        urban_keywords = ['central', 'metropol', 'city', 'urban', 'municipal']
        ward_lower = ward_name.lower()
        
        for keyword in urban_keywords:
            if keyword in ward_lower:
                return True
        
        # Check if urban_percentage column exists
        if 'urban_percentage' in ward_data.columns:
            avg_urban = ward_data['urban_percentage'].mean()
            return avg_urban > 50
        
        # Default to False if no urban indicators
        return False
    
    def _clean_ward_name(self, ward_name: str) -> str:
        """
        Clean ward name by removing state prefix and 'Ward' suffix.
        'ad Bille Ward' -> 'Bille'
        """
        import re
        # Remove 2-3 letter prefix followed by space
        pattern = r'^[A-Za-z]{2,3}\s+(.+)$'
        match = re.match(pattern, ward_name)
        if match:
            cleaned = match.group(1).strip()
        else:
            cleaned = ward_name
        
        # Remove 'Ward' suffix
        if cleaned.endswith(' Ward'):
            cleaned = cleaned[:-5].strip()
        
        return cleaned
    
    def _clean_lga_name(self, lga_name: str) -> str:
        """
        Clean LGA name by removing state prefix and 'Local Government Area' suffix.
        'ad Fufore Local Government Area' -> 'Fufore'
        """
        import re
        # Remove 2-3 letter prefix followed by space
        pattern = r'^[A-Za-z]{2,3}\s+(.+)$'
        match = re.match(pattern, lga_name)
        if match:
            cleaned = match.group(1).strip()
        else:
            cleaned = lga_name
        
        # Remove 'Local Government Area' suffix
        if cleaned.endswith(' Local Government Area'):
            cleaned = cleaned[:-23].strip()
        
        return cleaned
    
    def get_summary_statistics(self) -> Dict:
        """
        Get summary statistics for calculated TPR values.
        
        Returns:
            Dictionary with summary stats
        """
        if not self.results:
            return {
                'total_wards': 0,
                'average_tpr': 0,
                'median_tpr': 0,
                'min_tpr': 0,
                'max_tpr': 0,
                'std_dev': 0,
                'problematic_wards': 0,
                'wards_above_30': 0,
                'wards_above_50': 0,
                'average_completeness': 0
            }
        
        tpr_values = [r.tpr_value for r in self.results]
        
        # Handle case where all TPR values might be NaN or empty
        valid_tpr_values = [v for v in tpr_values if not np.isnan(v)]
        
        if not valid_tpr_values:
            logger.warning("No valid TPR values found - all values are NaN")
            return {
                'total_wards': len(self.results),
                'average_tpr': 0,
                'median_tpr': 0,
                'min_tpr': 0,
                'max_tpr': 0,
                'std_dev': 0,
                'problematic_wards': len(self.problematic_wards),
                'wards_above_30': 0,
                'wards_above_50': 0,
                'average_completeness': round(np.mean([r.data_completeness for r in self.results]), 1) if self.results else 0
            }
        
        return {
            'total_wards': len(self.results),
            'average_tpr': round(np.mean(valid_tpr_values), 1),
            'median_tpr': round(np.median(valid_tpr_values), 1),
            'min_tpr': round(min(valid_tpr_values), 1),
            'max_tpr': round(max(valid_tpr_values), 1),
            'std_dev': round(np.std(valid_tpr_values), 1),
            'problematic_wards': len(self.problematic_wards),
            'wards_above_30': len([r for r in self.results if r.tpr_value > 30 and not np.isnan(r.tpr_value)]),
            'wards_above_50': len([r for r in self.results if r.tpr_value > 50 and not np.isnan(r.tpr_value)]),
            'average_completeness': round(np.mean([r.data_completeness for r in self.results]), 1) if self.results else 0
        }
    
    def export_results_to_dataframe(self, include_geometry: bool = False) -> pd.DataFrame:
        """
        Export TPR results to a pandas DataFrame.
        
        Args:
            include_geometry: Whether to include geometry column if available
            
        Returns:
            DataFrame with TPR results
        """
        if not self.results:
            return pd.DataFrame()
        
        # Convert results to dictionary format
        data = []
        for result in self.results:
            data.append({
                'WardName': result.ward_name,
                'LGA': result.lga,
                'TPR': result.tpr_value,
                'TPR_Method': result.calculation_method,
                'Positive_Cases': result.numerator,
                'Tested_or_OPD': result.denominator,
                'Facility_Count': result.facility_count,
                'Data_Completeness': result.data_completeness,
                'Is_Urban': result.is_urban,
                'Urban_Percentage': result.urban_percentage
            })
        
        df = pd.DataFrame(data)
        
        # Add geometry if requested and available
        if include_geometry and hasattr(self, 'ward_geometries'):
            df['geometry'] = df['WardName'].map(self.ward_geometries)
        
        return df
    
    def identify_high_burden_wards(self, threshold: float = 40.0) -> List[TPRResult]:
        """
        Identify wards with TPR above a given threshold.
        
        Args:
            threshold: TPR threshold (default 40%)
            
        Returns:
            List of high-burden wards
        """
        return [r for r in self.results if r.tpr_value >= threshold]