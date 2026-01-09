"""Session context helpers and workflow utilities for the request interpreter."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, Optional

from flask import current_app

logger = logging.getLogger(__name__)

class ContextMixin:
    def _get_session_context(self, session_id: str, session_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get session context using SessionContextService which properly loads data files."""
        # Use SessionContextService if available (properly loads CSVs and creates current_data)
        if self.context_service:
            try:
                context = self.context_service.get_context(session_id, session_data)
                logger.info(f"📂 SessionContextService loaded context for {session_id}:")
                logger.info(f"  - Data loaded: {context.get('data_loaded', False)}")
                logger.info(f"  - CSV loaded: {context.get('csv_loaded', False)}")
                logger.info(f"  - Shapefile loaded: {context.get('shapefile_loaded', False)}")
                logger.info(f"  - Analysis complete: {context.get('analysis_complete', False)}")
                logger.info(f"  - Current data: {context.get('current_data', 'None')}")
                logger.info(f"  - Columns: {len(context.get('columns', []))} found")
                return context
            except Exception as e:
                logger.warning(f"SessionContextService failed: {e}, falling back to manual detection")

        # Fallback: manual file checking (legacy behavior)
        from pathlib import Path
        session_folder = Path(f"instance/uploads/{session_id}")
        if session_folder.exists():
            # Check for CSV files in root folder
            has_csv = any(f.suffix in ['.csv', '.xlsx', '.xls'] for f in session_folder.glob('*'))

            # Check for shapefiles - look in both root AND shapefile/ subdirectory
            has_shapefile = any(f.suffix == '.shp' for f in session_folder.glob('*'))
            shapefile_dir = session_folder / 'shapefile'
            if not has_shapefile and shapefile_dir.exists():
                has_shapefile = any(f.suffix == '.shp' for f in shapefile_dir.glob('*'))

            # Check for .zip files containing shapefiles
            if not has_shapefile:
                has_shapefile = any(f.suffix == '.zip' and 'shapefile' in f.name.lower() for f in session_folder.glob('*'))

            analysis_marker = session_folder / '.analysis_complete'

            # Load CSV to extract column names and row count
            columns = []
            current_data = "No data uploaded"
            if has_csv:
                try:
                    import pandas as pd
                    # Try common file patterns in priority order
                    file_patterns = ['unified_dataset.csv', 'raw_data.csv', 'data_analysis.csv', 'uploaded_data.csv']
                    df = None
                    for pattern in file_patterns:
                        csv_path = session_folder / pattern
                        if csv_path.exists():
                            df = pd.read_csv(csv_path)
                            columns = df.columns.tolist()
                            current_data = f"{len(df)} rows"
                            logger.info(f"📋 Loaded {len(df)} rows, {len(columns)} columns from {pattern}")
                            break

                    # Fallback: load any CSV file
                    if not columns:
                        csv_files = list(session_folder.glob('*.csv'))
                        if csv_files and not csv_files[0].name.startswith('.'):
                            df = pd.read_csv(csv_files[0])
                            columns = df.columns.tolist()
                            current_data = f"{len(df)} rows"
                            logger.info(f"📋 Loaded {len(df)} rows, {len(columns)} columns from {csv_files[0].name}")
                except Exception as e:
                    logger.warning(f"Could not load CSV: {e}")
                    current_data = "Data files found but could not be loaded"

            logger.info(f"📂 File-based session detection for {session_id}:")
            logger.info(f"  - CSV files found: {has_csv}")
            logger.info(f"  - Shapefile found: {has_shapefile}")
            logger.info(f"  - Analysis complete: {analysis_marker.exists()}")
            logger.info(f"  - Current data: {current_data}")

            return {
                'data_loaded': has_csv or has_shapefile,
                'csv_loaded': has_csv,
                'shapefile_loaded': has_shapefile,
                'analysis_complete': analysis_marker.exists(),
                'current_data': current_data,
                'state_name': session_data.get('state_name', 'Not specified') if session_data else 'Not specified',
                'columns': columns,
                'session_id': session_id
            }

        logger.warning(f"⚠️ Session folder not found: {session_folder}")
        return {'data_loaded': False, 'state_name': 'Not specified', 'current_data': 'No data uploaded'}

    def _handle_special_workflows(self, user_message: str, session_id: str, session_data: Dict[str, Any] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """Handle keyword-triggered workflow transitions (TPR, etc.)."""

        if not user_message:
            return None

        normalized = user_message.strip().lower()

        # --- TPR workflow trigger -------------------------------------------------
        if 'tpr' in normalized and any(word in normalized for word in ['start', 'begin', 'launch', 'run', 'initiate']):
            try:
                from app.runtime.tpr.workflow import get_tpr_status, start_tpr_workflow

                status = get_tpr_status(session_id)
                if status.get('active'):
                    return {
                        'response': "TPR workflow is already running. Let's continue from where we stopped.",
                        'status': 'success',
                        'workflow': 'tpr',
                        'stage': status.get('stage'),
                        'tools_used': ['start_tpr_workflow'],
                    }

                result = start_tpr_workflow(session_id)
                if not result:
                    return {
                        'response': "I couldn't start the TPR workflow because I couldn't find uploaded TPR data. Please upload your dataset first.",
                        'status': 'error',
                        'workflow': 'tpr',
                    }

                response_text = result.get('message') or result.get('response') or "TPR workflow started."
                status_flag = 'success' if result.get('success', True) else result.get('status', 'error')

                return {
                    'response': response_text,
                    'status': status_flag,
                    'visualizations': result.get('visualizations', []),
                    'download_links': result.get('download_links', []),
                    'tools_used': ['start_tpr_workflow'],
                    'workflow': result.get('workflow', 'tpr'),
                    'stage': result.get('stage'),
                }
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.error("Failed to start TPR workflow: %s", exc)
                return {
                    'response': 'I ran into an issue starting the TPR workflow. Please try uploading your TPR data again.',
                    'status': 'error',
                }

        return None

    def _run_itn_planning(self, session_id: str, total_nets: Optional[int] = 10000, avg_household_size: Optional[float] = 5.0, urban_threshold: Optional[float] = 30.0, method: str = 'composite'):
        """Plan ITN (Insecticide-Treated Net) distribution AFTER analysis is complete.
        Use this tool when user wants to plan ITN distribution, allocate bed nets, or create intervention plans.
        This tool uses existing analysis rankings - DO NOT run analysis again if already complete.
        Keywords: ITN, bed nets, net distribution, intervention planning, allocate nets."""
        logger.info("🛏️ ITN: _run_itn_planning called")
        logger.info(f"  🆔 Session ID: {session_id}")
        logger.info(f"  🔢 Total Nets: {total_nets}")
        logger.info(f"  🏠 Household Size: {avg_household_size}")
        logger.info(f"  🏙️ Urban Threshold: {urban_threshold}")
        logger.info(f"  📊 Method: {method}")
        try:
            # Check if analysis is complete first
            session_context = self._get_session_context(session_id)
            analysis_complete = session_context.get('analysis_complete', False)

            # CRITICAL FIX: Also check for physical evidence (marker file)
            if not analysis_complete:
                from pathlib import Path
                marker_file = Path(f"instance/uploads/{session_id}/.analysis_complete")
                if marker_file.exists():
                    analysis_complete = True
                    logger.info(f"✅ Found .analysis_complete marker, overriding flag for ITN planning in {session_id}")

                    # Update state to match evidence
                    try:
                        from app.core.workflow_state_manager import WorkflowStateManager
                        state_manager = WorkflowStateManager(session_id)
                        state_manager.update_state({
                            'analysis_complete': True
                        }, transition_reason="ITN tool found analysis evidence")
                    except Exception as e:
                        logger.warning(f"Could not update state: {e}")

            data_handler = self.data_service.get_handler(session_id)
            if not data_handler:
                return 'No data available. Please run analysis first.'

            ######################## NEW: DIRECT RANKINGS CHECK ########################
            # Just check the unified dataset - it has everything we need
            if hasattr(data_handler, 'unified_dataset') and data_handler.unified_dataset is not None:
                has_rankings = 'composite_rank' in data_handler.unified_dataset.columns or 'overall_rank' in data_handler.unified_dataset.columns
            else:
                # Try to load unified dataset
                data_handler._load_unified_dataset()
                has_rankings = (data_handler.unified_dataset is not None and 
                               ('composite_rank' in data_handler.unified_dataset.columns or 'overall_rank' in data_handler.unified_dataset.columns))

            if has_rankings:
                analysis_complete = True  # Override flag if rankings exist
                logger.info(f"Overrode analysis_complete to True based on unified dataset rankings for session {session_id}")
            ############################################################################

            if not analysis_complete:
                return 'Analysis has not been completed yet. Please run the malaria risk analysis first before planning ITN distribution.'

            from app.analysis.itn_pipeline import calculate_itn_distribution
            data_handler = self.data_service.get_handler(session_id)
            if not data_handler:
                return 'No data available. Please run analysis first.'

            # Check if unified dataset exists (it has all the rankings we need)
            if not hasattr(data_handler, 'unified_dataset') or data_handler.unified_dataset is None:
                # Try to load it
                data_handler._load_unified_dataset()
                if data_handler.unified_dataset is None:
                    return 'Analysis rankings not found. Please run the malaria risk analysis first to generate vulnerability rankings.'

            # Use the ITN planning tool to get comprehensive results with download links
            from app.tools.itn_planning_tools import PlanITNDistribution

            # Create tool instance with parameters
            tool = PlanITNDistribution(
                total_nets=total_nets if total_nets != 10000 else None,
                avg_household_size=avg_household_size,
                urban_threshold=urban_threshold,
                method=method
            )

            # Execute the tool
            tool_result = tool.execute(session_id=session_id)

            if not tool_result.success:
                return {
                    'response': tool_result.message,
                    'status': 'error',
                    'tools_used': ['run_itn_planning']
                }

            # Extract visualizations and download links from tool result
            visualizations = []
            if tool_result.web_path:
                visualizations.append({
                    'type': 'itn_map',
                    'path': tool_result.web_path,
                    'url': tool_result.web_path
                })

            # Return structured response with download links
            return {
                'response': tool_result.message,
                'visualizations': visualizations,
                'download_links': tool_result.download_links if hasattr(tool_result, 'download_links') else [],
                'tools_used': ['run_itn_planning'],
                'status': 'success'
            }
        except Exception as e:
            return f"Error planning ITN: {str(e)}"

    def _analyze_data_with_python(self, session_id: str, query: str) -> Dict[str, Any]:
        """
        Execute custom Python analysis on user data via DataExplorationAgent.

        Use this tool for ALL data analysis queries including:

        STATISTICAL TESTS (scipy.stats):
        - ANOVA tests (f_oneway, kruskal)
        - t-tests (ttest_ind, ttest_rel, mannwhitneyu)
        - Correlation tests (pearsonr, spearmanr)
        - Chi-square tests (chi2_contingency)
        - Normality tests (shapiro, kstest)

        MACHINE LEARNING (sklearn):
        - Clustering (KMeans, DBSCAN, AgglomerativeClustering)
        - Dimensionality reduction (PCA, NMF, t-SNE)
        - Regression (LinearRegression, LogisticRegression, RandomForest)
        - Classification (DecisionTree, SVM, GradientBoosting)
        - Preprocessing (StandardScaler, MinMaxScaler)

        DATA ANALYSIS (pandas, numpy):
        - Filtering, aggregation, groupby operations
        - Custom calculations and transformations
        - Statistical summaries (describe, quantile, etc.)
        - Custom data queries (e.g., "show top 10 wards by population")

        GEOSPATIAL ANALYSIS (geopandas):
        - Spatial joins and overlays
        - Distance calculations
        - Coordinate transformations
        - Geospatial queries

        VISUALIZATIONS (plotly):
        - Interactive charts (scatter, bar, line, heatmap)
        - Statistical plots (box, violin, histogram)
        - Geospatial maps

        Available libraries: pandas, numpy, scipy, sklearn, geopandas, plotly, matplotlib, seaborn

        Args:
            session_id: Session identifier
            query: Natural language description of analysis to perform

        Returns:
            Dict with response, visualizations, tools_used (matching RI format)
        """
        logger.info(f"🐍 TOOL: analyze_data_with_python called")
        logger.info(f"  Session: {session_id}")
        logger.info(f"  Query: {query[:100]}...")

        try:
            # Reuse agent if exists, create if not (for conversation memory)
            if session_id not in self.data_agents:
                from app.data_analysis_v3.core.data_exploration_agent import DataExplorationAgent
                logger.info(f"🆕 Creating new DataExplorationAgent for session {session_id}")
                self.data_agents[session_id] = DataExplorationAgent(session_id=session_id)
            else:
                logger.info(f"♻️ Reusing existing DataExplorationAgent for session {session_id} (conversation memory active)")

            # Get the cached agent
            agent = self.data_agents[session_id]

            # Execute query (synchronous interface)
            result = agent.analyze_sync(query)

            # Format result to match RI tool contract
            # CRITICAL: RI expects 'response', agent returns 'message'
            return {
                'status': 'success' if result.get('success', False) else 'error',  # Map boolean 'success' to string 'status'
                'response': result.get('message', ''),  # Map 'message' to 'response'
                'visualizations': result.get('visualizations', []),
                'tools_used': ['analyze_data_with_python']
            }

        except Exception as e:
            logger.error(f"Error in analyze_data_with_python: {e}", exc_info=True)
            return {
                'status': 'error',
                'response': f'I encountered an error analyzing the data: {str(e)}',
                'tools_used': ['analyze_data_with_python']
            }

    # Helper Methods
        def _run_data_quality_check(self, session_id: str):
            """Check data quality including missing values, duplicates, and statistics."""
            try:
                import pandas as pd
                from pathlib import Path

                # Load the data
                session_folder = Path(f'instance/uploads/{session_id}')
                raw_data_path = session_folder / 'raw_data.csv'

                if not raw_data_path.exists():
                    return "No data file found. Please upload data first."

                df = pd.read_csv(raw_data_path)

                # Calculate statistics
                total_missing = df.isnull().sum().sum()
                duplicates = df.duplicated().sum()
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                categorical_cols = df.select_dtypes(include=['object']).columns.tolist()

                # Find malaria-relevant variables
                malaria_vars = []
                env_vars = []
                risk_vars = []

                for col in df.columns:
                    col_lower = col.lower()
                    if 'tpr' in col_lower or 'test' in col_lower or 'positive' in col_lower:
                        malaria_vars.append(col)
                    elif any(x in col_lower for x in ['evi', 'ndvi', 'soil', 'rain', 'temp', 'humid']):
                        env_vars.append(col)
                    elif any(x in col_lower for x in ['urban', 'housing', 'population', 'density']):
                        risk_vars.append(col)

                # Format response
                response = f"""**Data Quality Check Complete**

    📊 Your dataset has {total_missing} total missing values (minimal impact on analysis).

    ✅ **{'No duplicate entries' if duplicates == 0 else f'{duplicates} duplicate entries found'}** - {'each ward has unique data' if duplicates == 0 else 'consider removing duplicates'}.

    **Key Dataset Characteristics:**
    • Both numeric indicators ({len(numeric_cols)}) and categorical identifiers ({len(categorical_cols)})

    **Malaria-Relevant Variables Found:**
    • **Health indicators**: {', '.join(malaria_vars[:3]) if malaria_vars else 'None detected'}
    • **Environmental factors**: {', '.join(env_vars[:4]) if env_vars else 'None detected'}  
    • **Risk modifiers**: {', '.join(risk_vars[:3]) if risk_vars else 'None detected'}

    **Analysis Readiness: ✅ Ready**
    Your data is suitable for analysis. You can now run comprehensive malaria risk assessment to identify priority wards for intervention.

    Would you like me to:
    • Run the full malaria risk analysis?
    • Explore specific variables in detail?
    • Create visualizations of key indicators?"""

                return response

            except Exception as e:
                return f"Error checking data quality: {str(e)}"

    def _get_tool_parameters(self, tool_name: str) -> Dict[str, Any]:
        """Get parameter schema for a tool."""
        base_params = {
            'type': 'object',
            'properties': {
                'session_id': {'type': 'string', 'description': 'Session identifier'}
            },
            'required': ['session_id']
        }

        if 'analysis' in tool_name:
            base_params['properties']['variables'] = {
                'type': 'array',
                'items': {'type': 'string'},
                'description': 'Optional custom variables for analysis. When specified, these will override automatic region-based selection.'
            }

        if 'map' in tool_name or 'plot' in tool_name:
            if tool_name == 'create_vulnerability_map':
                # For vulnerability map, method is optional - defaults to side-by-side comparison
                base_params['properties']['method'] = {
                    'type': 'string',
                    'enum': ['composite', 'pca'],
                    'description': 'Analysis method to visualize. If not specified, shows side-by-side comparison of both methods.'
                }
            else:
                base_params['properties']['method'] = {
                    'type': 'string',
                    'enum': ['composite', 'pca'],
                    'description': 'Analysis method to visualize'
                }

        if tool_name == 'execute_data_query':
            base_params['properties'].update({
                'query': {'type': 'string', 'description': 'Natural language query about the data'},
                'code': {'type': 'string', 'description': 'Optional Python code to execute'}
            })
            base_params['required'].append('query')

        if tool_name == 'execute_sql_query':
            base_params['properties'].update({
                'query': {
                    'type': 'string', 
                    'description': 'The SQL query string to execute on the dataframe. The table is always named "df". This parameter is REQUIRED and must contain a valid SQL query.',
                }
            })
            base_params['required'].append('query')

        if tool_name == 'explain_analysis_methodology':
            base_params['properties']['method'] = {
                'type': 'string',
                'enum': ['composite', 'pca', 'both'],
                'description': 'Which methodology to explain'
            }

        if tool_name == 'create_variable_distribution':
            base_params['properties']['variable_name'] = {
                'type': 'string',
                'description': 'The exact column name from the dataset to visualize on the map. This parameter is REQUIRED. Extract the variable name from the user request.',
            }
            base_params['required'].append('variable_name')

        if tool_name == 'create_settlement_map':
            base_params['properties'].update({
                'ward_name': {
                    'type': 'string',
                    'description': 'Optional specific ward name to highlight and focus on'
                },
                'zoom_level': {
                    'type': 'integer',
                    'description': 'Map zoom level (11=city view, 13=ward view, 15=detailed)',
                    'default': 11
                }
            })

        if tool_name == 'show_settlement_statistics':
            # No additional parameters needed - just session_id
            pass

        if tool_name == 'run_itn_planning':
            base_params['properties'].update({
                'total_nets': {
                    'type': 'integer',
                    'description': 'Total number of bed nets available for distribution (e.g., 50000, 100000)'
                },
                'avg_household_size': {
                    'type': 'number',
                    'description': 'Average household size in the area (default: 5.0)'
                },
                'urban_threshold': {
                    'type': 'number',
                    'description': 'Urban percentage threshold for prioritization (default: 30.0)'
                },
                'method': {
                    'type': 'string',
                    'enum': ['composite', 'pca'],
                    'description': 'Ranking method to use (default: composite)'
                }
            })

        if tool_name == 'list_dataset_columns':
            base_params['properties'].update({
                'page': {
                    'type': 'integer',
                    'description': 'Page number to display (1-indexed)',
                    'default': 1
                },
                'page_size': {
                    'type': 'integer',
                    'description': 'Number of columns per page (default 15)',
                    'default': 15
                }
            })

        return base_params



    # Legacy _build_system_prompt removed - now using PromptBuilder
    # See archive/legacy_prompt_builder.py for the original 400+ line method
    def _build_system_prompt_refactored(self, session_context: Dict, session_id: str = None) -> str:
        """Refactored system prompt using PromptBuilder; minimal fallback on error."""
        try:
            if hasattr(self, 'prompt_builder') and self.prompt_builder is not None:
                sc = dict(session_context) if isinstance(session_context, dict) else session_context
                if session_id and isinstance(sc, dict):
                    sc.setdefault('session_id', session_id)
                return self.prompt_builder.build(sc, session_id)
        except Exception as e:
            logger.warning(f"PromptBuilder failed, falling back to minimal prompt: {e}")
        return "You are ChatMRPT, an AI assistant for malaria risk analysis. Be accurate, concise, and action-oriented."
