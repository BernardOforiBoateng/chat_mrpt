"""
Survey Questions Configuration

Defines the survey questions for cognitive assessment based on ChatMRPT interactions.
Questions are categorized by trigger type and assessment domain.
"""

from typing import Dict, List, Any


class SurveyQuestions:
    """Manages survey questions based on context and triggers."""

    # Question bank organized by trigger type and assessment domain
    QUESTIONS = {
        # Arena Mode Questions
        'arena_comparison': {
            'preference': {
                'id': 'arena_pref_1',
                'text': 'Which model\'s explanation did you find most helpful?',
                'type': 'radio',
                'options': ['Model A', 'Model B', 'Model C'],
                'follow_up': 'Why did you prefer this explanation?',
                'follow_up_type': 'text'
            },
            'comprehension': {
                'id': 'arena_comp_1',
                'text': 'Based on the explanations provided, describe urban microstratification in your own words:',
                'type': 'textarea',
                'required': True
            },
            'clarity': {
                'id': 'arena_clarity_1',
                'text': 'Rate the clarity of each model\'s explanation:',
                'type': 'rating_matrix',
                'options': {
                    'Model A': [1, 2, 3, 4, 5],
                    'Model B': [1, 2, 3, 4, 5],
                    'Model C': [1, 2, 3, 4, 5]
                },
                'labels': ['Very Unclear', 'Unclear', 'Neutral', 'Clear', 'Very Clear']
            },
            'trust': {
                'id': 'arena_trust_1',
                'text': 'How much do you trust each model\'s accuracy?',
                'type': 'rating_matrix',
                'options': {
                    'Model A': [1, 2, 3, 4, 5],
                    'Model B': [1, 2, 3, 4, 5],
                    'Model C': [1, 2, 3, 4, 5]
                },
                'labels': ['Not at all', 'Slightly', 'Moderately', 'Very', 'Completely']
            }
        },

        # Risk Analysis Questions
        'risk_analysis_complete': {
            'interpretation': {
                'id': 'risk_interp_1',
                'text': 'Looking at the risk map, which three wards would you prioritize for intervention and why?',
                'type': 'textarea',
                'required': True
            },
            'methodology_understanding': {
                'id': 'risk_method_1',
                'text': 'Which analysis method (Composite Score or PCA) do you find more intuitive?',
                'type': 'radio',
                'options': ['Composite Score', 'PCA', 'Both equally', 'Neither'],
                'follow_up': 'Please explain your choice:',
                'follow_up_type': 'text'
            },
            'confidence': {
                'id': 'risk_conf_1',
                'text': 'How confident are you in using this risk analysis for decision-making?',
                'type': 'scale',
                'min': 1,
                'max': 5,
                'labels': ['Not confident', 'Slightly confident', 'Moderately confident', 'Very confident', 'Extremely confident']
            },
            'actionability': {
                'id': 'risk_action_1',
                'text': 'How actionable do you find the risk analysis results?',
                'type': 'scale',
                'min': 1,
                'max': 5,
                'labels': ['Not actionable', 'Slightly actionable', 'Moderately actionable', 'Very actionable', 'Extremely actionable']
            }
        },

        # ITN Distribution Questions
        'itn_distribution_generated': {
            'fairness': {
                'id': 'itn_fair_1',
                'text': 'Do you think the ITN distribution is fair across wards?',
                'type': 'radio',
                'options': ['Yes', 'No', 'Partially'],
                'follow_up': 'Please explain your assessment:',
                'follow_up_type': 'textarea'
            },
            'understanding': {
                'id': 'itn_under_1',
                'text': 'Explain how the urban threshold affects ITN distribution:',
                'type': 'textarea',
                'required': True
            },
            'usefulness': {
                'id': 'itn_use_1',
                'text': 'How useful is this ITN distribution plan for your work?',
                'type': 'scale',
                'min': 1,
                'max': 5,
                'labels': ['Not useful', 'Slightly useful', 'Moderately useful', 'Very useful', 'Extremely useful']
            },
            'modification': {
                'id': 'itn_mod_1',
                'text': 'Would you modify the distribution? If yes, how?',
                'type': 'textarea',
                'required': False
            }
        },

        # TPR Analysis Questions
        'tpr_analysis_complete': {
            'interpretation': {
                'id': 'tpr_interp_1',
                'text': 'What does a high TPR indicate about malaria transmission in a ward?',
                'type': 'textarea',
                'required': True
            },
            'data_quality': {
                'id': 'tpr_quality_1',
                'text': 'How would you assess the quality of the TPR data presented?',
                'type': 'radio',
                'options': ['Poor', 'Fair', 'Good', 'Excellent'],
                'follow_up': 'What factors influenced your assessment?',
                'follow_up_type': 'text'
            },
            'decision_impact': {
                'id': 'tpr_decision_1',
                'text': 'How would TPR data influence your intervention planning?',
                'type': 'textarea',
                'required': True
            }
        },

        # General Usability Questions
        'general_usability': {
            'ease_of_use': {
                'id': 'gen_ease_1',
                'text': 'How easy was it to understand ChatMRPT\'s outputs?',
                'type': 'scale',
                'min': 1,
                'max': 5,
                'labels': ['Very difficult', 'Difficult', 'Neutral', 'Easy', 'Very easy']
            },
            'learning_curve': {
                'id': 'gen_learn_1',
                'text': 'How would you describe the learning curve for ChatMRPT?',
                'type': 'radio',
                'options': ['Too steep', 'Manageable', 'Easy', 'Very intuitive']
            },
            'recommendation': {
                'id': 'gen_rec_1',
                'text': 'Would you recommend ChatMRPT to colleagues?',
                'type': 'radio',
                'options': ['Definitely not', 'Probably not', 'Maybe', 'Probably yes', 'Definitely yes'],
                'follow_up': 'What would be your main reason?',
                'follow_up_type': 'text'
            }
        }
    }

    @classmethod
    def get_questions_for_trigger(cls, trigger_type: str, context: Dict[str, Any] = None) -> List[Dict]:
        """Get relevant questions based on trigger type and context."""
        questions = []

        if trigger_type in cls.QUESTIONS:
            question_set = cls.QUESTIONS[trigger_type]

            for category, question in question_set.items():
                # Clone question to avoid modifying original
                q = question.copy()

                # Add context-specific modifications if needed
                if context:
                    q = cls._customize_question(q, context)

                questions.append(q)

        # Add general usability questions periodically
        if context and context.get('include_general', False):
            for category, question in cls.QUESTIONS['general_usability'].items():
                questions.append(question.copy())

        return questions

    @classmethod
    def _customize_question(cls, question: Dict, context: Dict) -> Dict:
        """Customize question based on context."""
        # For arena questions, replace generic model names with actual models
        if 'models' in context and 'Model A' in str(question):
            models = context['models']
            if len(models) >= 3:
                question_str = str(question)
                question_str = question_str.replace('Model A', models[0])
                question_str = question_str.replace('Model B', models[1])
                question_str = question_str.replace('Model C', models[2])
                # This is a simplified example - in practice, you'd properly parse and replace

        # Add session-specific context to questions
        if 'session_id' in context:
            question['session_context'] = context['session_id']

        return question

    @classmethod
    def get_question_by_id(cls, question_id: str) -> Dict:
        """Get a specific question by its ID."""
        for trigger_type, questions in cls.QUESTIONS.items():
            for category, question in questions.items():
                if question.get('id') == question_id:
                    return question
        return None

    @classmethod
    def validate_response(cls, question_id: str, response: Any) -> bool:
        """Validate a response based on question requirements."""
        question = cls.get_question_by_id(question_id)

        if not question:
            return False

        # Check required fields
        if question.get('required', False) and not response:
            return False

        # Validate based on question type
        if question['type'] == 'radio' and response not in question.get('options', []):
            return False

        if question['type'] == 'scale':
            try:
                value = int(response)
                return question['min'] <= value <= question['max']
            except (ValueError, TypeError):
                return False

        return True