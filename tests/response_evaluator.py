"""
Response Quality Evaluator
Evaluates agent responses based on comprehensive criteria
"""

import re
import os
from typing import Dict, List, Tuple

# Lazy import openai to avoid dependency issues
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class ResponseEvaluator:
    """Evaluates agent response quality with detailed scoring"""

    def __init__(self):
        self.openai_key = os.getenv('OPENAI_API_KEY')
        if self.openai_key:
            openai.api_key = self.openai_key

    def automated_checks(self, response: str, category: str) -> Dict[str, bool]:
        """Run automated keyword/pattern checks"""
        response_lower = response.lower()

        checks = {
            # General quality indicators
            'mentions_tpr': 'tpr' in response_lower or 'test positivity' in response_lower,
            'provides_examples': any(x in response_lower for x in ['example:', 'for instance', 'such as', 'like']),
            'asks_clarifying_question': '?' in response,
            'has_structure': bool(re.search(r'\d+\.|\d+\)', response)) or '\n' in response,
            'mentions_next_steps': any(x in response_lower for x in ['next', 'step', 'then', 'after']),

            # Category-specific checks
            'beginner_friendly': category == 'BEGINNER' and not any(x in response_lower for x in ['algorithm', 'parameter', 'function']),
            'acknowledges_limitation': any(x in response_lower for x in ['can\'t', 'cannot', 'unable', 'not able', 'limitation', 'currently']),
            'offers_alternative': any(x in response_lower for x in ['instead', 'alternatively', 'you can', 'try', 'option']),
            'shows_empathy': any(x in response_lower for x in ['understand', 'help you', 'let\'s', 'we can', 'i\'ll help']),
            'uses_analogy': any(x in response_lower for x in ['like', 'similar to', 'think of', 'imagine', 'as if']),

            # Workflow awareness
            'mentions_workflow': any(x in response_lower for x in ['workflow', 'process', 'stage']),
            'provides_options': response_lower.count('option') > 0 or response_lower.count('choice') > 0,
            'explains_why': any(x in response_lower for x in ['because', 'reason', 'why', 'so that']),

            # Helpfulness indicators
            'has_sufficient_length': len(response) > 200,  # Not too terse
            'not_too_long': len(response) < 2000,  # Not overwhelming
            'polite_tone': any(x in response_lower for x in ['please', 'thank', 'happy to']),
        }

        return checks

    def calculate_automated_score(self, checks: Dict[str, bool], category: str) -> Tuple[int, List[str]]:
        """Calculate score from automated checks with category-specific weights"""

        score = 0
        reasons = []

        # Category-specific scoring
        if category == 'BEGINNER':
            if checks['mentions_tpr']:
                score += 10
                reasons.append("+10: Explains TPR")
            if checks['beginner_friendly']:
                score += 10
                reasons.append("+10: Beginner-friendly language")
            if checks['provides_examples']:
                score += 8
                reasons.append("+8: Provides examples")
            if checks['shows_empathy']:
                score += 7
                reasons.append("+7: Shows empathy")
            if checks['mentions_next_steps']:
                score += 5
                reasons.append("+5: Mentions next steps")

        elif category == 'NATURAL':
            if checks['has_structure']:
                score += 10
                reasons.append("+10: Well-structured response")
            if checks['mentions_workflow']:
                score += 10
                reasons.append("+10: Initiates workflow")
            if checks['asks_clarifying_question']:
                score += 8
                reasons.append("+8: Asks clarifying questions")
            if checks['provides_options']:
                score += 7
                reasons.append("+7: Provides options")
            if checks['mentions_next_steps']:
                score += 5
                reasons.append("+5: Clear next steps")

        elif category == 'BIZARRE':
            if checks['shows_empathy']:
                score += 12
                reasons.append("+12: Handles gracefully")
            if checks['mentions_workflow']:
                score += 10
                reasons.append("+10: Returns to workflow")
            if checks['polite_tone']:
                score += 8
                reasons.append("+8: Professional tone")
            if checks['has_sufficient_length']:
                score += 5
                reasons.append("+5: Adequate response")
            if checks['not_too_long']:
                score += 5
                reasons.append("+5: Concise")

        elif category == 'EXPORT':
            if checks['acknowledges_limitation']:
                score += 15
                reasons.append("+15: Honest about limitations")
            if checks['offers_alternative']:
                score += 15
                reasons.append("+15: Offers alternatives")
            if checks['mentions_next_steps']:
                score += 7
                reasons.append("+7: Continues productively")
            if checks['shows_empathy']:
                score += 3
                reasons.append("+3: Helpful tone")

        elif category == 'WORKFLOW':
            if checks['explains_why']:
                score += 12
                reasons.append("+12: Explains why steps needed")
            if checks['provides_options']:
                score += 10
                reasons.append("+10: Provides clear options")
            if checks['shows_empathy']:
                score += 8
                reasons.append("+8: Patient tone")
            if checks['mentions_next_steps']:
                score += 5
                reasons.append("+5: Clear path forward")
            if checks['polite_tone']:
                score += 5
                reasons.append("+5: Non-condescending")

        elif category == 'EDGE':
            if checks['shows_empathy']:
                score += 15
                reasons.append("+15: Shows empathy")
            if checks['has_sufficient_length']:
                score += 10
                reasons.append("+10: Substantial response")
            if checks['mentions_next_steps']:
                score += 10
                reasons.append("+10: Clear next step")
            if checks['not_too_long']:
                score += 5
                reasons.append("+5: Simplified response")

        elif category == 'HELP':
            if checks['has_structure']:
                score += 12
                reasons.append("+12: Step-by-step structure")
            if checks['uses_analogy']:
                score += 12
                reasons.append("+12: Uses analogies")
            if checks['provides_examples']:
                score += 8
                reasons.append("+8: Provides examples")
            if checks['asks_clarifying_question']:
                score += 5
                reasons.append("+5: Checks understanding")
            if checks['shows_empathy']:
                score += 3
                reasons.append("+3: Encouraging tone")

        return score, reasons

    def llm_evaluate(self, user_query: str, agent_response: str, category: str) -> Tuple[int, str]:
        """Use GPT-4 as a judge to evaluate response quality"""

        if not OPENAI_AVAILABLE:
            return 50, "OpenAI module not available - returning neutral score"

        if not self.openai_key:
            return 50, "OpenAI API key not available - returning neutral score"

        # Category-specific evaluation criteria
        category_criteria = {
            'BEGINNER': """
            1. Explains concepts clearly (0-20)
            2. Uses beginner-friendly language (0-20)
            3. Provides helpful guidance (0-20)
            4. Shows patience/encouragement (0-20)
            5. Gives concrete next steps (0-20)
            """,
            'NATURAL': """
            1. Correctly interprets multi-part request (0-20)
            2. Addresses all components (0-20)
            3. Prioritizes actions logically (0-20)
            4. Initiates appropriate workflow (0-20)
            5. Confirms understanding (0-20)
            """,
            'BIZARRE': """
            1. Answers question if reasonable (0-20)
            2. Returns to workflow context (0-25)
            3. Maintains professional tone (0-20)
            4. Handles gracefully without confusion (0-20)
            5. Sets appropriate boundaries (0-15)
            """,
            'EXPORT': """
            1. Honest about capabilities (0-30)
            2. Offers specific alternatives (0-25)
            3. Explains what user CAN do (0-20)
            4. Maintains helpfulness (0-15)
            5. Continues workflow productively (0-10)
            """,
            'WORKFLOW': """
            1. Explains why steps are needed (0-30)
            2. Provides clear options (0-25)
            3. Non-condescending tone (0-20)
            4. Offers autonomous alternative if possible (0-15)
            5. Keeps user engaged (0-10)
            """,
            'EDGE': """
            1. Extracts core need from rambling (0-30)
            2. Shows empathy/understanding (0-25)
            3. Simplifies response appropriately (0-20)
            4. Provides reassurance (0-15)
            5. Focuses on clear next step (0-10)
            """,
            'HELP': """
            1. Adjusts to requested level (0-30)
            2. Uses analogies/examples (0-25)
            3. Step-by-step structure (0-20)
            4. Checks understanding (0-15)
            5. Engaging/encouraging (0-10)
            """
        }

        criteria = category_criteria.get(category, category_criteria['BEGINNER'])

        evaluation_prompt = f"""You are evaluating a conversational AI agent's response quality for a malaria analysis tool.

User Query: "{user_query}"

Agent Response: "{agent_response}"

Test Category: {category}

Evaluate the response based on these criteria (total 100 points):
{criteria}

IMPORTANT: Be strict but fair. A perfect score (100) should be rare. Good responses should score 70-85.

Provide:
1. Score for each criterion
2. Total score (0-100)
3. Brief 2-sentence justification

Format your response as:
SCORES: [criterion1]: X, [criterion2]: Y, ...
TOTAL: X
JUSTIFICATION: [Your 2-sentence assessment]
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at evaluating conversational AI quality. Be strict but fair in your assessments."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            evaluation_text = response.choices[0].message.content

            # Extract total score
            total_match = re.search(r'TOTAL:\s*(\d+)', evaluation_text)
            if total_match:
                total_score = int(total_match.group(1))
            else:
                total_score = 50  # Default if parsing fails

            return total_score, evaluation_text

        except Exception as e:
            return 50, f"LLM evaluation failed: {str(e)}"

    def evaluate_response(self, user_query: str, agent_response: str, category: str,
                         use_llm: bool = True) -> Dict:
        """Complete evaluation of a response"""

        # Run automated checks
        checks = self.automated_checks(agent_response, category)
        auto_score, auto_reasons = self.calculate_automated_score(checks, category)

        # Run LLM evaluation if available
        if use_llm and self.openai_key:
            llm_score, llm_justification = self.llm_evaluate(user_query, agent_response, category)
        else:
            llm_score = 50
            llm_justification = "LLM evaluation not available"

        # Calculate final score (40% automated, 50% LLM, 10% length bonus)
        length_bonus = 0
        if 200 <= len(agent_response) <= 1500:
            length_bonus = 10
        elif len(agent_response) > 100:
            length_bonus = 5

        final_score = int((auto_score * 0.4) + (llm_score * 0.5) + length_bonus)

        # Determine grade
        if final_score >= 80:
            grade = "EXCELLENT"
            grade_emoji = "🌟"
        elif final_score >= 70:
            grade = "GOOD"
            grade_emoji = "✅"
        elif final_score >= 60:
            grade = "ACCEPTABLE"
            grade_emoji = "⚠️"
        else:
            grade = "NEEDS WORK"
            grade_emoji = "❌"

        return {
            'final_score': final_score,
            'grade': grade,
            'grade_emoji': grade_emoji,
            'automated_score': auto_score,
            'llm_score': llm_score,
            'length_bonus': length_bonus,
            'checks_passed': checks,
            'automated_reasons': auto_reasons,
            'llm_justification': llm_justification,
            'response_length': len(agent_response)
        }

    def get_category_benchmark(self, category: str) -> Dict:
        """Get expected benchmark scores for category"""
        benchmarks = {
            'BEGINNER': {'excellent': 80, 'good': 60, 'acceptable': 40},
            'NATURAL': {'excellent': 80, 'good': 60, 'acceptable': 40},
            'BIZARRE': {'excellent': 80, 'good': 60, 'acceptable': 40},
            'EXPORT': {'excellent': 70, 'good': 50, 'acceptable': 30},  # Lower due to limitation
            'WORKFLOW': {'excellent': 80, 'good': 60, 'acceptable': 40},
            'EDGE': {'excellent': 80, 'good': 60, 'acceptable': 40},
            'HELP': {'excellent': 85, 'good': 65, 'acceptable': 45},
        }
        return benchmarks.get(category, benchmarks['BEGINNER'])
