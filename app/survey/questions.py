"""
Survey Questions Configuration - Appendix 5 Cognitive Assessment

These questions are taken directly from the ChatMRPT protocol Appendix 5.
They assess user comprehension and interpretation of ChatMRPT outputs.
"""

from typing import Dict, List, Any


class SurveyQuestions:
    """Manages survey questions based on Appendix 5 of the ChatMRPT protocol."""

    # Question bank from Appendix 5 - Cognitive Assessment
    QUESTIONS = {
        # General Malaria Knowledge Questions
        'urban_microstratification': {
            'model_selection': {
                'id': 'micro_model',
                'text': 'What is urban microstratification? (Select your preferred model answer)',
                'type': 'model_comparison',
                'instruction': 'System will show model answers two at a time'
            },
            'reason': {
                'id': 'micro_reason',
                'text': 'What stood out for you in the answer you chose?',
                'type': 'text',
                'required': True
            },
            'agreement': {
                'id': 'micro_agree',
                'text': 'Does your understanding of urban microstratification match what the tool says?',
                'type': 'scale',
                'min': 1,
                'max': 5,
                'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
            },
            'missing': {
                'id': 'micro_missing',
                'text': 'What aspect of the definition is missing/needs refinement based on your understanding?',
                'type': 'textarea',
                'required': False
            },
            'confidence': {
                'id': 'micro_conf',
                'text': 'How confident are you to explain this to your colleagues?',
                'type': 'scale',
                'min': 0,
                'max': 100,
                'labels': ['Not confident', '', '', '', 'Very confident']
            },
            'teachback': {
                'id': 'micro_teach',
                'text': 'In your own words, can you paraphrase the answer the model provided?',
                'type': 'textarea',
                'required': True
            },
            'quiz': {
                'id': 'micro_quiz',
                'text': 'Microstratification is primarily used to...',
                'type': 'radio',
                'options': [
                    'Identify within-city risk differences',  # Correct
                    'Measure ward population only',
                    'Map certainty only'
                ],
                'correct': 0
            }
        },

        # Within Ward Heterogeneity Questions
        'ward_heterogeneity': {
            'model_selection': {
                'id': 'hetero_model',
                'text': 'What is within ward heterogeneity (variation) in the context of urban area settlements?',
                'type': 'model_comparison'
            },
            'reason': {
                'id': 'hetero_reason',
                'text': 'What stood out for you in the answer you chose?',
                'type': 'text',
                'required': True
            },
            'agreement': {
                'id': 'hetero_agree',
                'text': 'Does your understanding of within ward heterogeneity match what the tool says?',
                'type': 'scale',
                'min': 1,
                'max': 5,
                'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
            },
            'missing': {
                'id': 'hetero_missing',
                'text': 'What aspect of the narrative is missing/needs refinement based on your understanding?',
                'type': 'textarea',
                'required': False
            },
            'confidence': {
                'id': 'hetero_conf',
                'text': 'How confident are you to explain within ward heterogeneity to your colleagues?',
                'type': 'scale',
                'min': 0,
                'max': 100
            },
            'teachback': {
                'id': 'hetero_teach',
                'text': 'In your own words, what is within-ward heterogeneity in urban areas, and why does it matter for planning?',
                'type': 'textarea',
                'required': True
            },
            'quiz': {
                'id': 'hetero_quiz',
                'text': 'Within ward heterogeneity refers to...',
                'type': 'radio',
                'options': [
                    'Variation in risk, population, and context within neighborhoods of the same ward',  # Correct
                    'Differences between cities',
                    'Random measurement error only',
                    'Total population differences across wards'
                ],
                'correct': 0
            }
        },

        # Malaria Risk Score Questions
        'risk_score': {
            'model_selection': {
                'id': 'risk_model',
                'text': 'Define malaria risk score and name two indicators that you could use to create a risk score.',
                'type': 'model_comparison'
            },
            'reason': {
                'id': 'risk_reason',
                'text': 'What stood out for you in the answer you chose?',
                'type': 'text',
                'required': True
            },
            'agreement': {
                'id': 'risk_agree',
                'text': 'Does your understanding of malaria risk score match what the tool says?',
                'type': 'scale',
                'min': 1,
                'max': 5,
                'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
            },
            'missing': {
                'id': 'risk_missing',
                'text': 'What aspect of the narrative is missing/needs refinement based on your understanding?',
                'type': 'textarea',
                'required': False
            },
            'confidence': {
                'id': 'risk_conf',
                'text': "How confident are you to explain ChatMRPT's malaria risk score to your colleagues?",
                'type': 'scale',
                'min': 0,
                'max': 100
            },
            'teachback': {
                'id': 'risk_teach',
                'text': 'In your own words, what is malaria risk score in urban areas, and why does it matter for planning?',
                'type': 'textarea',
                'required': True
            },
            'quiz': {
                'id': 'risk_quiz',
                'text': 'A malaria risk score is...',
                'type': 'radio',
                'options': [
                    'A composite of normalized indicators for a ward',  # Correct
                    'Just the raw TPR percentage',
                    "The ward's population size",
                    'A measure of model certainty'
                ],
                'correct': 0
            }
        },

        # Reprioritization Questions
        'reprioritization': {
            'model_selection': {
                'id': 'repri_model',
                'text': 'What is reprioritization?',
                'type': 'model_comparison'
            },
            'reason': {
                'id': 'repri_reason',
                'text': 'What stood out for you in the answer you chose?',
                'type': 'text',
                'required': True
            },
            'agreement': {
                'id': 'repri_agree',
                'text': 'Does your understanding of reprioritization match what the tool says?',
                'type': 'scale',
                'min': 1,
                'max': 5,
                'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
            },
            'missing': {
                'id': 'repri_missing',
                'text': 'What aspect of the narrative is missing/needs refinement based on your understanding?',
                'type': 'textarea',
                'required': False
            },
            'confidence': {
                'id': 'repri_conf',
                'text': 'How confident are you to explain reprioritization to your colleagues?',
                'type': 'scale',
                'min': 0,
                'max': 100
            },
            'teachback': {
                'id': 'repri_teach',
                'text': 'In your own words, what is reprioritization in urban areas, and why does it matter for planning?',
                'type': 'textarea',
                'required': True
            },
            'quiz': {
                'id': 'repri_quiz',
                'text': 'Reprioritization mainly means...',
                'type': 'radio',
                'options': [
                    'Strategically scale down the distribution of bed nets for flagged areas',  # Correct (based on context)
                    'Expanding bed net distribution to all areas equally, regardless of malaria risk',
                    'Stopping the distribution of bed nets entirely in all states',
                    'Increasing bed net distribution in areas already marked as low risk'
                ],
                'correct': 0
            }
        },

        # High-Risk Areas Questions
        'high_risk_areas': {
            'model_selection': {
                'id': 'highrisk_model',
                'text': 'What are the characteristics of high-risk areas/wards in your state and why does it matter for planning?',
                'type': 'model_comparison'
            },
            'reason': {
                'id': 'highrisk_reason',
                'text': 'What stood out for you in the answer you chose?',
                'type': 'text',
                'required': True
            },
            'agreement': {
                'id': 'highrisk_agree',
                'text': 'Does your understanding of high-risk areas in wards match what the tool says?',
                'type': 'scale',
                'min': 1,
                'max': 5,
                'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
            },
            'missing': {
                'id': 'highrisk_missing',
                'text': 'What aspect of the narrative is missing/needs refinement based on your understanding?',
                'type': 'textarea',
                'required': False
            },
            'confidence': {
                'id': 'highrisk_conf',
                'text': 'How confident are you to explain the characteristics of high-risk areas within wards to your colleagues?',
                'type': 'scale',
                'min': 0,
                'max': 100
            },
            'teachback': {
                'id': 'highrisk_teach',
                'text': 'In your own words, what are the characteristics of high-risk areas/wards in your state, and why does it matter for planning?',
                'type': 'textarea',
                'required': True
            },
            'quiz': {
                'id': 'highrisk_quiz',
                'text': 'Which pattern most often signals higher risk in urban wards?',
                'type': 'radio',
                'options': [
                    'Dense informal housing near poor drainage/stagnant water/poor housing and near vegetation and water bodies',  # Correct
                    'High-elevation windy ridge with no standing water',
                    'Recently sprayed area with high ITN coverage',
                    'Daytime office district with low nighttime residence'
                ],
                'correct': 0
            }
        },

        # TPR Analysis Questions
        'tpr_calculation': {
            'model_selection': {
                'id': 'tpr_model',
                'text': 'How do you calculate test positivity rate (TPR) among under-fives in the low-risk ward?',
                'type': 'model_comparison'
            },
            'reason': {
                'id': 'tpr_reason',
                'text': 'What stood out to you in the answer you chose?',
                'type': 'text',
                'required': True
            },
            'agreement': {
                'id': 'tpr_agree',
                'text': 'Does your understanding of TPR among under-fives match what the tool reports for the low-risk ward?',
                'type': 'scale',
                'min': 1,
                'max': 5,
                'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
            },
            'missing': {
                'id': 'tpr_missing',
                'text': "What's missing/needs refinement?",
                'type': 'textarea',
                'required': False
            },
            'confidence': {
                'id': 'tpr_conf',
                'text': 'How confident are you reporting under-five TPR calculation?',
                'type': 'scale',
                'min': 0,
                'max': 100
            },
            'teachback': {
                'id': 'tpr_teach',
                'text': 'In your own words, define "TPR among under-fives" and how it\'s shown in ChatMRPT.',
                'type': 'textarea',
                'required': True
            },
            'quiz': {
                'id': 'tpr_quiz',
                'text': '"Under-five TPR" is...',
                'type': 'radio',
                'options': [
                    'Total of positive tests <5 / total tested among children <5',  # Correct
                    'Positives / total ward population',
                    'Incidence per 1,000 under-fives',
                    'A certainty score'
                ],
                'correct': 0
            }
        },

        # High TPR and Environmental Risk Questions
        'tpr_environmental': {
            'model_selection': {
                'id': 'tpr_env_model',
                'text': 'Are there any wards with high TPR and high environmental risk?',
                'type': 'model_comparison'
            },
            'reason': {
                'id': 'tpr_env_reason',
                'text': 'What convinced you this answer was best?',
                'type': 'text',
                'required': True
            },
            'agreement': {
                'id': 'tpr_env_agree',
                'text': 'Does your understanding of "high-high" (TPR and environmental risk) match the tool\'s definitions and thresholds?',
                'type': 'scale',
                'min': 1,
                'max': 5,
                'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
            },
            'unclear': {
                'id': 'tpr_env_unclear',
                'text': "What's unclear?",
                'type': 'textarea',
                'required': False
            },
            'confidence': {
                'id': 'tpr_env_conf',
                'text': 'How confident are you identifying high-risk wards and explaining your choice to a friend?',
                'type': 'scale',
                'min': 0,
                'max': 100
            },
            'teachback': {
                'id': 'tpr_env_teach',
                'text': 'Explain what "high TPR and high environmental risk" implies for prioritization.',
                'type': 'textarea',
                'required': True
            },
            'quiz': {
                'id': 'tpr_env_quiz',
                'text': 'If both TPR and environmental risk are high, the ward...',
                'type': 'radio',
                'options': [
                    'Likely warrants priority attention (Consistent signals)',  # Correct
                    'Should be de-prioritized',
                    'Indicates a data error by default',
                    'Has low uncertainty'
                ],
                'correct': 0
            }
        },

        # TPR and Risk Index Relationship
        'tpr_risk_relationship': {
            'model_selection': {
                'id': 'tpr_rel_model',
                'text': 'What\'s the overall directional relationship between TPR and risk index?',
                'type': 'model_comparison'
            },
            'reason': {
                'id': 'tpr_rel_reason',
                'text': 'What made this computation/explanation clearest?',
                'type': 'text',
                'required': True
            },
            'agreement': {
                'id': 'tpr_rel_agree',
                'text': 'Does your understanding of directional relationship between TPR and composite score match the tool\'s?',
                'type': 'scale',
                'min': 1,
                'max': 5,
                'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
            },
            'why': {
                'id': 'tpr_rel_why',
                'text': 'Why do you agree/disagree with this?',
                'type': 'textarea',
                'required': False
            },
            'confidence': {
                'id': 'tpr_rel_conf',
                'text': 'How confident are you in discussing the tool\'s output to this answer to your workmates or collaborators?',
                'type': 'scale',
                'min': 0,
                'max': 100
            },
            'teachback': {
                'id': 'tpr_rel_teach',
                'text': 'Describe how you\'d investigate the directional relationship of TPR with distance to water bodies (add caveats if any).',
                'type': 'textarea',
                'required': True
            },
            'quiz': {
                'id': 'tpr_rel_quiz',
                'text': 'What is the overall directional relationship between TPR and risk index?',
                'type': 'radio',
                'options': [
                    'There is a positive relationship with higher risk index values generally corresponding to higher TPRs',  # Correct
                    'There is a negative relationship with higher risk index values correspond to lower TPRs',
                    'There is no relationship TPR and risk index are unrelated',
                    'The relationship is completely random and does not follow any directional pattern'
                ],
                'correct': 0
            }
        },

        # Imputation Questions
        'tpr_imputation': {
            'model_selection': {
                'id': 'impute_model',
                'text': 'Which wards had missing TPR values and were imputed using spatial mean?',
                'type': 'model_comparison'
            },
            'reason': {
                'id': 'impute_reason',
                'text': 'What stood out for you in the model answer chosen?',
                'type': 'text',
                'required': True
            },
            'agreement': {
                'id': 'impute_agree',
                'text': 'Does your understanding of imputed TPR via spatial mean align with the tool\'s approach to imputation?',
                'type': 'scale',
                'min': 1,
                'max': 5,
                'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
            },
            'missing': {
                'id': 'impute_missing',
                'text': "What's missing/needs refinement?",
                'type': 'textarea',
                'required': False
            },
            'confidence': {
                'id': 'impute_conf',
                'text': 'How confident are you explaining imputation flags to colleagues?',
                'type': 'scale',
                'min': 0,
                'max': 100
            },
            'teachback': {
                'id': 'impute_teach',
                'text': 'In your own words, explain how imputed TPR should influence decisions and communication.',
                'type': 'textarea',
                'required': True
            },
            'quiz': {
                'id': 'impute_quiz',
                'text': 'For wards with spatial-mean imputed TPR, you should...',
                'type': 'radio',
                'options': [
                    'Treat estimates cautiously; flag for monitoring/validation',  # Correct
                    'Treat them as high-certainty values',
                    'Convert them to zero',
                    'Exclude the wards from all analysis by default'
                ],
                'correct': 0
            }
        },

        # Visualization Questions
        'tpr_visualization': {
            'model_selection': {
                'id': 'viz_model',
                'text': 'Using the TPR distribution map, identify one ward in the highest quartile and one in the lowest quartile. Describe the spatial pattern you notice.',
                'type': 'model_comparison'
            },
            'reason': {
                'id': 'viz_reason',
                'text': 'What stood out in the answer you chose?',
                'type': 'text',
                'required': True
            },
            'agreement': {
                'id': 'viz_agree',
                'text': 'Does your understanding of the TPR map match what the tool explains?',
                'type': 'scale',
                'min': 1,
                'max': 5,
                'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
            },
            'missing': {
                'id': 'viz_missing',
                'text': "What's missing/needs refinement?",
                'type': 'textarea',
                'required': False
            },
            'confidence': {
                'id': 'viz_conf',
                'text': 'How confident are you interpreting and/or describing the TPR map?',
                'type': 'scale',
                'min': 0,
                'max': 100
            },
            'teachback': {
                'id': 'viz_teach',
                'text': 'In your own words, how should the TPR distribution map be interpreted and used?',
                'type': 'textarea',
                'required': True
            },
            'quiz': {
                'id': 'viz_quiz',
                'text': 'A deep-red ward on the TPR map most likely indicates...',
                'type': 'radio',
                'options': [
                    'A high fraction of positive tests among those tested in that ward',  # Correct
                    'High population',
                    'High certainty',
                    'High EVI'
                ],
                'correct': 0
            }
        },

        # Normalization Questions
        'normalization': {
            'model_selection': {
                'id': 'norm_model',
                'text': 'Which of the two variables (EVI vs distance to water bodies) will drive the composite score after normalization? Why do you think normalization is important?',
                'type': 'model_comparison'
            },
            'reason': {
                'id': 'norm_reason',
                'text': 'What stood out in the answer you chose?',
                'type': 'text',
                'required': True
            },
            'agreement': {
                'id': 'norm_agree',
                'text': 'Does your understanding of EVI vs normalized EVI match the tool\'s narrative?',
                'type': 'scale',
                'min': 1,
                'max': 5,
                'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
            },
            'refine': {
                'id': 'norm_refine',
                'text': 'What would you refine?',
                'type': 'textarea',
                'required': False
            },
            'confidence': {
                'id': 'norm_conf',
                'text': 'How confident are you in explaining the purpose of normalization to your colleagues?',
                'type': 'scale',
                'min': 0,
                'max': 100
            },
            'teachback': {
                'id': 'norm_teach',
                'text': 'Paraphrase what normalization does and how it affects cross variable comparison.',
                'type': 'textarea',
                'required': True
            },
            'quiz': {
                'id': 'norm_quiz',
                'text': 'Normalization mainly...',
                'type': 'radio',
                'options': [
                    'Puts indicators on a common scale so they can be compared and combined',  # Correct
                    'Removes outliers automatically',
                    'Creates a normal (bell-curve) distribution',
                    'Fixes missing data'
                ],
                'correct': 0
            }
        },

        # ITN Distribution Questions
        'itn_distribution': {
            'model_selection': {
                'id': 'itn_model',
                'text': 'On the ITN distribution view, find one ward that changed status (reprioritized vs prioritized) after changing the urbanicity index. Describe how its planned nets allocation changed.',
                'type': 'model_comparison'
            },
            'reason': {
                'id': 'itn_reason',
                'text': 'What stood out in the answer you chose?',
                'type': 'text',
                'required': True
            },
            'agreement': {
                'id': 'itn_agree',
                'text': 'Does your understanding of status changes and ITN allocations match the tool\'s logic?',
                'type': 'scale',
                'min': 1,
                'max': 5,
                'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
            },
            'refine': {
                'id': 'itn_refine',
                'text': 'What needs refinement?',
                'type': 'textarea',
                'required': False
            },
            'confidence': {
                'id': 'itn_conf',
                'text': 'Confidence explaining how reprioritization affects net counts?',
                'type': 'scale',
                'min': 0,
                'max': 100
            },
            'teachback': {
                'id': 'itn_teach',
                'text': 'In your words, how do priority state changes translate into ITN planning?',
                'type': 'textarea',
                'required': True
            },
            'quiz': {
                'id': 'itn_quiz',
                'text': 'If Ward X shifts from prioritized to reprioritized (scale down), the ITN plan should...',
                'type': 'radio',
                'options': [
                    'Decrease planned nets while applying equity safeguards (e.g., protect slum pockets)',  # Correct
                    'Remove all nets entirely',
                    'Auto-raise to 100% coverage',
                    'Only change uncertainty'
                ],
                'correct': 0
            }
        }
    }

    @classmethod
    def get_questions_for_trigger(cls, trigger_type: str, context: Dict[str, Any] = None) -> List[Dict]:
        """Get relevant questions based on trigger type and context."""
        questions = []

        # Map trigger types to question categories
        trigger_mapping = {
            'arena_comparison': ['urban_microstratification', 'ward_heterogeneity', 'risk_score'],
            'risk_analysis_complete': ['risk_score', 'high_risk_areas', 'tpr_risk_relationship'],
            'itn_distribution_generated': ['reprioritization', 'itn_distribution'],
            'tpr_analysis_complete': ['tpr_calculation', 'tpr_environmental', 'tpr_imputation', 'tpr_visualization'],
            'visualization_generated': ['tpr_visualization', 'normalization'],
            'general_assessment': ['urban_microstratification', 'risk_score', 'reprioritization']
        }

        # Get question categories for this trigger
        categories = trigger_mapping.get(trigger_type, ['general_assessment'])

        # Build question list
        for category in categories:
            if category in cls.QUESTIONS:
                category_questions = cls.QUESTIONS[category]
                for q_type, question in category_questions.items():
                    # Clone question to avoid modifying original
                    q = question.copy()
                    q['category'] = category
                    q['question_type'] = q_type

                    # Add context if provided
                    if context:
                        q['context'] = context

                    questions.append(q)

        return questions

    @classmethod
    def get_question_by_id(cls, question_id: str) -> Dict:
        """Get a specific question by its ID."""
        for category, questions in cls.QUESTIONS.items():
            for q_type, question in questions.items():
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
                value = float(response) if '.' in str(response) else int(response)
                return question['min'] <= value <= question['max']
            except (ValueError, TypeError):
                return False

        if question['type'] == 'model_comparison':
            # Model comparison requires special handling
            return response in ['Model A', 'Model B', 'Model C'] or response in context.get('models', [])

        return True

    @classmethod
    def check_quiz_answer(cls, question_id: str, response: Any) -> bool:
        """Check if a quiz answer is correct."""
        question = cls.get_question_by_id(question_id)

        if not question or question.get('type') != 'radio':
            return False

        correct_index = question.get('correct')
        if correct_index is not None:
            options = question.get('options', [])
            if 0 <= correct_index < len(options):
                return response == options[correct_index]

        return False