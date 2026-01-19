"""
Enhanced Arena Manager for Data Interpretation

Extends the base ArenaManager to provide multi-model interpretation battles
with full data access. Enables diverse perspectives on malaria risk analysis
results through ensemble intelligence.
"""

import logging
from typing import Dict, Any, List

from .arena_manager import ArenaManager
from .arena_data_context import ArenaDataContextManager
from .arena_trigger_detector import ConversationalArenaTrigger

logger = logging.getLogger(__name__)


class EnhancedArenaManager(ArenaManager):
    """Data-aware Arena manager with formatting helpers used by tests."""

    def _analyze_consensus(self, interpretations: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """Derive a simple consensus object from model responses.

        Args:
            interpretations: mapping of model -> {response|interpretation: str}

        Returns:
            Dict like {'agreement_level': 'high'|'medium'|'low'}
        """
        try:
            texts: List[str] = []
            for v in (interpretations or {}).values():
                if not isinstance(v, dict):
                    continue
                txt = v.get('interpretation') or v.get('response') or ''
                if txt:
                    texts.append(txt.strip().lower())
            if len(texts) < 2:
                return {'agreement_level': 'low'}
            # Naive agreement: if many responses mention same key token
            keys = ['risk', 'ward', 'intervention', 'high', 'low']
            score = 0
            for k in keys:
                count = sum(1 for t in texts if k in t)
                if count >= 2:
                    score += 1
            if score >= 3:
                return {'agreement_level': 'high'}
            if score >= 1:
                return {'agreement_level': 'medium'}
            return {'agreement_level': 'low'}
        except Exception as e:
            logger.debug(f"Consensus analysis error: {e}")
            return {'agreement_level': 'low'}

    def format_for_conversation(self, arena_results: Dict[str, Any],
                                trigger_detector: ConversationalArenaTrigger) -> str:
        """Format Arena results for natural chat output with a clear header."""
        if not arena_results.get('success'):
            return "I apologize, but I couldn't generate multiple perspectives at this time."

        parts: List[str] = ["## Arena Analysis"]  # heading expected by tests

        trigger_type = arena_results.get('trigger_type', 'interpretation_request')
        parts.append(trigger_detector.get_trigger_explanation(trigger_type))

        confidence = arena_results.get('confidence_score', 0)
        if confidence > 0.7:
            parts.append("**Key Findings (High Agreement)**")
            consensus = arena_results.get('consensus', 'Analysis in progress...')
            if isinstance(consensus, dict):
                summary = ", ".join(f"{k}: {v}" for k, v in consensus.items()) or "Analysis in progress..."
            else:
                summary = str(consensus)
            parts.append(summary)

            interps = arena_results.get('interpretations') or []
            top = None
            if isinstance(interps, dict):
                top = next(iter(interps.values())) if interps else None
            elif isinstance(interps, list) and interps:
                top = interps[0]
            if top:
                role = top.get('role', 'Lead Analysis')
                text = top.get('interpretation') or top.get('response', '')
                parts.append(f"**{role}**:")
                parts.append((text or '')[:500] + '...')
        else:
            parts.append("**Multiple Analytical Perspectives**")
            interps = arena_results.get('interpretations') or []
            iterable = list(interps.values())[:3] if isinstance(interps, dict) else interps[:3]
            for i, item in enumerate(iterable):
                role = item.get('role', f'Perspective {i+1}')
                text = item.get('interpretation') or item.get('response', '')
                snippet = (text or '').split('\n\n')[0]
                parts.append(f"**{role}**:")
                parts.append(snippet[:300] + '...')

        return "\n".join(parts)

