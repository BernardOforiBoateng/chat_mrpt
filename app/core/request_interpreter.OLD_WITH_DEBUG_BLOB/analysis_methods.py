"""Analysis and visualization helper methods used by the request interpreter."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import scipy.stats as stats
from sklearn.linear_model import LinearRegression

from app.analysis.engine import AnalysisEngine
from app.tools.base import ToolExecutionResult

logger = logging.getLogger(__name__)

class AnalysisToolsMixin:
    def _run_malaria_risk_analysis(self, session_id: str, variables: Optional[List[str]] = None):
        """Run complete dual-method malaria risk analysis (composite scoring + PCA).
        Use ONLY when analysis has NOT been run yet. DO NOT use if analysis is already complete.
        For ITN planning after analysis, use run_itn_planning instead."""
        logger.info("⚡ TOOL: _run_malaria_risk_analysis called")
        logger.info(f"  🆔 Session ID: {session_id}")
        logger.info(f"  📊 Variables: {variables}")
        try:
            # Use the tool directly to get the comprehensive summary
            from app.tools.complete_analysis_tools import RunMalariaRiskAnalysis
            tool = RunMalariaRiskAnalysis()

            # Execute the tool with proper parameters
            tool_result = tool.execute(
                session_id=session_id,
                composite_variables=variables,  # Use same variables for both methods if provided
                pca_variables=variables
            )

            # Update session to mark analysis as complete on success
            if tool_result.success:
                try:
                    from flask import session
                    session['analysis_complete'] = True
                    session.modified = True
                except:
                    # If not in request context, update conversation history
                    if session_id not in self.conversation_history:
                        self.conversation_history[session_id] = []
                    self.conversation_history[session_id].append({
                        'analysis_complete': True
                    })

            # Get the comprehensive message from tool result
            message = tool_result.message  # This contains the custom summary

            # Auto-explain any visualizations
            visualizations = tool_result.data.get('visualizations', []) if tool_result.data else []
            if visualizations:
                explanations = []
                for viz in visualizations:
                    if viz.get('file_path'):
                        explanation = self._explain_visualization_universally(
                            viz['file_path'], viz.get('type', 'visualization'), session_id
                        )
                        explanations.append(explanation)
                if explanations:
                    message += "\n\n" + "\n\n".join(explanations)

            # Return structured response to bypass interpretation layer
            hint = "\n\n_Shortcut: type **run malaria risk analysis** to rerun this workflow quickly._"
            return {
                'response': message + hint,
                'status': 'success' if tool_result.success else 'error',
                'tools_used': ['run_malaria_risk_analysis'],
                'visualizations': visualizations
            }
        except Exception as e:
            return f"Error running complete analysis: {str(e)}"

    def _run_composite_analysis(self, session_id: str, variables: Optional[List[str]] = None):
        """Run composite scoring malaria risk analysis with equal weights."""
        try:
            result = self.analysis_service.run_composite_analysis(session_id, variables=variables)

            if isinstance(result, dict) and result.get('status') == 'success':
                # Update session to mark analysis as complete
                try:
                    from flask import session
                    session['analysis_complete'] = True
                    session.modified = True
                except:
                    # If not in request context, update conversation history
                    if session_id not in self.conversation_history:
                        self.conversation_history[session_id] = []
                    self.conversation_history[session_id].append({
                        'analysis_complete': True
                    })

                # Run PCA analysis too for comprehensive comparison
                pca_result = self.analysis_service.run_pca_analysis(session_id, variables=variables)

                # Use your proper summary function
                try:
                    from app.tools.complete_analysis_tools import RunMalariaRiskAnalysis

                    analysis_tool = RunMalariaRiskAnalysis()
                    summary = analysis_tool._generate_comprehensive_summary(
                        result, pca_result, {}, 0.0, session_id
                    )

                    return summary

                except Exception as summary_error:
                    logger.error(f"Error calling _generate_summary_from_analysis_results: {summary_error}")
                    logger.error(f"Composite result structure: {result.keys() if result else 'None'}")
                    logger.error(f"PCA result structure: {pca_result.keys() if pca_result else 'None'}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    return "✅ Composite analysis completed successfully. Results are available - please ask for detailed rankings."
            else:
                # Use your existing error formatter
                from app.services.response_formatter import response_formatter
                return response_formatter.format_error_message(
                    result.get('message', 'Composite analysis failed'),
                    'composite_analysis',
                    ['Check data quality', 'Verify variable selection', 'Review analysis parameters']
                )
        except Exception as e:
            from app.services.response_formatter import response_formatter
            return response_formatter.format_error_message(
                str(e),
                'composite_analysis_execution',
                ['Check data upload', 'Verify system configuration', 'Review error logs']
            )

    def _run_pca_analysis(self, session_id: str, variables: Optional[List[str]] = None):
        """Run PCA malaria risk analysis."""
        try:
            result = self.analysis_service.run_pca_analysis(session_id, variables=variables)

            # Update session to mark analysis as complete on success
            if result.get('status') == 'success':
                try:
                    from flask import session
                    session['analysis_complete'] = True
                    session.modified = True
                except:
                    # If not in request context, update conversation history
                    if session_id not in self.conversation_history:
                        self.conversation_history[session_id] = []
                    self.conversation_history[session_id].append({
                        'analysis_complete': True
                    })

            # Format PCA results properly
            from app.services.response_formatter import response_formatter

            if isinstance(result, dict):
                formatted_result = response_formatter.format_analysis_result(result, 'pca')
                return formatted_result
            else:
                return result.get('message', 'PCA analysis completed successfully')
        except Exception as e:
            return f"Error running PCA analysis: {str(e)}"

    def _create_vulnerability_map(self, session_id: str, method: str = None):
        """Create vulnerability/risk assessment choropleth map showing ward risk rankings from completed analysis.

        IMPORTANT: Use this tool ONLY when user explicitly requests:
        - "vulnerability map"
        - "risk map"
        - "create vulnerability map comparison"
        - "show vulnerability assessment"

        DO NOT use for mapping raw data variables (use create_variable_distribution for that).

        This requires completed malaria risk analysis with composite_rank or pca_rank columns.
        If method is not specified, creates a side-by-side comparison of both methods.
        If method is specified ('composite' or 'pca'), creates a single map for that method.
        """
        try:
            # If no method specified, use the comparison tool
            if method is None:
                # Use the new comparison tool from the tool registry
                from app.core.tool_registry import get_tool_registry
                tool_registry = get_tool_registry()

                # Execute the comparison tool
                result = tool_registry.execute_tool(
                    'create_vulnerability_map_comparison',  # This tool overrides get_tool_name()
                    session_id=session_id,
                    include_statistics=True
                )

                if result.get('status') == 'success':
                    # Convert tool result to expected format
                    return {
                        'response': result.get('message', 'Created side-by-side vulnerability map comparison'),
                        'visualizations': [{
                            'type': 'vulnerability_comparison',
                            'file_path': result.get('data', {}).get('file_path', ''),
                            'path': result.get('data', {}).get('web_path', ''),
                            'url': result.get('data', {}).get('web_path', ''),
                            'title': "Vulnerability Assessment Comparison",
                            'description': "Side-by-side comparison of Composite and PCA vulnerability methods"
                        }],
                        'tools_used': ['create_vulnerability_map_comparison'],
                        'status': 'success'
                    }
                else:
                    return f"Error creating vulnerability comparison: {result.get('message', 'Unknown error')}"

            # Otherwise use the specific method requested
            else:
                result = self.visualization_service.create_vulnerability_map(session_id, method=method)
                message = result.get('message', f'Vulnerability map created using {method} method')

                # Auto-explain the visualization if file_path exists
                if result.get('file_path'):
                    explanation = self._explain_visualization_universally(
                        result['file_path'], 'vulnerability_map', session_id
                    )
                    message += f"\\n\\n{explanation}"

                # Return structured response if successful
                if result.get('status') == 'success' and result.get('web_path'):
                    return {
                        'response': message,
                        'visualizations': [{
                            'type': result.get('visualization_type', 'vulnerability_map'),
                            'file_path': result.get('file_path', ''),
                            'path': result.get('web_path', ''),
                            'url': result.get('web_path', ''),
                            'title': f"Vulnerability Map ({method.title()} Method)",
                            'description': f"Ward vulnerability classification using {method} method"
                        }],
                        'tools_used': ['create_vulnerability_map'],
                        'status': 'success'
                    }
                else:
                    return f"Error creating vulnerability map: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Error creating vulnerability map: {str(e)}"

    def _create_box_plot(self, session_id: str, method: str = 'composite'):
        """Create box plots showing vulnerability score distributions."""
        try:
            result = self.visualization_service.create_box_plot(session_id, method=method)
            message = result.get('message', f'Box plot created for {method} scores')

            # Auto-explain the visualization if file_path exists
            if result.get('file_path'):
                explanation = self._explain_visualization_universally(
                    result['file_path'], 'box_plot', session_id
                )
                message += f"\\n\\n{explanation}"

            # Return structured response if successful
            if result.get('status') == 'success' and result.get('web_path'):
                return {
                    'response': message,
                    'visualizations': [{
                        'type': result.get('visualization_type', 'box_plot'),
                        'file_path': result.get('file_path', ''),
                        'path': result.get('web_path', ''),
                        'url': result.get('web_path', ''),
                        'title': f"Box Plot ({method.title()} Method)",
                        'description': f"Vulnerability score distribution using {method} method"
                    }],
                    'tools_used': ['create_box_plot'],
                    'status': 'success'
                }
            else:
                return f"Error creating box plot: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Error creating box plot: {str(e)}"

    def _create_pca_map(self, session_id: str):
        """Create PCA-based vulnerability map."""
        try:
            result = self.visualization_service.create_pca_map(session_id)
            message = result.get('message', 'PCA vulnerability map created')

            # Auto-explain the visualization if file_path exists
            if result.get('file_path'):
                explanation = self._explain_visualization_universally(
                    result['file_path'], 'pca_map', session_id
                )
                message += f"\\n\\n{explanation}"

            # Return structured response if successful
            if result.get('status') == 'success' and result.get('web_path'):
                return {
                    'response': message,
                    'visualizations': [{
                        'type': result.get('visualization_type', 'pca_map'),
                        'file_path': result.get('file_path', ''),
                        'path': result.get('web_path', ''),
                        'url': result.get('web_path', ''),
                        'title': "PCA Vulnerability Map",
                        'description': "Ward vulnerability classification using PCA method"
                    }],
                    'tools_used': ['create_pca_map'],
                    'status': 'success'
                }
            else:
                return f"Error creating PCA map: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Error creating PCA map: {str(e)}"

    def _create_variable_distribution(self, session_id: str, variable_name: str):
        """Create an interactive choropleth map showing the spatial distribution of a RAW DATA COLUMN.

        Use this ONLY for mapping existing columns from uploaded data (TPR, rainfall, elevation, etc).
        DO NOT use for vulnerability/risk maps (use create_vulnerability_map for that).

        REQUIRES: 'variable_name' parameter with the exact column name to visualize.

        Examples:
        - User: "plot the map distribution for mean_rainfall" -> Use variable_name='mean_rainfall'
        - User: "show pfpr on map" -> Use variable_name='pfpr'
        - User: "map TPR distribution" -> Use variable_name='TPR'

        DO NOT use for:
        - "vulnerability map" (use create_vulnerability_map)
        - "risk map" (use create_vulnerability_map)
        """
        try:
            from app.tools.variable_distribution import VariableDistribution

            # Create the tool instance
            tool = VariableDistribution(variable_name=variable_name)

            # Execute the tool
            result = tool.execute(session_id)

            if result.success:
                message = result.message

                # Auto-explain the visualization if it was created
                if result.data and result.data.get('file_path'):
                    explanation = self._explain_visualization_universally(
                        result.data['file_path'], 'variable_distribution', session_id
                    )
                    message += f"\n\n{explanation}"

                # Return structured response with visualization data
                return {
                    'response': message,
                    'visualizations': [{
                        'type': result.data.get('chart_type', 'variable_distribution'),
                        'file_path': result.data.get('file_path', ''),
                        'path': result.data.get('web_path', ''),  # Frontend expects 'path' key
                        'url': result.data.get('web_path', ''),   # Also provide 'url' for compatibility
                        'title': f"{result.data.get('variable', 'Variable')} Distribution",
                        'description': f"Spatial distribution of {result.data.get('variable', 'variable')} across study area"
                    }] if result.data else [],
                    'tools_used': ['create_variable_distribution'],
                    'status': 'success'
                }
            else:
                return f"Error creating variable distribution: {result.message}"
        except Exception as e:
            return f"Error creating variable distribution: {str(e)}"

    def _execute_data_query(self, session_id: str, query: str, code: Optional[str] = None):
        """Execute complex data analysis using Python code. Use for statistics, correlations, or advanced analysis.
        The 'query' parameter is REQUIRED and should describe what analysis to perform.
        Examples: query='check data quality', query='correlation between rainfall and malaria', query='statistical summary'"""
        try:
            # Check if data is available via data service first
            data_handler = self.data_service.get_handler(session_id)
            if not data_handler or not hasattr(data_handler, 'csv_data') or data_handler.csv_data is None:
                return "Error executing query: No data available. Please upload data first."

            # Initialize conversational data access for this session
            # Always create a new instance to ensure proper session context
            logger.info(f"Creating ConversationalDataAccess for session: {session_id}")
            from app.services.conversational_data_access import ConversationalDataAccess
            conversational_data_access = ConversationalDataAccess(session_id, self.llm_manager)

            if code:
                logger.info(f"Executing provided code: {code}")
                result = conversational_data_access.execute_code(code)
            else:
                logger.info(f"Processing query: {query}")
                result = conversational_data_access.process_query(query)

            if result.get('success'):
                # Get the formatted output from the executed code
                output = result.get('output', '').strip()
                plot_data = result.get('plot_data')

                # Return structured response with visualizations
                response_data = {
                    'response': output if output else f"Query executed successfully: {query}",
                    'visualizations': [],
                    'tools_used': ['execute_data_query'],
                    'status': 'success'
                }

                # Add visualization if plot was generated
                if plot_data:
                    # Determine specific chart type from query context
                    viz_type = self._determine_chart_type_from_query(query)
                    response_data['visualizations'].append({
                        'type': viz_type,
                        'data': plot_data,
                        'title': f'Analysis Visualization - {query[:50]}...' if len(query) > 50 else f'Analysis Visualization - {query}'
                    })

                return response_data
            else:
                error_msg = f"Error executing query: {result.get('error', 'Unknown error')}"
                return error_msg
        except Exception as e:
            return f"Error in data query: {str(e)}"

    def _execute_sql_query(self, session_id: str, query: str):
        """Execute SQL queries on the dataset.
        REQUIRES: 'query' parameter with a valid SQL string. The table name is always 'df'.
        Use this when users ask to see data, list columns, or filter records.
        User asks: 'what are the variables in my data?' -> Use query: 'SELECT * FROM df LIMIT 1'
        User asks: 'show top 5 wards by pfpr' -> Use query: 'SELECT * FROM df ORDER BY pfpr DESC LIMIT 5'"""
        try:
            # For now, continue using the conversational data access
            # The interpretation will happen in the streaming handler
            logger.info(f"Executing SQL query: {query}")
            from app.services.conversational_data_access import ConversationalDataAccess
            conversational_data_access = ConversationalDataAccess(session_id, self.llm_manager)

            # Use the process_sql_query method which handles all stages properly
            result = conversational_data_access.process_sql_query(query)

            if result.get('success'):
                return result.get('output', 'Query executed successfully')
            else:
                return f"Error executing SQL: {result.get('error', 'Unknown error')}"
        except Exception as e:
            logger.error(f"SQL query error: {e}")
            return f"Error executing SQL query: {str(e)}"

    def _determine_chart_type_from_query(self, query: str) -> str:
        """Determine specific chart type from user query to avoid visualization conflicts."""
        query_lower = query.lower()

        # Check for specific chart types mentioned in the query
        if 'scatter' in query_lower:
            return 'scatter_plot'
        elif 'histogram' in query_lower or 'hist' in query_lower:
            return 'histogram'
        elif ('distribution' in query_lower and 'plot' in query_lower) or 'distplot' in query_lower:
            return 'histogram'  # Most distribution plots are histograms
        elif 'box plot' in query_lower or 'boxplot' in query_lower:
            return 'box_plot'
        elif 'bar chart' in query_lower or 'bar plot' in query_lower or 'barplot' in query_lower:
            return 'bar_chart'
        elif 'line chart' in query_lower or 'line plot' in query_lower or 'lineplot' in query_lower:
            return 'line_plot'
        elif 'pie chart' in query_lower or 'pie plot' in query_lower:
            return 'pie_chart'
        elif 'heatmap' in query_lower or 'heat map' in query_lower:
            return 'heatmap'
        elif 'density' in query_lower and 'plot' in query_lower:
            return 'density_plot'
        elif 'violin' in query_lower:
            return 'violin_plot'
        elif 'correlation' in query_lower and 'plot' in query_lower:
            return 'scatter_plot'  # Correlation plots are usually scatter plots
        else:
            # Return a unique type for each general plot to prevent conflicts
            import time
            return f'conversational_plot_{int(time.time())}'

    def _explain_analysis_methodology(self, session_id: str, method: str = 'both'):
        """Explain how malaria risk analysis methodologies work (composite scoring, PCA, or both)."""
        try:
            # Use LLM to generate methodology explanation
            if method == 'composite':
                explanation = """**Composite Scoring Methodology**

Composite scoring combines multiple malaria risk indicators into a single vulnerability score:

1. **Variable Selection**: Selects scientifically-validated variables based on Nigerian geopolitical zones
2. **Normalization**: Standardizes all variables to 0-1 scale for fair comparison
3. **Equal Weighting**: All variables contribute equally to the final score
4. **Aggregation**: Sums normalized values to create composite vulnerability score
5. **Ranking**: Ranks wards from highest to lowest risk for intervention targeting

This method is transparent, interpretable, and follows WHO guidelines for malaria stratification."""

            elif method == 'pca':
                explanation = """**Principal Component Analysis (PCA) Methodology**

PCA reduces dimensionality while preserving variance in malaria risk data:

1. **Data Standardization**: Centers and scales all variables
2. **Covariance Analysis**: Identifies relationships between variables
3. **Component Extraction**: Finds principal components that explain maximum variance
4. **Weight Calculation**: Automatically determines variable importance
5. **Score Generation**: Creates data-driven vulnerability scores
6. **Interpretation**: First component typically captures overall malaria risk

This method is statistically robust and reveals hidden patterns in the data."""

            else:  # both
                explanation = """**Dual-Method Malaria Risk Analysis**

ChatMRPT uses both composite scoring and PCA for comprehensive assessment:

**Composite Scoring**: Transparent, equal-weighted approach following WHO guidelines
- Pros: Interpretable, policy-friendly, scientifically grounded
- Use when: Clear intervention priorities needed

**PCA Analysis**: Statistical approach revealing data patterns
- Pros: Objective, captures complex relationships, statistically robust
- Use when: Exploring underlying risk structures

**Comparison**: Both methods often agree on high-risk areas but may differ in rankings. Use both for robust decision-making and to validate findings."""

            return explanation
        except Exception as e:
            return f"Error explaining methodology: {str(e)}"

    def _create_settlement_map(self, session_id: str, ward_name: str = None, zoom_level: int = 11, **kwargs):
        """Create interactive settlement map showing building types for specific wards."""
        try:
            # Filter out any invalid parameters that LLM might pass
            valid_params = {'session_id': session_id}
            if ward_name:
                valid_params['ward_name'] = ward_name
            if zoom_level:
                valid_params['zoom_level'] = zoom_level

            from app.tools.settlement_visualization_tools import create_settlement_map

            result = create_settlement_map(**valid_params)

            if result.get('status') == 'success':
                message = result.get('message', f'Settlement map created')

                # Add ward-specific information
                if ward_name:
                    message += f" for {ward_name} ward"

                # Auto-explain the visualization if file_path exists
                if result.get('file_path'):
                    explanation = self._explain_visualization_universally(
                        result['file_path'], 'settlement_map', session_id
                    )
                    message += f"\n\n{explanation}"

                # Return structured response
                if result.get('web_path'):
                    return {
                        'response': message,
                        'visualizations': [{
                            'type': 'settlement_map',
                            'file_path': result.get('file_path', ''),
                            'path': result.get('web_path', ''),
                            'url': result.get('web_path', ''),
                            'title': f"Settlement Map{' - ' + ward_name if ward_name else ''}",
                            'description': f"Building classification map showing settlement types{' for ' + ward_name + ' ward' if ward_name else ''}"
                        }],
                        'tools_used': ['create_settlement_map'],
                        'status': 'success'
                    }
                else:
                    return message
            else:
                return f"Error creating settlement map: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Error creating settlement map: {str(e)}"

    def _show_settlement_statistics(self, session_id: str):
        """Show comprehensive statistics about available settlement data."""
        try:
            from app.tools.settlement_visualization_tools import show_settlement_statistics

            result = show_settlement_statistics(session_id)

            if result.get('status') == 'success':
                message = result.get('message', 'Settlement statistics retrieved')

                # Enhance with AI explanation if available
                if result.get('ai_response'):
                    message = result['ai_response']

                return {
                    'response': message,
                    'tools_used': ['show_settlement_statistics'],
                    'status': 'success',
                    'data': result.get('data', {})
                }
            else:
                return f"Error getting settlement statistics: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Error getting settlement statistics: {str(e)}"

    def _create_urban_extent_map(self, session_id: str, threshold: float = 30.0):
        """Create urban extent classification map showing urban vs rural areas."""
        try:
            from app.core.tool_registry import get_tool_registry
            tool_registry = get_tool_registry()

            result = tool_registry.execute_tool(
                'createurbanextentmap',
                session_id=session_id,
                urban_threshold=threshold
            )

            if result.get('status') == 'success':
                return {
                    'response': result.get('message', 'Urban extent map created'),
                    'visualizations': [{
                        'type': 'urban_extent_map',
                        'file_path': result.get('data', {}).get('file_path', ''),
                        'path': result.get('data', {}).get('web_path', ''),
                        'url': result.get('data', {}).get('web_path', ''),
                        'title': 'Urban Extent Classification',
                        'description': f'Urban areas (>{threshold}% built-up) vs rural areas'
                    }],
                    'tools_used': ['createurbanextentmap'],
                    'status': 'success'
                }
            else:
                return f"Error creating urban extent map: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Error creating urban extent map: {str(e)}"

    def _create_decision_tree(self, session_id: str):
        """Create decision tree visualization showing risk factor logic."""
        try:
            from app.core.tool_registry import get_tool_registry
            tool_registry = get_tool_registry()

            result = tool_registry.execute_tool(
                'createdecisiontree',
                session_id=session_id
            )

            if result.get('status') == 'success':
                return {
                    'response': result.get('message', 'Decision tree visualization created'),
                    'visualizations': [{
                        'type': 'decision_tree',
                        'file_path': result.get('data', {}).get('file_path', ''),
                        'path': result.get('data', {}).get('web_path', ''),
                        'url': result.get('data', {}).get('web_path', ''),
                        'title': 'Risk Factor Decision Tree',
                        'description': 'Decision logic for malaria risk assessment'
                    }],
                    'tools_used': ['createdecisiontree'],
                    'status': 'success'
                }
            else:
                return f"Error creating decision tree: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Error creating decision tree: {str(e)}"


    def _create_composite_score_maps(self, session_id: str):
        """Create composite score maps with individual model breakdowns."""
        try:
            from app.core.tool_registry import get_tool_registry
            tool_registry = get_tool_registry()

            result = tool_registry.execute_tool(
                'createcompositescoremaps',
                session_id=session_id
            )

            if result.get('status') == 'success':
                return {
                    'response': result.get('message', 'Composite score maps created'),
                    'visualizations': [{
                        'type': 'composite_score_maps',
                        'file_path': result.get('data', {}).get('file_path', ''),
                        'path': result.get('data', {}).get('web_path', ''),
                        'url': result.get('data', {}).get('web_path', ''),
                        'title': 'Composite Score Model Breakdown',
                        'description': 'Individual model contributions to composite malaria risk score'
                    }],
                    'tools_used': ['createcompositescoremaps'],
                    'status': 'success'
                }
            else:
                return f"Error creating composite score maps: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Error creating composite score maps: {str(e)}"

    def _create_composite_vulnerability_map(self, session_id: str):
        """Create vulnerability map specifically for composite method."""
        try:
            from app.core.tool_registry import get_tool_registry
            tool_registry = get_tool_registry()

            result = tool_registry.execute_tool(
                'createcompositevulnerabilitymap',  # lowercase tool name
                session_id=session_id
            )

            if result.get('status') == 'success':
                return {
                    'response': result.get('message', 'Composite vulnerability map created'),
                    'visualizations': [{
                        'type': 'composite_vulnerability_map',
                        'file_path': result.get('data', {}).get('file_path', ''),
                        'path': result.get('data', {}).get('web_path', ''),
                        'url': result.get('data', {}).get('web_path', ''),
                        'title': 'Composite Vulnerability Map',
                        'description': 'Ward vulnerability classification using composite method'
                    }],
                    'tools_used': ['createcompositevulnerabilitymap'],
                    'status': 'success'
                }
            else:
                return f"Error creating composite vulnerability map: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Error creating composite vulnerability map: {str(e)}"

    def _explain_visualization_universally(self, file_path: str, viz_type: str, session_id: str) -> str:
        """Generate a short explanation for the given visualization.

        This wraps :class:`UniversalVizExplainer` but shields the main request
        flow from failures—if the explainer cannot run we simply return an empty
        string rather than breaking the calling tool pipeline.
        """
        if not file_path:
            return ""

        try:
            if not hasattr(self, "_viz_explainer") or self._viz_explainer is None:
                from app.services.universal_viz_explainer import UniversalVizExplainer

                self._viz_explainer = UniversalVizExplainer()

            explanation = self._viz_explainer.explain_visualization(
                viz_path=file_path,
                viz_type=viz_type,
                session_id=session_id,
            )

            if explanation and explanation.strip():
                return explanation.strip()

        except Exception as exc:  # pragma: no cover - best-effort helper
            logger.warning(
                "Visualization explanation failed for %s (type=%s): %s",
                file_path,
                viz_type,
                exc,
            )

        return ""

