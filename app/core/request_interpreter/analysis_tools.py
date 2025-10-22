"""Analysis tool helpers for RequestInterpreter."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AnalysisToolsMixin:
    """Provide malaria risk analysis helper methods."""

    def _run_malaria_risk_analysis(self, session_id: str, variables: Optional[List[str]] = None) -> Any:
        try:
            result = self.analysis_service.run_composite_analysis(session_id, variables=variables)
            if result.get('status') == 'success':
                try:
                    from flask import session

                    session['analysis_complete'] = True
                    session.modified = True
                except Exception:
                    self.conversation_history.setdefault(session_id, []).append({'analysis_complete': True})

                pca_result = self.analysis_service.run_pca_analysis(session_id, variables=variables)
                try:
                    from app.tools.complete_analysis_tools import RunMalariaRiskAnalysis

                    analysis_tool = RunMalariaRiskAnalysis()
                    summary = analysis_tool._generate_comprehensive_summary(result, pca_result, {}, 0.0, session_id)
                    return summary
                except Exception as summary_error:  # pragma: no cover - logging only
                    logger.error(f"Error calling _generate_summary_from_analysis_results: {summary_error}")
                    logger.error(f"Composite result structure: {(result.keys() if result else 'None')}")
                    logger.error(f"PCA result structure: {(pca_result.keys() if pca_result else 'None')}")
                    import traceback

                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    return '✅ Composite analysis completed successfully. Results are available - please ask for detailed rankings.'
            else:
                from app.services.response_formatter import response_formatter

                return response_formatter.format_error_message(
                    result.get('message', 'Composite analysis failed'),
                    'composite_analysis',
                    ['Check data quality', 'Verify variable selection', 'Review analysis parameters'],
                )
        except Exception as exc:
            from app.services.response_formatter import response_formatter

            return response_formatter.format_error_message(
                str(exc),
                'composite_analysis_execution',
                ['Check data upload', 'Verify system configuration', 'Review error logs'],
            )

    def _run_composite_analysis(self, session_id: str, variables: Optional[List[str]] = None) -> Any:
        try:
            result = self.analysis_service.run_composite_analysis(session_id, variables=variables)
            if result.get('status') == 'success':
                return result.get('message', 'Composite analysis completed successfully.')
            return result.get('message', 'Composite analysis failed.')
        except Exception as exc:
            return f'Error running composite analysis: {exc}'

    def _run_pca_analysis(self, session_id: str, variables: Optional[List[str]] = None) -> Any:
        try:
            result = self.analysis_service.run_pca_analysis(session_id, variables=variables)
            if result.get('status') == 'success':
                try:
                    from flask import session

                    session['analysis_complete'] = True
                    session.modified = True
                except Exception:
                    self.conversation_history.setdefault(session_id, []).append({'analysis_complete': True})

            from app.services.response_formatter import response_formatter

            if isinstance(result, dict):
                return response_formatter.format_analysis_result(result, 'pca')
            return result.get('message', 'PCA analysis completed successfully')
        except Exception as exc:
            return f'Error running PCA analysis: {exc}'

__all__ = ['AnalysisToolsMixin']
