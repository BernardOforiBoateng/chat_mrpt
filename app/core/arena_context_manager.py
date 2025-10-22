"""
Arena Context Manager
Aggregates session context and recent analysis results for Arena models
"""

import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


class ArenaContextManager:
    """Manages context aggregation for Arena models to understand analysis results."""
    
    def __init__(self):
        self.max_context_items = 3  # Limit recent results to avoid token overflow
        self.max_conversation_history = 5  # Limit conversation history to last 5 exchanges
        from app.core.redis_state_manager import get_redis_state_manager
        self.redis_manager = get_redis_state_manager()
        
    def get_session_context(self, session_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate session context for Arena models.
        
        Args:
            session_id: Current session ID
            session_data: Flask session data
            
        Returns:
            Context dictionary with relevant analysis information
        """
        context = {
            'session_id': session_id,
            'data_loaded': session_data.get('data_loaded', False),
            'analysis_type': None,
            'recent_results': [],
            'key_metrics': {},
            'data_summary': {},
            'workflow_state': {
                'tpr_active': session_data.get('tpr_workflow_active', False),
                'analysis_complete': session_data.get('analysis_complete', False),
                'itn_planning_active': session_data.get('itn_planning_active', False)
            }
        }
        
        try:
            # Determine analysis type
            if session_data.get('tpr_workflow_active'):
                context['analysis_type'] = 'TPR Analysis'
            elif session_data.get('csv_loaded') and session_data.get('shapefile_loaded'):
                context['analysis_type'] = 'Risk Assessment'
            elif session_data.get('csv_loaded'):
                context['analysis_type'] = 'Data Analysis'
                
            # Get recent analysis results if available
            session_folder = Path(f'instance/uploads/{session_id}')
            
            if session_folder.exists():
                # Check for TPR results
                tpr_file = session_folder / 'tpr_results.csv'
                if tpr_file.exists():
                    context['recent_results'].append(self._summarize_tpr_results(tpr_file))
                    
                # Check for risk analysis results
                analysis_file = session_folder / 'analysis_rankings.csv'
                if analysis_file.exists():
                    context['recent_results'].append(self._summarize_risk_results(analysis_file))
                    
                # Check for raw data summary
                raw_data_file = session_folder / 'raw_data.csv'
                if raw_data_file.exists():
                    context['data_summary'] = self._summarize_data(raw_data_file)
                    
            # Extract key metrics from recent results
            context['key_metrics'] = self._extract_key_metrics(context['recent_results'])

            # Add conversation history from Redis
            context['conversation_history'] = self.get_conversation_history(session_id)

        except Exception as e:
            logger.error(f"Error aggregating session context: {e}")

        return context

    def store_conversation_exchange(self, session_id: str, user_message: str, assistant_response: str):
        """Store a conversation exchange in Redis for context persistence."""
        try:
            # Get existing conversation state
            convo_state = self.redis_manager.get_conversation_state(session_id) or {}
            history = convo_state.get('history', [])

            # Add new exchange
            exchange = {
                'user': user_message,
                'assistant': assistant_response
            }
            history.append(exchange)

            # Keep only last N exchanges
            if len(history) > self.max_conversation_history:
                history = history[-self.max_conversation_history:]

            # Update conversation state
            convo_state['history'] = history
            convo_state['last_message'] = user_message
            convo_state['last_response'] = assistant_response

            # Store in Redis
            self.redis_manager.set_conversation_state(session_id, convo_state)
            logger.info(f"Stored conversation exchange for session {session_id}")

        except Exception as e:
            logger.error(f"Error storing conversation exchange: {e}")

    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieve conversation history from Redis."""
        try:
            convo_state = self.redis_manager.get_conversation_state(session_id)
            if convo_state and 'history' in convo_state:
                return convo_state['history'][-self.max_conversation_history:]
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
        return []
    
    def _summarize_tpr_results(self, file_path: Path) -> Dict[str, Any]:
        """Summarize TPR analysis results."""
        try:
            df = pd.read_csv(file_path)
            
            # Get top high-risk wards
            high_risk = df[df['TPR'] > 20].nlargest(5, 'TPR') if 'TPR' in df.columns else pd.DataFrame()
            
            summary = {
                'type': 'TPR Analysis',
                'total_wards': len(df),
                'mean_tpr': df['TPR'].mean() if 'TPR' in df.columns else 0,
                'max_tpr': df['TPR'].max() if 'TPR' in df.columns else 0,
                'high_risk_count': len(high_risk),
                'top_wards': []
            }
            
            for _, ward in high_risk.iterrows():
                summary['top_wards'].append({
                    'name': ward.get('WardName', 'Unknown'),
                    'tpr': float(ward.get('TPR', 0)),
                    'lga': ward.get('LGA', 'Unknown')
                })
                
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing TPR results: {e}")
            return {'type': 'TPR Analysis', 'error': str(e)}
    
    def _summarize_risk_results(self, file_path: Path) -> Dict[str, Any]:
        """Summarize risk analysis results."""
        try:
            df = pd.read_csv(file_path)
            
            # Determine which scoring method was used
            score_col = 'composite_score' if 'composite_score' in df.columns else 'pca_score' if 'pca_score' in df.columns else None
            
            if not score_col:
                return {'type': 'Risk Analysis', 'error': 'No score column found'}
            
            # Get top vulnerable wards
            top_wards = df.nlargest(10, score_col)
            
            summary = {
                'type': 'Risk Analysis',
                'method': 'Composite' if 'composite' in score_col else 'PCA',
                'total_wards': len(df),
                'mean_score': df[score_col].mean(),
                'max_score': df[score_col].max(),
                'top_wards': []
            }
            
            for idx, (_, ward) in enumerate(top_wards.iterrows(), 1):
                summary['top_wards'].append({
                    'rank': idx,
                    'name': ward.get('WardName', 'Unknown'),
                    'score': float(ward.get(score_col, 0)),
                    'category': ward.get('vulnerability_category', 'Unknown')
                })
                
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing risk results: {e}")
            return {'type': 'Risk Analysis', 'error': str(e)}
    
    def _summarize_data(self, file_path: Path) -> Dict[str, Any]:
        """Provide basic data summary with enhanced column information."""
        try:
            df = pd.read_csv(file_path)

            # Get column information with types
            column_info = []
            for col in df.columns[:20]:  # First 20 columns
                dtype_str = str(df[col].dtype)
                if 'float' in dtype_str or 'int' in dtype_str:
                    col_type = 'numeric'
                elif 'object' in dtype_str:
                    col_type = 'text'
                else:
                    col_type = dtype_str

                column_info.append({
                    'name': col,
                    'type': col_type,
                    'non_null': df[col].notna().sum()
                })

            return {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns)[:20],  # First 20 columns
                'column_info': column_info,
                'has_ward_names': 'WardName' in df.columns or 'ward' in str(df.columns).lower(),
                'has_lga': 'LGA' in df.columns or 'lga' in str(df.columns).lower(),
                'numeric_columns': df.select_dtypes(include=['float64', 'int64']).columns.tolist()[:10],
                'text_columns': df.select_dtypes(include=['object']).columns.tolist()[:10]
            }

        except Exception as e:
            logger.error(f"Error summarizing data: {e}")
            return {'error': str(e)}
    
    def _extract_key_metrics(self, recent_results: List[Dict]) -> Dict[str, Any]:
        """Extract key metrics from recent results for quick reference."""
        metrics = {}
        
        for result in recent_results:
            if result.get('type') == 'TPR Analysis':
                metrics['tpr_mean'] = result.get('mean_tpr', 0)
                metrics['tpr_max'] = result.get('max_tpr', 0)
                metrics['tpr_high_risk_count'] = result.get('high_risk_count', 0)
                
            elif result.get('type') == 'Risk Analysis':
                metrics['risk_method'] = result.get('method', 'Unknown')
                metrics['risk_mean_score'] = result.get('mean_score', 0)
                metrics['risk_max_score'] = result.get('max_score', 0)
                
        return metrics
    
    def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """
        Format context into a string suitable for inclusion in Arena model prompts.
        
        Args:
            context: Context dictionary from get_session_context
            
        Returns:
            Formatted string for prompt injection
        """
        if not context.get('data_loaded'):
            return ""
            
        prompt_parts = ["\n## Current Session Context\n"]
        
        # Add analysis type
        if context.get('analysis_type'):
            prompt_parts.append(f"**Analysis Type:** {context['analysis_type']}\n")
        
        # Add enhanced data summary with column information
        if context.get('data_summary') and not context['data_summary'].get('error'):
            summary = context['data_summary']
            prompt_parts.append(f"**Data Loaded:** {summary.get('rows', 0)} rows × {summary.get('columns', 0)} columns\n")

            # Add column names
            if summary.get('column_names'):
                prompt_parts.append("\n**Available Variables/Columns:**")
                for i, col_name in enumerate(summary['column_names'][:15], 1):
                    prompt_parts.append(f"  {i}. {col_name}")
                if summary.get('columns', 0) > 15:
                    prompt_parts.append(f"  ... and {summary['columns'] - 15} more columns\n")

            # Add column types summary
            if summary.get('numeric_columns'):
                prompt_parts.append(f"\n**Numeric Columns:** {', '.join(summary['numeric_columns'][:8])}")
            if summary.get('text_columns'):
                prompt_parts.append(f"**Text Columns:** {', '.join(summary['text_columns'][:5])}")
        
        # Add recent results
        if context.get('recent_results'):
            prompt_parts.append("\n### Recent Analysis Results\n")
            
            for result in context['recent_results'][:self.max_context_items]:
                if result.get('type') == 'TPR Analysis' and not result.get('error'):
                    prompt_parts.append(f"\n**TPR Analysis:**")
                    prompt_parts.append(f"- Wards Analyzed: {result.get('total_wards', 0)}")
                    prompt_parts.append(f"- Mean TPR: {result.get('mean_tpr', 0):.1f}%")
                    prompt_parts.append(f"- Max TPR: {result.get('max_tpr', 0):.1f}%")
                    prompt_parts.append(f"- High Risk Wards (TPR >20%): {result.get('high_risk_count', 0)}")
                    
                    if result.get('top_wards'):
                        prompt_parts.append("\nTop High-Risk Wards:")
                        for ward in result['top_wards'][:3]:
                            prompt_parts.append(f"  • {ward['name']} ({ward['lga']}): {ward['tpr']:.1f}%")
                            
                elif result.get('type') == 'Risk Analysis' and not result.get('error'):
                    prompt_parts.append(f"\n**{result.get('method', '')} Risk Analysis:**")
                    prompt_parts.append(f"- Wards Analyzed: {result.get('total_wards', 0)}")
                    prompt_parts.append(f"- Mean Score: {result.get('mean_score', 0):.3f}")
                    prompt_parts.append(f"- Max Score: {result.get('max_score', 0):.3f}")
                    
                    if result.get('top_wards'):
                        prompt_parts.append("\nTop Vulnerable Wards:")
                        for ward in result['top_wards'][:5]:
                            prompt_parts.append(f"  {ward['rank']}. {ward['name']}: {ward['score']:.3f} ({ward['category']})")
        
        # Add key metrics summary
        if context.get('key_metrics'):
            prompt_parts.append("\n### Key Metrics\n")
            metrics = context['key_metrics']
            
            if 'tpr_mean' in metrics:
                prompt_parts.append(f"- Average TPR: {metrics['tpr_mean']:.1f}%")
            if 'risk_method' in metrics:
                prompt_parts.append(f"- Risk Assessment Method: {metrics['risk_method']}")
                
        # Add workflow state
        if context.get('workflow_state'):
            workflow = context['workflow_state']
            if workflow.get('tpr_active'):
                prompt_parts.append("\n### Active Workflow\n")
                prompt_parts.append("**TPR Workflow Active**: The user is currently working on TPR (Test Positivity Rate) analysis.")
                prompt_parts.append("If the user asks unrelated questions, gently remind them about the active workflow.\n")
            elif workflow.get('itn_planning_active'):
                prompt_parts.append("\n### Active Workflow\n")
                prompt_parts.append("**ITN Planning Active**: The user is planning ITN (Insecticide-Treated Net) distribution.")
                prompt_parts.append("Help them continue with the planning process if they get sidetracked.\n")

        # Add conversation history
        if context.get('conversation_history'):
            prompt_parts.append("\n### Recent Conversation History\n")
            for i, exchange in enumerate(context['conversation_history'][-3:], 1):  # Last 3 exchanges
                if 'user' in exchange:
                    prompt_parts.append(f"User: {exchange['user'][:200]}")
                if 'assistant' in exchange:
                    prompt_parts.append(f"Assistant: {exchange['assistant'][:200]}")
                if i < len(context['conversation_history'][-3:]):
                    prompt_parts.append("")  # Empty line between exchanges

        prompt_parts.append("\n---\n")

        return '\n'.join(prompt_parts)


# Singleton instance
_arena_context_manager = None

def get_arena_context_manager() -> ArenaContextManager:
    """Get or create the singleton ArenaContextManager instance."""
    global _arena_context_manager
    if _arena_context_manager is None:
        _arena_context_manager = ArenaContextManager()
    return _arena_context_manager