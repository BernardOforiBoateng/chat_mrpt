"""
Test Script for Arena Integration
Tests the complete Arena simplification implementation
"""

import sys
import os
import json
import time
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ArenaIntegrationTester:
    """Test suite for Arena integration."""

    def __init__(self):
        self.test_results = []
        self.session_id = f"test_arena_{int(time.time())}"

    def setup_test_environment(self):
        """Set up test environment."""
        logger.info("🔧 Setting up test environment...")

        # Create test session directory
        session_dir = Path(f"instance/uploads/{self.session_id}")
        session_dir.mkdir(parents=True, exist_ok=True)

        # Create sample analysis results
        import pandas as pd

        # Create sample analysis data
        data = {
            'WardName': ['Ward A', 'Ward B', 'Ward C', 'Ward D', 'Ward E'],
            'composite_score': [0.85, 0.72, 0.65, 0.45, 0.30],
            'pfpr': [35, 28, 22, 15, 8],
            'population': [5000, 7500, 6000, 4500, 3000],
            'vulnerability_category': ['High', 'High', 'Medium', 'Low', 'Low']
        }
        df = pd.DataFrame(data)
        df.to_csv(session_dir / 'analysis_rankings.csv', index=False)

        # Create TPR results
        tpr_data = {
            'WardName': ['Ward A', 'Ward B', 'Ward C', 'Ward D', 'Ward E'],
            'TPR': [45.2, 38.5, 25.3, 18.7, 12.1],
            'tested': [100, 150, 120, 90, 60],
            'positive': [45, 58, 30, 17, 7]
        }
        tpr_df = pd.DataFrame(tpr_data)
        tpr_df.to_csv(session_dir / 'tpr_results.csv', index=False)

        logger.info(f"✅ Test environment created with session_id: {self.session_id}")
        return True

    def test_smart_request_handler(self):
        """Test the SmartRequestHandler routing."""
        logger.info("\n🧪 TEST 1: SmartRequestHandler Routing")

        try:
            from app.web.routes.analysis_routes import smart_handler

            test_cases = [
                {
                    'message': "run malaria risk analysis",
                    'expected': 'needs_tools',
                    'description': 'Tool trigger phrase'
                },
                {
                    'message': "What does this mean?",
                    'expected': 'can_answer',
                    'description': 'Interpretation request'
                },
                {
                    'message': "What is malaria?",
                    'expected': 'can_answer',
                    'description': 'General knowledge'
                },
                {
                    'message': "plot the vulnerability map",
                    'expected': 'needs_tools',
                    'description': 'Visualization trigger'
                }
            ]

            passed = 0
            failed = 0

            for test in test_cases:
                context = {'analysis_complete': True}
                result = smart_handler.handle_request(test['message'], context)

                if result == test['expected']:
                    logger.info(f"  ✅ PASS: '{test['description']}' -> {result}")
                    passed += 1
                else:
                    logger.error(f"  ❌ FAIL: '{test['description']}' - Expected {test['expected']}, got {result}")
                    failed += 1

            logger.info(f"\nResults: {passed} passed, {failed} failed")

            self.test_results.append({
                'test': 'SmartRequestHandler',
                'passed': passed,
                'failed': failed,
                'success': failed == 0
            })

            return failed == 0

        except Exception as e:
            logger.error(f"  ❌ ERROR: {e}")
            self.test_results.append({
                'test': 'SmartRequestHandler',
                'error': str(e),
                'success': False
            })
            return False

    def test_arena_data_context(self):
        """Test Arena's ability to access full data context."""
        logger.info("\n🧪 TEST 2: Arena Data Context Loading")

        try:
            # Test Arena Manager's context loading directly
            from app.core.arena_manager import ArenaManager

            arena = ArenaManager()

            # Test loading interpretation context
            context = arena._load_interpretation_context(self.session_id)

            # Verify context contains expected data
            checks = [
                ('analysis_results' in context, "Analysis results loaded"),
                ('tpr_results' in context, "TPR results loaded"),
                (context.get('analysis_complete', False), "Analysis marked complete"),
                (context.get('data_loaded', False), "Data marked loaded")
            ]

            passed = 0
            failed = 0

            for check, description in checks:
                if check:
                    logger.info(f"  ✅ PASS: {description}")
                    passed += 1
                else:
                    logger.error(f"  ❌ FAIL: {description}")
                    failed += 1

            # Log what was loaded
            if context.get('analysis_results'):
                logger.info(f"  📊 Analysis: {context['analysis_results'].get('total_wards', 0)} wards")
            if context.get('tpr_results'):
                logger.info(f"  📈 TPR: {context['tpr_results'].get('high_risk_count', 0)} high-risk wards")

            self.test_results.append({
                'test': 'Arena Data Context',
                'passed': passed,
                'failed': failed,
                'success': failed == 0
            })

            return failed == 0

        except Exception as e:
            logger.error(f"  ❌ ERROR: {e}")
            self.test_results.append({
                'test': 'Arena Data Context',
                'error': str(e),
                'success': False
            })
            return False

    def test_arena_interpretation_methods(self):
        """Test Arena manager's interpretation methods."""
        logger.info("\n🧪 TEST 3: Arena Manager Interpretation Methods")

        try:
            from app.core.arena_manager import ArenaManager

            arena = ArenaManager()

            # Test context loading
            context = arena._load_interpretation_context(self.session_id)

            checks = [
                (context.get('statistics') is not None, "Statistics loaded"),
                (context.get('analysis_complete', False), "Analysis status detected"),
                ('tpr_data' in context, "TPR data loaded")
            ]

            passed = 0
            failed = 0

            for check, description in checks:
                if check:
                    logger.info(f"  ✅ PASS: {description}")
                    passed += 1
                else:
                    logger.error(f"  ❌ FAIL: {description}")
                    failed += 1

            # Test prompt building
            tool_results = {
                'results': {
                    'total_wards': 5,
                    'high_risk_wards': 2
                }
            }

            prompt = arena._build_interpretation_prompt(
                "What does this mean?",
                tool_results,
                context
            )

            if "User's Question:" in prompt and "Tool Results:" in prompt:
                logger.info("  ✅ PASS: Interpretation prompt built correctly")
                passed += 1
            else:
                logger.error("  ❌ FAIL: Prompt missing required sections")
                failed += 1

            self.test_results.append({
                'test': 'Arena Manager Methods',
                'passed': passed,
                'failed': failed,
                'success': failed == 0
            })

            return failed == 0

        except Exception as e:
            logger.error(f"  ❌ ERROR: {e}")
            self.test_results.append({
                'test': 'Arena Manager Methods',
                'error': str(e),
                'success': False
            })
            return False

    def test_arena_trigger_detection(self):
        """Test Arena trigger detection in RequestInterpreter."""
        logger.info("\n🧪 TEST 4: Arena Trigger Detection")

        try:
            from app.core.arena_trigger_detector import ConversationalArenaTrigger

            detector = ConversationalArenaTrigger()

            test_cases = [
                {
                    'message': "What does this mean?",
                    'context': {'analysis_complete': True, 'data_loaded': True},
                    'expected': True,
                    'description': 'Explicit interpretation'
                },
                {
                    'message': "Explain these results",
                    'context': {'analysis_complete': True, 'data_loaded': True},
                    'expected': True,
                    'description': 'Explain trigger'
                },
                {
                    'message': "Why is Ward A high risk?",
                    'context': {'analysis_complete': True, 'data_loaded': True},
                    'expected': True,
                    'description': 'Contextual question'
                },
                {
                    'message': "What is malaria?",
                    'context': {'analysis_complete': False, 'data_loaded': False},
                    'expected': False,
                    'description': 'General knowledge (no trigger)'
                }
            ]

            passed = 0
            failed = 0

            for test in test_cases:
                result = detector.detect_trigger(test['message'], test['context'])
                triggered = result.get('use_arena', False)

                if triggered == test['expected']:
                    logger.info(f"  ✅ PASS: '{test['description']}' -> {triggered}")
                    passed += 1
                else:
                    logger.error(f"  ❌ FAIL: '{test['description']}' - Expected {test['expected']}, got {triggered}")
                    failed += 1

            self.test_results.append({
                'test': 'Arena Trigger Detection',
                'passed': passed,
                'failed': failed,
                'success': failed == 0
            })

            return failed == 0

        except Exception as e:
            logger.error(f"  ❌ ERROR: {e}")
            self.test_results.append({
                'test': 'Arena Trigger Detection',
                'error': str(e),
                'success': False
            })
            return False

    def test_tool_arena_pipeline(self):
        """Test the Tool→Arena pipeline."""
        logger.info("\n🧪 TEST 5: Tool→Arena Pipeline")

        try:
            from app.core.tool_arena_pipeline import ToolArenaPipeline

            pipeline = ToolArenaPipeline()

            # Test context preparation
            tool_response = {
                'success': True,
                'results': {'analysis_complete': True},
                'tools_used': ['analysis']
            }

            context = pipeline.prepare_interpretation_context(
                "Run analysis and explain",
                tool_response,
                self.session_id,
                {}
            )

            checks = [
                ('original_query' in context, "Original query preserved"),
                ('tool_results' in context, "Tool results included"),
                ('session_data' in context, "Session data loaded")
            ]

            passed = 0
            failed = 0

            for check, description in checks:
                if check:
                    logger.info(f"  ✅ PASS: {description}")
                    passed += 1
                else:
                    logger.error(f"  ❌ FAIL: {description}")
                    failed += 1

            # Test prompt building
            prompt = pipeline.build_interpretation_prompt(
                "What does this mean?",
                tool_response,
                context
            )

            if "User asked:" in prompt and "Tool Execution Results" in prompt:
                logger.info("  ✅ PASS: Pipeline prompt built correctly")
                passed += 1
            else:
                logger.error("  ❌ FAIL: Pipeline prompt incomplete")
                failed += 1

            # Test metrics
            metrics = pipeline.get_metrics()
            logger.info(f"  📊 Pipeline metrics: {metrics}")

            self.test_results.append({
                'test': 'Tool→Arena Pipeline',
                'passed': passed,
                'failed': failed,
                'success': failed == 0
            })

            return failed == 0

        except Exception as e:
            logger.error(f"  ❌ ERROR: {e}")
            self.test_results.append({
                'test': 'Tool→Arena Pipeline',
                'error': str(e),
                'success': False
            })
            return False

    def cleanup(self):
        """Clean up test environment."""
        logger.info("\n🧹 Cleaning up test environment...")

        import shutil
        session_dir = Path(f"instance/uploads/{self.session_id}")
        if session_dir.exists():
            shutil.rmtree(session_dir)
            logger.info("✅ Test data cleaned up")

    def run_all_tests(self):
        """Run all tests."""
        logger.info("=" * 60)
        logger.info("🎯 ARENA INTEGRATION TEST SUITE")
        logger.info("=" * 60)

        # Set up environment
        self.setup_test_environment()

        # Run tests
        tests = [
            self.test_smart_request_handler,
            self.test_arena_data_context,
            self.test_arena_interpretation_methods,
            self.test_arena_trigger_detection,
            self.test_tool_arena_pipeline
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                logger.error(f"Test failed with exception: {e}")

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)

        total_passed = 0
        total_failed = 0
        all_success = True

        for result in self.test_results:
            test_name = result['test']
            if 'error' in result:
                logger.error(f"❌ {test_name}: ERROR - {result['error']}")
                all_success = False
            else:
                passed = result.get('passed', 0)
                failed = result.get('failed', 0)
                total_passed += passed
                total_failed += failed

                if result['success']:
                    logger.info(f"✅ {test_name}: PASSED ({passed}/{passed + failed})")
                else:
                    logger.error(f"❌ {test_name}: FAILED ({passed}/{passed + failed})")
                    all_success = False

        logger.info(f"\n🏆 Overall: {total_passed} passed, {total_failed} failed")

        if all_success:
            logger.info("✅ ALL TESTS PASSED! Arena integration is working correctly.")
        else:
            logger.warning("⚠️ Some tests failed. Review the logs above for details.")

        # Clean up
        self.cleanup()

        return all_success


if __name__ == "__main__":
    tester = ArenaIntegrationTester()
    success = tester.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)