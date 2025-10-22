"""Visualization helper methods for RequestInterpreter."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class VisualizationToolsMixin:
    """Provide visualization-related tool handlers."""

    def _create_vulnerability_map(self, session_id: str, method: str | None = None):
        try:
            if method is None:
                from app.core.tool_registry import get_tool_registry

                tool_registry = get_tool_registry()
                result = tool_registry.execute_tool(
                    'create_vulnerability_map_comparison',
                    session_id=session_id,
                    include_statistics=True,
                )
                if result.get('status') == 'success':
                    return {
                        'response': result.get('message', 'Created side-by-side vulnerability map comparison'),
                        'visualizations': [
                            {
                                'type': 'vulnerability_comparison',
                                'file_path': result.get('data', {}).get('file_path', ''),
                                'path': result.get('data', {}).get('web_path', ''),
                                'url': result.get('data', {}).get('web_path', ''),
                                'title': 'Vulnerability Assessment Comparison',
                                'description': 'Side-by-side comparison of Composite and PCA vulnerability methods',
                            }
                        ],
                        'tools_used': ['create_vulnerability_map_comparison'],
                        'status': 'success',
                    }
                return f"Error creating vulnerability comparison: {result.get('message', 'Unknown error')}"

            result = self.visualization_service.create_vulnerability_map(session_id, method=method)
            message = result.get('message', f'Vulnerability map created using {method} method')
            if result.get('file_path'):
                explanation = self._explain_visualization_universally(
                    result['file_path'], 'vulnerability_map', session_id
                )
                message += f'\n\n{explanation}'
            if result.get('status') == 'success' and result.get('web_path'):
                return {
                    'response': message,
                    'visualizations': [
                        {
                            'type': result.get('visualization_type', 'vulnerability_map'),
                            'file_path': result.get('file_path', ''),
                            'path': result.get('web_path', ''),
                            'url': result.get('web_path', ''),
                            'title': f'Vulnerability Map ({method.title()} Method)',
                            'description': f'Ward vulnerability classification using {method} method',
                        }
                    ],
                    'tools_used': ['create_vulnerability_map'],
                    'status': 'success',
                }
            return f"Error creating vulnerability map: {result.get('message', 'Unknown error')}"
        except Exception as exc:
            return f'Error creating vulnerability map: {exc}'

    def _create_box_plot(self, session_id: str, method: str = 'composite'):
        try:
            result = self.visualization_service.create_box_plot(session_id, method=method)
            message = result.get('message', f'Box plot created for {method} scores')
            if result.get('file_path'):
                explanation = self._explain_visualization_universally(
                    result['file_path'], 'box_plot', session_id
                )
                message += f'\n\n{explanation}'
            if result.get('status') == 'success' and result.get('web_path'):
                return {
                    'response': message,
                    'visualizations': [
                        {
                            'type': result.get('visualization_type', 'box_plot'),
                            'file_path': result.get('file_path', ''),
                            'path': result.get('web_path', ''),
                            'url': result.get('web_path', ''),
                            'title': f'Box Plot ({method.title()} Method)',
                            'description': f'Vulnerability score distribution using {method} method',
                        }
                    ],
                    'tools_used': ['create_box_plot'],
                    'status': 'success',
                }
            return f"Error creating box plot: {result.get('message', 'Unknown error')}"
        except Exception as exc:
            return f'Error creating box plot: {exc}'

    def _create_pca_map(self, session_id: str):
        try:
            result = self.visualization_service.create_pca_map(session_id)
            message = result.get('message', 'PCA vulnerability map created')
            if result.get('file_path'):
                explanation = self._explain_visualization_universally(
                    result['file_path'], 'pca_map', session_id
                )
                message += f'\n\n{explanation}'
            if result.get('status') == 'success' and result.get('web_path'):
                return {
                    'response': message,
                    'visualizations': [
                        {
                            'type': result.get('visualization_type', 'pca_map'),
                            'file_path': result.get('file_path', ''),
                            'path': result.get('web_path', ''),
                            'url': result.get('web_path', ''),
                            'title': 'PCA Vulnerability Map',
                            'description': 'Ward vulnerability classification using PCA method',
                        }
                    ],
                    'tools_used': ['create_pca_map'],
                    'status': 'success',
                }
            return f"Error creating PCA map: {result.get('message', 'Unknown error')}"
        except Exception as exc:
            return f'Error creating PCA map: {exc}'

    def _create_variable_distribution(self, session_id: str, variable_name: str):
        try:
            from app.tools.variable_distribution import VariableDistribution

            tool = VariableDistribution(variable_name=variable_name)
            result = tool.execute(session_id)
            if isinstance(result, Dict):
                return result
            return {'response': str(result), 'status': 'success', 'tools_used': ['create_variable_distribution']}
        except Exception as exc:
            return f'Error creating variable distribution: {exc}'

    def _create_settlement_map(
        self,
        session_id: str,
        ward_name: Optional[str] = None,
        zoom_level: int = 11,
    ):
        try:
            from app.tools.settlement_visualization_tools import CreateSettlementVisualization

            tool = CreateSettlementVisualization(ward_name=ward_name, zoom_level=zoom_level)
            result = tool.execute(session_id)
            return result
        except Exception as exc:
            return {'status': 'error', 'response': f'Error creating settlement map: {exc}'}

    def _show_settlement_statistics(self, session_id: str):
        try:
            from app.tools.settlement_visualization_tools import ShowSettlementStatistics

            tool = ShowSettlementStatistics()
            return tool.execute(session_id)
        except Exception as exc:
            return {'status': 'error', 'response': f'Error showing settlement statistics: {exc}'}

    def _create_urban_extent_map(self, session_id: str):
        try:
            result = self.visualization_service.create_urban_extent_map(session_id)
            if result.get('status') == 'success':
                return result
            return f"Error creating urban extent map: {result.get('message', 'Unknown error')}"
        except Exception as exc:
            return f'Error creating urban extent map: {exc}'

    def _create_decision_tree(self, session_id: str):
        try:
            result = self.visualization_service.create_decision_tree(session_id)
            if result.get('status') == 'success':
                return result
            return f"Error creating decision tree visualization: {result.get('message', 'Unknown error')}"
        except Exception as exc:
            return f'Error creating decision tree visualization: {exc}'

    def _create_composite_score_maps(self, session_id: str):
        try:
            result = self.visualization_service.create_composite_score_maps(session_id)
            if result.get('status') == 'success':
                return result
            return f"Error creating composite score maps: {result.get('message', 'Unknown error')}"
        except Exception as exc:
            return f'Error creating composite score maps: {exc}'

    def _create_composite_vulnerability_map(self, session_id: str):
        try:
            result = self.visualization_service.create_composite_vulnerability_map(session_id)
            if result.get('status') == 'success':
                return result
            return f"Error creating composite vulnerability map: {result.get('message', 'Unknown error')}"
        except Exception as exc:
            return f'Error creating composite vulnerability map: {exc}'

    def _explain_visualization_universally(self, file_path: str, viz_type: str, session_id: str) -> str:
        """Proxy to universal explanation helper with caching and graceful failure."""
        if not file_path:
            return ''

        try:
            if not hasattr(self, '_viz_explainer') or self._viz_explainer is None:
                from app.services.universal_viz_explainer import UniversalVizExplainer

                self._viz_explainer = UniversalVizExplainer()

            explanation = self._viz_explainer.explain_visualization(
                viz_path=file_path,
                viz_type=viz_type,
                session_id=session_id,
            )
            if explanation and explanation.strip():
                return explanation.strip()
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "Visualization explanation failed for %s (type=%s): %s",
                file_path,
                viz_type,
                exc,
            )
        return ''

    def _determine_chart_type_from_query(self, query: str) -> str:
        query_lower = query.lower()
        if 'scatter' in query_lower:
            return 'scatter_plot'
        if 'histogram' in query_lower or 'hist' in query_lower:
            return 'histogram'
        if 'distribution' in query_lower and 'plot' in query_lower or 'distplot' in query_lower:
            return 'histogram'
        if 'box plot' in query_lower or 'boxplot' in query_lower:
            return 'box_plot'
        if 'bar chart' in query_lower or 'bar plot' in query_lower or 'barplot' in query_lower:
            return 'bar_chart'
        if 'line chart' in query_lower or 'line plot' in query_lower or 'lineplot' in query_lower:
            return 'line_plot'
        if 'pie chart' in query_lower or 'pie plot' in query_lower:
            return 'pie_chart'
        if 'heatmap' in query_lower or 'heat map' in query_lower:
            return 'heatmap'
        if 'map' in query_lower or 'choropleth' in query_lower:
            return 'choropleth'
        return 'custom'

__all__ = ['VisualizationToolsMixin']
