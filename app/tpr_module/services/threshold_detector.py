"""
Threshold detector for identifying wards with suspiciously high TPR values.
Focuses on urban areas where TPR > 50% is unusual.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ThresholdDetector:
    """
    Detects wards with TPR values exceeding thresholds.
    
    Key logic:
    - Urban areas with TPR > 50% are flagged for alternative calculation
    - Rural areas may have higher TPR due to limited testing
    - Provides detailed analysis of problematic wards
    """
    
    # Default thresholds
    URBAN_TPR_THRESHOLD = 50.0  # 50% TPR in urban areas is suspicious
    RURAL_TPR_THRESHOLD = 70.0  # Higher threshold for rural areas
    URBAN_CLASSIFICATION_THRESHOLD = 30.0  # >30% urban population = urban ward
    
    def __init__(self, urban_threshold: float = 50.0, 
                 rural_threshold: float = 70.0):
        """
        Initialize the threshold detector.
        
        Args:
            urban_threshold: TPR threshold for urban areas
            rural_threshold: TPR threshold for rural areas
        """
        self.urban_threshold = urban_threshold
        self.rural_threshold = rural_threshold
        self.problematic_wards = []
        self.analysis_results = {}
        
    def detect_threshold_violations(self, tpr_results: List, 
                                  ward_urban_data: Optional[pd.DataFrame] = None) -> Dict:
        """
        Detect wards exceeding TPR thresholds.
        
        Args:
            tpr_results: List of TPRResult objects from TPRCalculator
            ward_urban_data: Optional DataFrame with urban percentage by ward
            
        Returns:
            Dictionary with detection results and recommendations
        """
        logger.info(f"Detecting threshold violations (urban: {self.urban_threshold}%, "
                   f"rural: {self.rural_threshold}%)")
        
        # Reset results
        self.problematic_wards = []
        urban_violations = []
        rural_violations = []
        
        # Analyze each ward
        for tpr_result in tpr_results:
            ward_name = tpr_result.ward_name
            tpr_value = tpr_result.tpr_value
            
            # Determine if ward is urban
            is_urban = self._determine_urban_status(
                ward_name, 
                tpr_result.is_urban,
                tpr_result.urban_percentage,
                ward_urban_data
            )
            
            # Check threshold based on urban/rural status
            if is_urban:
                if tpr_value > self.urban_threshold:
                    urban_violations.append({
                        'ward': ward_name,
                        'lga': tpr_result.lga,
                        'tpr': tpr_value,
                        'urban_pct': tpr_result.urban_percentage,
                        'excess': tpr_value - self.urban_threshold,
                        'facility_count': tpr_result.facility_count,
                        'calculation_method': tpr_result.calculation_method
                    })
                    self.problematic_wards.append(tpr_result)
            else:
                if tpr_value > self.rural_threshold:
                    rural_violations.append({
                        'ward': ward_name,
                        'lga': tpr_result.lga,
                        'tpr': tpr_value,
                        'urban_pct': tpr_result.urban_percentage,
                        'excess': tpr_value - self.rural_threshold,
                        'facility_count': tpr_result.facility_count,
                        'calculation_method': tpr_result.calculation_method
                    })
        
        # Analyze patterns in violations
        patterns = self._analyze_violation_patterns(urban_violations, rural_violations)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            urban_violations, rural_violations, patterns
        )
        
        self.analysis_results = {
            'total_wards': len(tpr_results),
            'urban_violations': urban_violations,
            'rural_violations': rural_violations,
            'violation_patterns': patterns,
            'recommendations': recommendations,
            'summary': self._generate_summary(urban_violations, rural_violations)
        }
        
        return self.analysis_results
    
    def _determine_urban_status(self, ward_name: str, 
                               is_urban_flag: bool,
                               urban_percentage: float,
                               ward_urban_data: Optional[pd.DataFrame]) -> bool:
        """
        Determine if a ward is urban using multiple criteria.
        
        Args:
            ward_name: Name of the ward
            is_urban_flag: Urban flag from TPR result
            urban_percentage: Urban percentage from TPR result
            ward_urban_data: Optional external urban data
            
        Returns:
            True if ward is urban, False otherwise
        """
        # First check external data if available
        if ward_urban_data is not None and 'WardName' in ward_urban_data.columns:
            ward_row = ward_urban_data[ward_urban_data['WardName'] == ward_name]
            if not ward_row.empty and 'urban_percentage' in ward_row.columns:
                return ward_row['urban_percentage'].iloc[0] > self.URBAN_CLASSIFICATION_THRESHOLD
        
        # Use urban percentage if available
        if urban_percentage > 0:
            return urban_percentage > self.URBAN_CLASSIFICATION_THRESHOLD
        
        # Use flag if set
        if is_urban_flag:
            return True
        
        # Check ward name for urban indicators
        urban_keywords = ['central', 'metro', 'city', 'urban', 'municipal', 'town']
        ward_lower = ward_name.lower()
        
        return any(keyword in ward_lower for keyword in urban_keywords)
    
    def _analyze_violation_patterns(self, urban_violations: List[Dict], 
                                   rural_violations: List[Dict]) -> Dict:
        """
        Analyze patterns in threshold violations.
        
        Args:
            urban_violations: List of urban ward violations
            rural_violations: List of rural ward violations
            
        Returns:
            Dictionary with pattern analysis
        """
        patterns = {
            'geographic_clustering': {},
            'severity_distribution': {},
            'facility_patterns': {}
        }
        
        # Geographic clustering by LGA
        if urban_violations:
            urban_lgas = {}
            for violation in urban_violations:
                lga = violation['lga']
                if lga not in urban_lgas:
                    urban_lgas[lga] = []
                urban_lgas[lga].append(violation['ward'])
            
            # Find LGAs with multiple violations
            clustered_lgas = {lga: wards for lga, wards in urban_lgas.items() 
                            if len(wards) > 1}
            
            patterns['geographic_clustering']['urban'] = {
                'clustered_lgas': clustered_lgas,
                'cluster_count': len(clustered_lgas)
            }
        
        # Severity distribution
        all_violations = urban_violations + rural_violations
        if all_violations:
            tpr_values = [v['tpr'] for v in all_violations]
            patterns['severity_distribution'] = {
                'mean_tpr': round(np.mean(tpr_values), 1),
                'max_tpr': round(max(tpr_values), 1),
                'severe_violations': len([v for v in all_violations if v['tpr'] > 70]),
                'extreme_violations': len([v for v in all_violations if v['tpr'] > 90])
            }
        
        # Facility count patterns
        if urban_violations:
            facility_counts = [v['facility_count'] for v in urban_violations]
            patterns['facility_patterns'] = {
                'low_facility_violations': len([v for v in urban_violations 
                                              if v['facility_count'] < 5]),
                'average_facilities': round(np.mean(facility_counts), 1)
            }
        
        return patterns
    
    def _generate_recommendations(self, urban_violations: List[Dict],
                                 rural_violations: List[Dict],
                                 patterns: Dict) -> List[Dict]:
        """
        Generate recommendations based on violation analysis.
        
        Args:
            urban_violations: Urban ward violations
            rural_violations: Rural ward violations
            patterns: Pattern analysis results
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Recommendation for urban violations
        if urban_violations:
            recommendations.append({
                'type': 'alternative_calculation',
                'priority': 'high',
                'affected_wards': len(urban_violations),
                'message': (f"Recalculate TPR for {len(urban_violations)} urban wards "
                          f"using outpatient attendance as denominator"),
                'reason': "Urban areas typically have lower TPR due to better access to testing"
            })
        
        # Check for geographic clustering
        geo_clusters = patterns.get('geographic_clustering', {}).get('urban', {}).get('clustered_lgas', {})
        if geo_clusters:
            recommendations.append({
                'type': 'data_quality_check',
                'priority': 'medium',
                'affected_lgas': list(geo_clusters.keys()),
                'message': f"Review data quality for {len(geo_clusters)} LGAs with multiple high-TPR wards",
                'reason': "Geographic clustering may indicate systematic data issues"
            })
        
        # Check for extreme values
        severity = patterns.get('severity_distribution', {})
        if severity.get('extreme_violations', 0) > 0:
            recommendations.append({
                'type': 'data_validation',
                'priority': 'high',
                'affected_wards': severity['extreme_violations'],
                'message': f"Validate source data for {severity['extreme_violations']} wards with TPR > 90%",
                'reason': "Extremely high TPR values may indicate data entry errors"
            })
        
        # Low facility count warning
        facility_patterns = patterns.get('facility_patterns', {})
        if facility_patterns.get('low_facility_violations', 0) > 0:
            recommendations.append({
                'type': 'interpretation_warning',
                'priority': 'medium',
                'affected_wards': facility_patterns['low_facility_violations'],
                'message': "Interpret results carefully for wards with <5 reporting facilities",
                'reason': "Low facility counts may not represent true ward-level burden"
            })
        
        return recommendations
    
    def _generate_summary(self, urban_violations: List[Dict], 
                         rural_violations: List[Dict]) -> str:
        """
        Generate a conversational summary of threshold violations.
        
        Args:
            urban_violations: Urban ward violations
            rural_violations: Rural ward violations
            
        Returns:
            Formatted summary string
        """
        if not urban_violations and not rural_violations:
            return " No threshold violations detected. All TPR values are within expected ranges."
        
        summary_parts = []
        
        if urban_violations:
            summary_parts.append(
                f"- Found **{len(urban_violations)} urban wards** with TPR > {self.urban_threshold}%:"
            )
            
            # Show top 3 violations
            top_violations = sorted(urban_violations, key=lambda x: x['tpr'], reverse=True)[:3]
            for v in top_violations:
                summary_parts.append(
                    f"   - {v['ward']} ({v['lga']}): {v['tpr']:.1f}%"
                )
            
            if len(urban_violations) > 3:
                summary_parts.append(f"   ...and {len(urban_violations) - 3} more")
        
        if rural_violations:
            summary_parts.append(
                f"\n- Found **{len(rural_violations)} rural wards** with TPR > {self.rural_threshold}%"
            )
        
        return "\n".join(summary_parts)
    
    def get_alternative_calculation_list(self) -> List[Dict]:
        """
        Get list of wards requiring alternative TPR calculation.
        
        Returns:
            List of ward information for alternative calculation
        """
        if not self.analysis_results.get('urban_violations'):
            return []
        
        alt_calc_list = []
        for violation in self.analysis_results['urban_violations']:
            alt_calc_list.append({
                'ward': violation['ward'],
                'lga': violation['lga'],
                'current_tpr': violation['tpr'],
                'reason': f"Urban ward with TPR {violation['tpr']:.1f}% > {self.urban_threshold}%",
                'priority': 'high' if violation['tpr'] > 70 else 'medium'
            })
        
        return alt_calc_list
    
    def generate_alert_message(self) -> Optional[str]:
        """
        Generate alert message for user about threshold violations.
        
        Returns:
            Alert message or None if no violations
        """
        urban_count = len(self.analysis_results.get('urban_violations', []))
        
        if urban_count == 0:
            return None
        
        message = (
            f"- **Data Quality Alert**\n\n"
            f"I've detected {urban_count} urban ward{'s' if urban_count > 1 else ''} "
            f"with unusually high TPR values (>{self.urban_threshold}%).\n\n"
        )
        
        # Add specific examples
        violations = self.analysis_results['urban_violations'][:3]
        for v in violations:
            message += f"- {v['ward']}: {v['tpr']:.1f}%\n"
        
        message += (
            f"\nThese values seem high for urban areas where testing is more accessible. "
            f"Would you like me to recalculate using the alternative method "
            f"(positive cases / outpatient attendance)?"
        )
        
        return message