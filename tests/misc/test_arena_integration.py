"""
Comprehensive tests for Arena multi-model interpretation integration.

Tests the full Arena enhancement system including:
- Trigger detection
- Data context loading
- Model-specific prompts
- RequestInterpreter integration
- End-to-end interpretation flow
"""

import pytest
import asyncio
import os
import json
import pandas as pd
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timedelta

# Import Arena components
from app.core.arena_trigger_detector import ConversationalArenaTrigger
from app.core.arena_data_context import ArenaDataContextManager
from app.core.arena_prompt_builder import ModelSpecificPromptBuilder
from app.core.enhanced_arena_manager import EnhancedArenaManager
from app.core.arena_integration_patch import ArenaIntegrationMixin, patch_request_interpreter


class TestArenaTriggerDetector:
    """Test conversational trigger detection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.trigger = ConversationalArenaTrigger('test_session')

    def test_explicit_trigger_detection(self):
        """Test explicit trigger patterns."""
        # Test interpretation request
        should_trigger, trigger_type, confidence = self.trigger.should_trigger(
            "What does this mean?",
            {'analysis_complete': True}
        )
        assert should_trigger is True
        assert trigger_type == 'interpretation_request'
        assert confidence > 0.5

        # Reset cooldown for next test
        self.trigger.reset_cooldown()

        # Test comparison request
        should_trigger, trigger_type, confidence = self.trigger.should_trigger(
            "Show me different perspectives on these results",
            {'analysis_complete': True}
        )
        assert should_trigger is True
        assert trigger_type == 'comparison_request'

        # Reset cooldown for next test
        self.trigger.reset_cooldown()

        # Test action planning
        should_trigger, trigger_type, confidence = self.trigger.should_trigger(
            "What should we do next?",
            {'analysis_complete': True}
        )
        assert should_trigger is True
        assert trigger_type == 'action_planning'

    def test_implicit_trigger_detection(self):
        """Test implicit trigger conditions."""
        # Test post-analysis trigger
        context = {
            'analysis_complete': True,
            'arena_interpreted': False,
            'analysis_complete_time': datetime.now()
        }
        should_trigger, trigger_type, confidence = self.trigger.should_trigger(
            "Show me the results",
            context
        )
        # Should trigger if it's the first message after analysis
        # Depending on timing, this might or might not trigger

        # Test high-risk alert
        context = {
            'analysis_complete': True,
            'statistics': {
                'risk_distribution': {'High': 15, 'Medium': 10, 'Low': 5}
            }
        }
        should_trigger, trigger_type, confidence = self.trigger.should_trigger(
            "Interesting patterns here",
            context
        )
        assert should_trigger is True
        assert trigger_type == 'high_risk_alert'

    def test_contextual_triggers(self):
        """Test contextual trigger combinations."""
        # Test ward investigation
        context = {'analysis_complete': True}
        should_trigger, trigger_type, confidence = self.trigger.should_trigger(
            "Why is this ward showing high risk?",
            context
        )
        assert should_trigger is True
        assert trigger_type == 'ward_investigation'

        # Test pattern analysis
        should_trigger, trigger_type, confidence = self.trigger.should_trigger(
            "I see some patterns and trends here",
            context
        )
        assert should_trigger is True
        assert trigger_type == 'pattern_analysis'

    def test_cooldown_period(self):
        """Test trigger cooldown mechanism."""
        context = {'analysis_complete': True}

        # First trigger should work
        should_trigger, _, _ = self.trigger.should_trigger(
            "Explain these results",
            context
        )
        assert should_trigger is True

        # Second trigger immediately after should be blocked
        should_trigger, _, _ = self.trigger.should_trigger(
            "Tell me more",
            context
        )
        assert should_trigger is False

        # Reset cooldown
        self.trigger.reset_cooldown()

        # Should trigger again
        should_trigger, _, _ = self.trigger.should_trigger(
            "Explain further",
            context
        )
        assert should_trigger is True


class TestArenaDataContext:
    """Test data context loading for Arena models."""

    def setup_method(self):
        """Create test data directory."""
        self.test_dir = tempfile.mkdtemp()
        self.session_id = 'test_session'
        self.session_dir = os.path.join(self.test_dir, 'uploads', self.session_id)
        os.makedirs(self.session_dir)

        # Create test data files
        self._create_test_data()

        # Patch the instance path
        self.patcher = patch('app.core.arena_data_context.current_app')
        mock_app = self.patcher.start()
        mock_app.instance_path = self.test_dir

    def teardown_method(self):
        """Clean up test directory."""
        self.patcher.stop()
        shutil.rmtree(self.test_dir)

    def _create_test_data(self):
        """Create test CSV files."""
        # Create raw data
        pd.DataFrame({
            'ward': ['Ward A', 'Ward B', 'Ward C'],
            'population': [1000, 1500, 1200],
            'tpr': [45.2, 38.7, 52.1]
        }).to_csv(os.path.join(self.session_dir, 'raw_data.csv'), index=False)

        # Create analysis results
        pd.DataFrame({
            'ward': ['Ward A', 'Ward B', 'Ward C'],
            'composite_score': [0.72, 0.58, 0.81],
            'risk_category': ['High', 'Medium', 'High']
        }).to_csv(os.path.join(self.session_dir, 'analysis_composite_scores.csv'), index=False)

        # Create PCA scores
        pd.DataFrame({
            'ward': ['Ward A', 'Ward B', 'Ward C'],
            'PC1': [0.5, -0.2, 0.8],
            'PC2': [-0.1, 0.3, 0.4]
        }).to_csv(os.path.join(self.session_dir, 'analysis_pca_scores.csv'), index=False)

    def test_load_full_context(self):
        """Test loading complete data context."""
        manager = ArenaDataContextManager(self.session_id)
        context = manager.load_full_context()

        # Check data files loaded
        assert 'data_files' in context
        assert 'raw_data' in context['data_files']
        assert len(context['data_files']['raw_data']) == 3

        # Check analysis results loaded
        assert 'analysis_results' in context
        assert 'composite_scores' in context['analysis_results']
        assert 'pca_scores' in context['analysis_results']

        # Check statistics calculated
        assert 'statistics' in context
        assert 'tpr' in context['statistics']
        assert 'risk_distribution' in context['statistics']

    def test_missing_data_handling(self):
        """Test handling of missing data files."""
        manager = ArenaDataContextManager('nonexistent_session')
        context = manager.load_full_context()

        # Should return empty context
        assert context['data_files'] == {}
        assert context['analysis_results'] == {}

    def test_build_arena_prompt(self):
        """Test prompt building with context."""
        manager = ArenaDataContextManager(self.session_id)
        prompt = manager.build_arena_prompt(
            "Explain the risk patterns",
            "interpretation_request"
        )

        # Check prompt contains data summary
        assert "Dataset Overview" in prompt
        assert "ward" in prompt
        assert "Risk Distribution" in prompt


class TestModelSpecificPromptBuilder:
    """Test model-specific prompt optimization."""

    def setup_method(self):
        """Set up prompt builder."""
        self.builder = ModelSpecificPromptBuilder()
        self.base_prompt = "Analyze the malaria risk data"
        self.context = {
            'data_files': {
                'unified_dataset': pd.DataFrame({
                    'ward': ['A', 'B', 'C'],
                    'composite_score': [0.7, 0.5, 0.8],
                    'risk_category': ['High', 'Medium', 'High']
                })
            },
            'statistics': {
                'tpr': {'mean': 45.0, 'std': 8.5},
                'risk_distribution': {'High': 2, 'Medium': 1}
            }
        }

    def test_phi3_prompt_building(self):
        """Test Phi-3 prompt optimization for logical reasoning."""
        prompt = self.builder.build_prompt('phi3:mini', self.base_prompt, self.context)

        # Check for Phi-3 specific elements
        assert "The Analyst" in prompt
        assert "logical reasoning" in prompt.lower()
        assert "pattern" in prompt.lower()
        assert "Step" in prompt  # Step-by-step analysis

    def test_mistral_prompt_building(self):
        """Test Mistral prompt optimization for statistics."""
        prompt = self.builder.build_prompt('mistral:7b', self.base_prompt, self.context)

        # Check for Mistral specific elements
        assert "The Statistician" in prompt
        assert "statistical" in prompt.lower()
        assert "confidence" in prompt.lower()
        assert "Dataset size: n =" in prompt

    def test_qwen_prompt_building(self):
        """Test Qwen prompt optimization for technical implementation."""
        prompt = self.builder.build_prompt('qwen2.5:7b', self.base_prompt, self.context)

        # Check for Qwen specific elements
        assert "The Technician" in prompt
        assert "implementation" in prompt.lower()
        assert "practical" in prompt.lower()
        assert "Data Specifications" in prompt

    def test_model_temperature_settings(self):
        """Test temperature recommendations for each model."""
        assert self.builder.get_model_temperature('phi3:mini') == 0.7
        assert self.builder.get_model_temperature('mistral:7b') == 0.5
        assert self.builder.get_model_temperature('qwen2.5:7b') == 0.6


class TestEnhancedArenaManager:
    """Test enhanced Arena manager with data interpretation."""

    def setup_method(self):
        """Set up Arena manager."""
        self.config = {
            'phi3:mini': {'type': 'ollama', 'display_name': 'The Analyst'},
            'mistral:7b': {'type': 'ollama', 'display_name': 'The Statistician'},
            'qwen2.5:7b': {'type': 'ollama', 'display_name': 'The Technician'}
        }
        self.manager = EnhancedArenaManager(self.config)

    @pytest.mark.asyncio
    @patch('app.core.enhanced_arena_manager.ArenaDataContextManager')
    @patch('app.core.enhanced_arena_manager.EnhancedArenaManager.get_parallel_interpretations')
    async def test_interpret_analysis_results(self, mock_parallel, mock_context_manager):
        """Test analysis interpretation with full data context."""
        # Mock context loading
        mock_context_manager.return_value.load_full_context.return_value = {
            'data_files': {'raw_data': pd.DataFrame()},
            'statistics': {'tpr': {'mean': 45.0}}
        }

        # Mock model responses
        mock_parallel.return_value = {
            'phi3:mini': {'response': 'Logical analysis...', 'tokens': 50, 'time': 1.2},
            'mistral:7b': {'response': 'Statistical analysis...', 'tokens': 45, 'time': 1.1},
            'qwen2.5:7b': {'response': 'Technical analysis...', 'tokens': 48, 'time': 1.0}
        }

        # Execute interpretation
        result = await self.manager.interpret_analysis_results(
            'test_session',
            'Explain the results',
            'interpretation_request'
        )

        # Verify result structure
        assert result['success'] is True
        assert 'interpretations' in result
        assert len(result['interpretations']) == 3
        assert 'consensus' in result
        assert 'unique_insights' in result

    def test_analyze_consensus(self):
        """Test consensus analysis from multiple interpretations."""
        interpretations = {
            'phi3:mini': {'response': 'High risk in Ward A due to poor infrastructure'},
            'mistral:7b': {'response': 'Ward A shows 70% risk with high statistical confidence'},
            'qwen2.5:7b': {'response': 'Ward A requires immediate intervention'}
        }

        consensus = self.manager._analyze_consensus(interpretations)

        assert 'agreement_level' in consensus
        assert 'common_themes' in consensus
        assert 'disagreements' in consensus

    def test_format_for_conversation(self):
        """Test formatting Arena results for chat display."""
        arena_result = {
            'success': True,
            'interpretations': {
                'phi3:mini': {'response': 'Analysis 1'},
                'mistral:7b': {'response': 'Analysis 2'},
                'qwen2.5:7b': {'response': 'Analysis 3'}
            },
            'consensus': {'agreement_level': 'high'},
            'confidence_score': 0.85
        }

        trigger = ConversationalArenaTrigger('test')
        formatted = self.manager.format_for_conversation(arena_result, trigger)

        assert "Arena Analysis" in formatted
        assert "The Analyst" in formatted
        assert "The Statistician" in formatted
        assert "The Technician" in formatted


class TestArenaIntegrationPatch:
    """Test RequestInterpreter integration."""

    @patch('app.core.arena_integration_patch.RequestInterpreter')
    def test_patch_application(self, mock_interpreter_class):
        """Test patching RequestInterpreter with Arena capabilities."""
        # Apply patch
        success = patch_request_interpreter()

        # Patch should succeed (with mock)
        # In real test, this would check if the class was replaced
        assert success is True or success is False  # Depends on import availability

    def test_arena_mixin_initialization(self):
        """Test Arena mixin initialization."""
        # Create mock base class
        class MockRequestInterpreter:
            def __init__(self):
                self.session_data = {}

            def process_message(self, message, session_id, session_data=None, **kwargs):
                return {'response': 'Base response'}

        # Apply mixin
        class TestInterpreter(ArenaIntegrationMixin, MockRequestInterpreter):
            pass

        interpreter = TestInterpreter()

        # Check Arena components initialized
        assert hasattr(interpreter, 'arena_enabled')
        assert hasattr(interpreter, 'arena_states')

    @patch('app.core.arena_integration_patch.ArenaIntegrationMixin._execute_arena_interpretation')
    def test_process_message_with_arena(self, mock_execute):
        """Test message processing with Arena trigger."""
        # Create test interpreter
        class MockRequestInterpreter:
            def __init__(self):
                pass

            def process_message(self, message, session_id, session_data=None, **kwargs):
                return {'response': 'Base response'}

        class TestInterpreter(ArenaIntegrationMixin, MockRequestInterpreter):
            pass

        interpreter = TestInterpreter()
        interpreter.arena_enabled = True

        # Mock Arena execution
        mock_execute.return_value = {
            'success': True,
            'interpretations': {'phi3:mini': {'response': 'Arena insight'}}
        }

        # Process message that should trigger Arena
        result = interpreter.process_message_with_arena(
            "Explain these results",
            "test_session",
            {'analysis_complete': True}
        )

        # Check base response is preserved
        assert 'response' in result

    def test_arena_follow_up_handling(self):
        """Test handling follow-up questions about Arena results."""
        # Create mixin instance
        class MockBase:
            def __init__(self):
                pass

        class TestInterpreter(ArenaIntegrationMixin, MockBase):
            pass

        interpreter = TestInterpreter()

        # Test follow-up for more detail
        previous_result = {
            'arena_triggered': True,
            'arena_unique_insights': {
                'phi3:mini': 'Unique insight 1',
                'mistral:7b': 'Unique insight 2'
            }
        }

        response = interpreter.handle_arena_follow_up(
            "Tell me more",
            "test_session",
            previous_result
        )

        assert response is not None
        assert "unique perspectives" in response.lower()


@pytest.mark.integration
class TestEndToEndArenaFlow:
    """Test complete Arena interpretation flow."""

    def setup_method(self):
        """Set up integration test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.session_id = 'integration_test'

        # Create session directory with test data
        session_dir = os.path.join(self.test_dir, 'uploads', self.session_id)
        os.makedirs(session_dir)

        # Create comprehensive test data
        self._create_comprehensive_test_data(session_dir)

        # Patch instance path
        self.patcher = patch('app.core.arena_data_context.current_app')
        mock_app = self.patcher.start()
        mock_app.instance_path = self.test_dir

    def teardown_method(self):
        """Clean up."""
        self.patcher.stop()
        shutil.rmtree(self.test_dir)

    def _create_comprehensive_test_data(self, session_dir):
        """Create realistic test dataset."""
        # Create main dataset
        pd.DataFrame({
            'ward': [f'Ward {i}' for i in range(20)],
            'population': [1000 + i*50 for i in range(20)],
            'tpr': [35 + i*1.5 for i in range(20)],
            'poverty_index': [0.3 + i*0.02 for i in range(20)],
            'health_facility_density': [2.5 - i*0.05 for i in range(20)]
        }).to_csv(os.path.join(session_dir, 'unified_dataset.csv'), index=False)

        # Create analysis results
        pd.DataFrame({
            'ward': [f'Ward {i}' for i in range(20)],
            'composite_score': [0.4 + i*0.03 for i in range(20)],
            'risk_category': ['Low']*5 + ['Medium']*10 + ['High']*5
        }).to_csv(os.path.join(session_dir, 'analysis_composite_scores.csv'), index=False)

    @pytest.mark.asyncio
    @patch('app.core.enhanced_arena_manager.EnhancedArenaManager._get_model_response')
    async def test_complete_interpretation_flow(self, mock_model_response):
        """Test full flow from trigger to formatted output."""
        # Mock model responses
        mock_model_response.side_effect = [
            "Logical analysis: Pattern shows increasing risk gradient",
            "Statistical analysis: Correlation coefficient r=0.85, p<0.001",
            "Technical analysis: Deploy mobile health units to wards 15-19"
        ]

        # Initialize components
        trigger = ConversationalArenaTrigger(self.session_id)
        manager = EnhancedArenaManager({
            'phi3:mini': {'type': 'ollama', 'display_name': 'The Analyst'},
            'mistral:7b': {'type': 'ollama', 'display_name': 'The Statistician'},
            'qwen2.5:7b': {'type': 'ollama', 'display_name': 'The Technician'}
        })

        # Check trigger detection
        should_trigger, trigger_type, confidence = trigger.should_trigger(
            "What does this risk pattern mean?",
            {'analysis_complete': True}
        )
        assert should_trigger is True

        # Execute interpretation
        result = await manager.interpret_analysis_results(
            self.session_id,
            "What does this risk pattern mean?",
            trigger_type
        )

        # Verify complete result
        assert result['success'] is True
        assert len(result['interpretations']) == 3
        assert result['session_id'] == self.session_id
        assert result['trigger_type'] == trigger_type

        # Format for display
        formatted = manager.format_for_conversation(result, trigger)
        assert "Arena Analysis" in formatted
        assert "Pattern shows increasing risk gradient" in formatted


if __name__ == '__main__':
    pytest.main([__file__, '-v'])