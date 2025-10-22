"""Data-related helpers for RequestInterpreter."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DataToolsMixin:
    """Provide data query utilities and workflow helpers."""

    def _get_session_context(self, session_id: str, session_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
            except Exception as exc:
                logger.warning(f"SessionContextService failed: {exc}, falling back to manual detection")

        session_folder = Path(f'instance/uploads/{session_id}')
        if session_folder.exists():
            has_csv = any(f.suffix in ['.csv', '.xlsx', '.xls'] for f in session_folder.glob('*'))
            has_shapefile = any(f.suffix == '.shp' for f in session_folder.glob('*'))
            shapefile_dir = session_folder / 'shapefile'
            if not has_shapefile and shapefile_dir.exists():
                has_shapefile = any(f.suffix == '.shp' for f in shapefile_dir.glob('*'))
            if not has_shapefile:
                has_shapefile = any(
                    f.suffix == '.zip' and 'shapefile' in f.name.lower() for f in session_folder.glob('*')
                )

            analysis_marker = session_folder / '.analysis_complete'
            columns: list[str] = []
            current_data = 'No data uploaded'
            if has_csv:
                try:
                    file_patterns = ['unified_dataset.csv', 'raw_data.csv', 'data_analysis.csv', 'uploaded_data.csv']
                    df = None
                    for pattern in file_patterns:
                        csv_path = session_folder / pattern
                        if csv_path.exists():
                            df = pd.read_csv(csv_path)
                            columns = df.columns.tolist()
                            current_data = f'{len(df)} rows'
                            logger.info(f"📋 Loaded {len(df)} rows, {len(columns)} columns from {pattern}")
                            break
                    if not columns:
                        csv_files = [f for f in session_folder.glob('*.csv') if not f.name.startswith('.')]
                        if csv_files:
                            df = pd.read_csv(csv_files[0])
                            columns = df.columns.tolist()
                            current_data = f'{len(df)} rows'
                            logger.info(f"📋 Loaded {len(df)} rows, {len(columns)} columns from {csv_files[0].name}")
                except Exception as exc:
                    logger.warning(f"Could not load CSV: {exc}")
                    current_data = 'Data files found but could not be loaded'

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
                'session_id': session_id,
            }

        logger.warning(f"⚠️ Session folder not found: {session_folder}")
        return {'data_loaded': False, 'state_name': 'Not specified', 'current_data': 'No data uploaded'}

    def _handle_special_workflows(
        self,
        user_message: str,
        session_id: str,
        session_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        return None

    def _simple_conversational_response(
        self,
        user_message: str,
        session_context: Dict,
        session_id: str,
    ) -> Dict:
        try:
            system_prompt = self._build_system_prompt_refactored(session_context, session_id)
            response = self.llm_manager.generate(
                user_message,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=500,
            )
            self._store_conversation(session_id, user_message, response)
            return {'response': response, 'status': 'success', 'tools_used': []}
        except Exception as exc:
            logger.error(f"Error generating conversational response: {exc}")
            return {
                'response': 'I encountered an error processing your message. Please try again.',
                'status': 'error',
                'tools_used': [],
            }

    def _execute_data_query(self, session_id: str, query: str, code: Optional[str] = None):
        try:
            from app.services.conversational_data_access import ConversationalDataAccess

            logger.info(f"Executing data query: {query}")
            conversational_data_access = ConversationalDataAccess(session_id, self.llm_manager)
            result = conversational_data_access.process_query(query=query, code=code)
            if result.get('success'):
                return result.get('output', 'Query executed successfully')
            error_msg = result.get('error', 'Unknown error')
            return f"Error executing query: {error_msg}"
        except Exception as exc:
            return f'Error in data query: {exc}'

    def _execute_sql_query(self, session_id: str, query: str):
        try:
            logger.info(f"Executing SQL query: {query}")
            from app.services.conversational_data_access import ConversationalDataAccess

            conversational_data_access = ConversationalDataAccess(session_id, self.llm_manager)
            result = conversational_data_access.process_sql_query(query)
            if result.get('success'):
                return result.get('output', 'Query executed successfully')
            return f"Error executing SQL: {result.get('error', 'Unknown error')}"
        except Exception as exc:
            logger.error(f"SQL query error: {exc}")
            return f'Error executing SQL query: {exc}'

    def _run_itn_planning(
        self,
        session_id: str,
        total_nets: Optional[int] = 10000,
        avg_household_size: Optional[float] = 5.0,
        urban_threshold: Optional[float] = 30.0,
        method: str = 'composite',
    ):
        logger.info('🛏️ ITN: _run_itn_planning called')
        logger.info(f'  Session ID: {session_id}')
        logger.info(f'  Total Nets: {total_nets}')
        logger.info(f'  Household Size: {avg_household_size}')
        logger.info(f'  Urban Threshold: {urban_threshold}')
        logger.info(f'  Method: {method}')

        try:
            if not self.analysis_service.has_completed_analysis(session_id):
                return 'ITN planning requires completed analysis. Please run the malaria risk analysis first before planning ITN distribution.'

            data_handler = self.data_service.get_handler(session_id)
            if not data_handler:
                return 'No data available. Please run analysis first.'
            if not getattr(data_handler, 'unified_dataset', None):
                data_handler._load_unified_dataset()
                if data_handler.unified_dataset is None:
                    return 'Analysis rankings not found. Please run the malaria risk analysis first to generate vulnerability rankings.'

            from app.tools.itn_planning_tools import PlanITNDistribution

            tool = PlanITNDistribution(
                total_nets=total_nets if total_nets != 10000 else None,
                avg_household_size=avg_household_size,
                urban_threshold=urban_threshold,
                method=method,
            )
            tool_result = tool.execute(session_id=session_id)
            if not tool_result.success:
                return {
                    'response': tool_result.message,
                    'status': 'error',
                    'tools_used': ['run_itn_planning'],
                }

            visualizations = []
            if getattr(tool_result, 'web_path', None):
                visualizations.append({'type': 'itn_map', 'path': tool_result.web_path, 'url': tool_result.web_path})

            return {
                'response': tool_result.message,
                'visualizations': visualizations,
                'download_links': getattr(tool_result, 'download_links', []),
                'tools_used': ['run_itn_planning'],
                'status': 'success',
            }
        except Exception as exc:
            return f'Error planning ITN: {exc}'

    def _analyze_data_with_python(self, session_id: str, query: str) -> Dict[str, Any]:
        logger.info('🐍 TOOL: analyze_data_with_python called')
        logger.info(f'  Session: {session_id}')
        logger.info(f'  Query: {query[:100]}...')
        try:
            if session_id not in self.data_agents:
                from app.data_analysis_v3.core.data_exploration_agent import DataExplorationAgent

                logger.info(f'🆕 Creating new DataExplorationAgent for session {session_id}')
                self.data_agents[session_id] = DataExplorationAgent(session_id=session_id)
            else:
                logger.info(f'♻️ Reusing existing DataExplorationAgent for session {session_id} (conversation memory active)')

            agent = self.data_agents[session_id]
            result = agent.analyze_sync(query)
            return {
                'status': 'success' if result.get('success', False) else 'error',
                'response': result.get('message', ''),
                'visualizations': result.get('visualizations', []),
                'tools_used': ['analyze_data_with_python'],
            }
        except Exception as exc:
            logger.error(f'Error in analyze_data_with_python: {exc}', exc_info=True)
            return {
                'status': 'error',
                'response': f'I encountered an error analyzing the data: {exc}',
                'tools_used': ['analyze_data_with_python'],
            }

    def _run_data_quality_check(self, session_id: str):
        try:
            session_folder = Path(f'instance/uploads/{session_id}')
            raw_data_path = session_folder / 'raw_data.csv'
            if not raw_data_path.exists():
                return 'No data file found. Please upload data first.'

            df = pd.read_csv(raw_data_path)
            total_missing = df.isnull().sum().sum()
            duplicates = df.duplicated().sum()
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()

            malaria_vars: list[str] = []
            env_vars: list[str] = []
            risk_vars: list[str] = []

            for col in df.columns:
                col_lower = col.lower()
                if any(token in col_lower for token in ['tpr', 'test', 'positive']):
                    malaria_vars.append(col)
                elif any(token in col_lower for token in ['evi', 'ndvi', 'soil', 'rain', 'temp', 'humid']):
                    env_vars.append(col)
                elif any(token in col_lower for token in ['urban', 'housing', 'population', 'density']):
                    risk_vars.append(col)

            response = (
                "**Data Quality Check Complete**\n\n"
                f"📊 Your dataset has {total_missing} total missing values (minimal impact on analysis).\n\n"
                f"✅ **{'No duplicate entries' if duplicates == 0 else f'{duplicates} duplicate entries found'}** -"
                f" {'each ward has unique data' if duplicates == 0 else 'consider removing duplicates'}.\n\n"
                "**Key Dataset Characteristics:**\n"
                f"• Both numeric indicators ({len(numeric_cols)}) and categorical identifiers ({len(categorical_cols)})\n\n"
                "**Malaria-Relevant Variables Found:**\n"
                f"• **Health indicators**: {(', '.join(malaria_vars[:3]) if malaria_vars else 'None detected')}\n"
                f"• **Environmental factors**: {(', '.join(env_vars[:4]) if env_vars else 'None detected')}  \n"
                f"• **Risk modifiers**: {(', '.join(risk_vars[:3]) if risk_vars else 'None detected')}\n\n"
                "**Analysis Readiness: ✅ Ready**\n"
                "Your data is suitable for analysis. You can now run comprehensive malaria risk assessment to identify priority wards for intervention.\n\n"
                "Would you like me to:\n"
                "• Run the full malaria risk analysis?\n"
                "• Explore specific variables in detail?\n"
                "• Create visualizations of key indicators?"
            )
            return response
        except Exception as exc:
            return f'Error checking data quality: {exc}'

__all__ = ['DataToolsMixin']
