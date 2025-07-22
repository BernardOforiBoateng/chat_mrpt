"""
ITN (Insecticide-Treated Net) Distribution Planning Tools

Tools for planning optimal distribution of bed nets based on malaria vulnerability rankings.
Activates after analysis is complete and uses composite or PCA rankings for prioritization.
"""

import logging
from typing import Optional, List, Dict, Any
from pydantic import Field, validator

from .base import BaseTool, ToolCategory, ToolExecutionResult
from ..analysis.itn_pipeline import calculate_itn_distribution
from ..models.data_handler import DataHandler
from ..services.container import get_service_container

logger = logging.getLogger(__name__)


class PlanITNDistribution(BaseTool):
    """
    Plan ITN (bed net) distribution based on vulnerability rankings.
    
    This tool helps allocate insecticide-treated nets optimally across wards,
    prioritizing high-risk areas based on malaria vulnerability analysis.
    """
    
    total_nets: Optional[int] = Field(
        None, 
        description="Total number of nets available for distribution"
    )
    
    avg_household_size: Optional[float] = Field(
        None,
        description="Average household size in the region (default: 5.0)"
    )
    
    urban_threshold: Optional[float] = Field(
        None,
        description="Urban percentage threshold for prioritization (default: 30%)"
    )
    
    method: str = Field(
        "composite",
        description="Ranking method to use: 'composite' or 'pca'"
    )
    
    @classmethod
    def get_tool_name(cls) -> str:
        return "plan_itn_distribution"
    
    @classmethod
    def get_description(cls) -> str:
        return "Plan optimal distribution of ITN/bed nets based on malaria vulnerability rankings"
    
    @classmethod
    def get_category(cls) -> ToolCategory:
        return ToolCategory.ITN_PLANNING
    
    @classmethod
    def get_examples(cls) -> List[str]:
        return [
            "Plan ITN distribution",
            "I want to distribute bed nets",
            "Help me plan net distribution",
            "Allocate 10000 nets across wards",
            "Plan bed net distribution with 50000 nets"
        ]
    
    @validator('method')
    def validate_method(cls, v):
        if v not in ['composite', 'pca']:
            raise ValueError("Method must be either 'composite' or 'pca'")
        return v
    
    def execute(self, session_id: str) -> ToolExecutionResult:
        """Execute ITN distribution planning"""
        try:
            # Get service container
            container = get_service_container()
            data_service = container.get('data_service')
            
            # Get data handler
            data_handler = data_service.get_handler(session_id)
            if not data_handler:
                return self._create_error_result(
                    "No data available. Please upload data first."
                )
            
            # Check if analysis is complete
            if not self._check_analysis_complete(data_handler):
                return self._create_error_result(
                    "Analysis has not been completed yet. Please run malaria risk analysis first before planning ITN distribution."
                )
            
            # Check if parameters are provided
            if self.total_nets is None:
                return self._create_parameter_request_result()
            
            # Use defaults if not provided
            avg_household_size = self.avg_household_size or 5.0
            urban_threshold = self.urban_threshold or 30.0
            
            # Run ITN distribution calculation
            result = calculate_itn_distribution(
                data_handler=data_handler,
                session_id=session_id,
                total_nets=self.total_nets,
                avg_household_size=avg_household_size,
                urban_threshold=urban_threshold,
                method=self.method
            )
            
            if result['status'] != 'success':
                return self._create_error_result(
                    result.get('message', 'ITN distribution calculation failed')
                )
            
            # Format success message
            stats = result['stats']
            message = self._format_distribution_summary(stats, result)
            
            # Prepare result data
            result_data = {
                'stats': stats,
                'map_path': result.get('map_path'),
                'method_used': self.method,
                'urban_threshold': urban_threshold,
                'household_size': avg_household_size,
                'top_priority_wards': self._get_top_priority_wards(result['prioritized'])
            }
            
            return self._create_success_result(
                message=message,
                data=result_data,
                web_path=result.get('map_path')
            )
            
        except Exception as e:
            logger.error(f"Error in ITN planning: {e}", exc_info=True)
            return self._create_error_result(f"ITN planning failed: {str(e)}")
    
    def _check_analysis_complete(self, data_handler: DataHandler) -> bool:
        """Check if analysis has been completed"""
        # First check session flag (primary indicator)
        try:
            from flask import session
            if session.get('analysis_complete', False):
                logger.info("Analysis complete flag found in session")
                return True
        except Exception as e:
            logger.debug(f"Could not check session flag: {e}")
        
        # Check for vulnerability rankings in data handler
        has_composite = hasattr(data_handler, 'vulnerability_rankings') and data_handler.vulnerability_rankings is not None
        has_pca = hasattr(data_handler, 'vulnerability_rankings_pca') and data_handler.vulnerability_rankings_pca is not None
        
        # Check for unified dataset
        has_unified = hasattr(data_handler, 'unified_dataset') and data_handler.unified_dataset is not None
        
        # Check if analysis results exist in the current dataset
        try:
            from ..core.unified_data_state import get_data_state
            data_state = get_data_state(getattr(data_handler, 'session_id', None))
            if data_state.current_data is not None:
                df = data_state.current_data
                # Check for analysis columns
                has_analysis_columns = ('composite_score' in df.columns or 
                                      'composite_rank' in df.columns or 
                                      'pca_score' in df.columns or 
                                      'pca_rank' in df.columns)
                if has_analysis_columns:
                    logger.info("Analysis columns found in current dataset")
                    return True
        except Exception as e:
            logger.debug(f"Could not check unified data state: {e}")
        
        return has_composite or has_pca or has_unified
    
    def _create_parameter_request_result(self) -> ToolExecutionResult:
        """Create result requesting parameters from user"""
        message = """I'll help you plan ITN (Insecticide-Treated Net) distribution.

To optimize the distribution, I need a few inputs:

1. **Total number of nets available**: How many ITN nets do you have for distribution?
2. **Average household size**: What's the typical household size in this region? (default is 5)
3. **Urban threshold**: What percentage of urbanization should we use as the threshold for prioritizing rural areas? (default is 30%)

Please provide these values and I'll calculate the optimal distribution plan based on the vulnerability rankings."""
        
        return ToolExecutionResult(
            success=True,
            message=message,
            data={'waiting_for_parameters': True},
            metadata={'requires_user_input': True}
        )
    
    def _format_distribution_summary(self, stats: Dict[str, Any], result: Dict[str, Any]) -> str:
        """Format the distribution summary message"""
        prioritized = result.get('prioritized', None)
        
        summary = f"""✅ **ITN Distribution Plan Complete!**

**Allocation Summary:**
- Total nets available: {stats['total_nets']:,}
- Nets allocated: {stats['allocated']:,}
- Remaining: {stats['remaining']:,}

**Coverage Statistics:**
- Population covered: {stats['covered_population']:,} ({stats['coverage_percent']}%)
- Prioritized rural wards: {stats['prioritized_wards']}
- Additional urban wards: {stats['reprioritized_wards']}"""
        
        # Add top priority wards if available
        if prioritized is not None and len(prioritized) > 0:
            top_5 = prioritized.nlargest(5, 'nets_allocated')[['WardName', 'nets_allocated', 'Population']]
            summary += "\n\n**Top 5 Priority Wards:**"
            for idx, ward in top_5.iterrows():
                coverage = (ward['nets_allocated'] * 1.8 / ward['Population'] * 100) if ward['Population'] > 0 else 0
                summary += f"\n{idx+1}. **{ward['WardName']}** - {ward['nets_allocated']} nets ({coverage:.1f}% coverage)"
        
        summary += "\n\n📊 View the interactive distribution map below to see the allocation across all wards."
        
        return summary
    
    def _get_top_priority_wards(self, prioritized) -> List[Dict[str, Any]]:
        """Get top priority wards for metadata"""
        if prioritized is None or len(prioritized) == 0:
            return []
        
        top_wards = []
        for _, ward in prioritized.nlargest(10, 'nets_allocated').iterrows():
            top_wards.append({
                'ward_name': ward['WardName'],
                'nets_allocated': int(ward['nets_allocated']),
                'population': int(ward['Population']) if 'Population' in ward else 0,
                'coverage_percent': float((ward['nets_allocated'] * 1.8 / ward['Population'] * 100)) if ward.get('Population', 0) > 0 else 0
            })
        
        return top_wards