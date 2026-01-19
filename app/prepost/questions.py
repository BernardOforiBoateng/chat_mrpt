"""
Pre-Post Test Questions Configuration

Defines the question structure for both background information and concept assessment.
Based on: "A Mixed-Methods Evaluation of chatMRPT: an AI-Enhanced Copilot for
Malaria Reprioritization in Urban Nigeria"
"""

from typing import Dict, List, Any, Optional


class PrePostQuestions:
    """Manages questions for pre-post test survey."""

    # Background Information Questions (Pre-Test Only - No Timer)
    # NOTE: Phone number is collected at welcome screen, not as a question
    BACKGROUND_QUESTIONS = [
        # Subsection Header: Background information
        {
            'id': 'bg_header_demographics',
            'text': 'Background information',
            'type': 'section_header',
            'required': False,
            'section': 'background'
        },
        {
            'id': 'bg_age',
            'text': 'What is your age?',
            'type': 'radio',
            'required': True,
            'section': 'background',
            'subsection': 'Background information',
            'options': [
                '18 – 24',
                '25 – 34',
                '35 – 44',
                '45 – 54',
                '55+'
            ]
        },
        {
            'id': 'bg_education_level',
            'text': 'What is the highest level of education you have completed?',
            'type': 'radio',
            'required': True,
            'section': 'background',
            'options': [
                'Primary education',
                'Secondary education',
                'Diploma',
                'Certificate',
                "Bachelor's degree",
                "Master's degree",
                'Doctorate (PhD/DrPH/MD)',
                'Other'
            ]
        },
        {
            'id': 'bg_education_years',
            'text': 'How many total years of formal education have you completed?',
            'type': 'number',
            'required': True,
            'section': 'background',
            'min': 0,
            'max': 50
        },
        {
            'id': 'bg_years_current_role',
            'text': 'How many years have you worked in your current role?',
            'type': 'number',
            'required': True,
            'section': 'background',
            'min': 0,
            'max': 50
        },
        {
            'id': 'bg_years_malaria_public_health',
            'text': 'How many total years have you worked in malaria control or public health?',
            'type': 'number',
            'required': True,
            'section': 'background',
            'min': 0,
            'max': 50
        },
        {
            'id': 'bg_job_title',
            'text': 'What is your current job title/position?',
            'type': 'text',
            'required': True,
            'section': 'background'
        },
        {
            'id': 'bg_work_level',
            'text': 'At which level do you primarily work?',
            'type': 'text',
            'required': True,
            'section': 'background'
        },
        {
            'id': 'bg_used_digital_tools',
            'text': 'Have you previously used digital decision-support tools (e.g., GIS platforms, dashboards, or AI tools)?',
            'type': 'radio',
            'required': True,
            'section': 'background',
            'options': ['Yes', 'No']
        },
        {
            'id': 'bg_digital_tools_specify',
            'text': 'If yes, please specify which tools:',
            'type': 'textarea',
            'required': False,
            'section': 'background'
        },
        {
            'id': 'bg_learning_format',
            'text': 'What type of training/learning format do you learn best from? (Select all that apply)',
            'type': 'checkbox',
            'required': True,
            'section': 'background',
            'options': [
                'Hands on workshop',
                'Demonstration',
                'Self-paced manuals',
                'Videos',
                'Peer to peer learning',
                'Other'
            ]
        },

        # Subsection Header: Technical and digital literacy
        {
            'id': 'bg_header_technical',
            'text': 'Technical and digital literacy',
            'type': 'section_header',
            'required': False,
            'section': 'background'
        },
        {
            'id': 'bg_computer_skills',
            'text': 'How would you rate your computer skills?',
            'type': 'radio',
            'required': True,
            'section': 'background',
            'options': ['Beginner', 'Intermediate', 'Advanced']
        },
        {
            'id': 'bg_data_work_frequency',
            'text': 'How often do you work with data in your role (e.g., analysis, interpretation, reporting)?',
            'type': 'radio',
            'required': True,
            'section': 'background',
            'options': ['Rarely', 'Sometimes', 'Often', 'Very often']
        },
        {
            'id': 'bg_resource_access',
            'text': 'Do you have regular access to the following resources while at work? (Select all that apply)',
            'type': 'checkbox',
            'required': True,
            'section': 'background',
            'options': [
                'Laptop or desktop',
                'Smartphone or tablet',
                'Stable internet',
                'Stable electricity'
            ]
        },

        # Subsection Header: Decision making and planning
        {
            'id': 'bg_header_decision_making',
            'text': 'Decision making and planning',
            'type': 'section_header',
            'required': False,
            'section': 'background'
        },
        {
            'id': 'bg_itn_involvement_frequency',
            'text': 'How frequently are you directly involved in ITN campaign planning or microstratification activities?',
            'type': 'radio',
            'required': True,
            'section': 'background',
            'options': ['Rarely', 'Sometimes', 'Often', 'Very often']
        },
        {
            'id': 'bg_planning_role',
            'text': 'What role do you usually play in planning processes?',
            'type': 'radio',
            'required': True,
            'section': 'background',
            'options': [
                'Data analysis',
                'Conceptualization',
                'Data visualization',
                'Microplanning field implementation or logistics',
                'Supervisor or managerial',
                'Policy or strategy development',
                'Other'
            ]
        }
    ]

    # Concept Assessment Questions (Both Pre-Test and Post-Test - With Timer)
    CONCEPT_QUESTIONS = [
        # Subsection Header: Concept assessment
        {
            'id': 'concept_header',
            'text': 'Concept assessment',
            'instruction': 'Please note that these questions are intended to help us evaluate the tool\'s usability and usefulness in practice. They are not meant to measure your skills or performance.',
            'type': 'section_header',
            'required': False,
            'section': 'concepts'
        },
        # Question 1: Disease distribution
        {
            'id': 'concept_disease_distribution',
            'text': 'Disease distribution in urban areas is mostly _____ concentrating in _____.',
            'instruction': 'Pick the correct answer',
            'type': 'radio',
            'required': True,
            'section': 'concepts',
            'topic': 'Disease Distribution',
            'options': [
                'Uniform; in peri-urban and informal settlements',
                'Focal; in peri-urban and informal settlements',
                'Exponential; in central business districts',
                'Widespread; equally across all neighbourhoods'
            ],
            'correct_index': 1  # Focal; in peri-urban and informal settlements
        },
        {
            'id': 'concept_disease_distribution_implications',
            'text': 'What are the implications of your response for the choice of surveillance strategy and intervention distribution?',
            'type': 'textarea',
            'required': True,
            'section': 'concepts',
            'topic': 'Disease Distribution',
            'parent_question': 'concept_disease_distribution'
        },

        # Question 2: Infections in urban vs rural
        {
            'id': 'concept_infections_urban_rural',
            'text': 'Infections in urban areas are often linked to ______ and can be _____, while most in rural areas are ______.',
            'type': 'radio',
            'required': True,
            'section': 'concepts',
            'topic': 'Urban vs Rural Infections',
            'options': [
                'Travel; locally acquired; locally acquired',
                'Travel; imported only; locally acquired',
                'Local farming; imported; imported',
                'Housing quality; eliminated; imported'
            ],
            'correct_index': 0  # Travel; locally acquired; locally acquired
        },
        {
            'id': 'concept_infections_implications',
            'text': 'What are the implications of your response for the timing of your surveillance strategy and intervention distribution?',
            'type': 'textarea',
            'required': True,
            'section': 'concepts',
            'topic': 'Urban vs Rural Infections',
            'parent_question': 'concept_infections_urban_rural'
        },

        # Question 3: Housing types and mosquito biting
        {
            'id': 'concept_housing_biting',
            'text': 'Many housing types in urban areas reduce ______ biting.',
            'type': 'radio',
            'required': True,
            'section': 'concepts',
            'topic': 'Housing and Mosquito Biting',
            'options': [
                'Outdoor',
                'Daytime',
                'Indoor',
                'Peri-urban'
            ],
            'correct_index': 2  # Indoor
        },
        {
            'id': 'concept_housing_implications',
            'text': 'What are the implications of your response for intervention reprioritization?',
            'type': 'textarea',
            'required': True,
            'section': 'concepts',
            'topic': 'Housing and Mosquito Biting',
            'parent_question': 'concept_housing_biting'
        },

        # Question 4: TPR shortcomings
        {
            'id': 'concept_tpr_shortcomings',
            'text': 'What are the shortcomings of test positivity rate (TPR) data from DHIS2? (Choose all that apply)',
            'type': 'checkbox',
            'required': True,
            'section': 'concepts',
            'topic': 'TPR Data Quality',
            'options': [
                'They reflect testing practices',
                'They are based on RDT testing, which does not perform well in low-transmission areas',
                'Issues with completeness of reporting',
                'Lack of age breakdown (not granular)'
            ],
            'correct_indices': [0, 1, 2, 3]  # All are correct
        },
        {
            'id': 'concept_tpr_decision_making',
            'text': 'Given these shortcomings, can we use the TPR data to make conclusive decisions specifically intervention reprioritization?',
            'type': 'textarea',
            'required': True,
            'section': 'concepts',
            'topic': 'TPR Data Quality',
            'parent_question': 'concept_tpr_shortcomings'
        },

        # Question 5: Data sources for malaria transmission
        {
            'id': 'concept_data_sources',
            'text': 'What are potential data sources that can be used to understand malaria transmission? (Check all that apply)',
            'type': 'checkbox',
            'required': True,
            'section': 'concepts',
            'topic': 'Data Sources',
            'options': [
                'Satellite imagery',
                'DHIS2',
                'National Electricity Commission',
                'Demographic Health Surveys'
            ],
            'correct_indices': [0, 1, 3]  # Satellite, DHIS2, DHS
        },
        {
            'id': 'concept_satellite_variables',
            'text': 'Explain the types or variables we can extract from satellite imagery',
            'type': 'textarea',
            'required': True,
            'section': 'concepts',
            'topic': 'Data Sources',
            'parent_question': 'concept_data_sources'
        },

        # Question 6: Vulnerability map interpretation
        {
            'id': 'concept_vulnerability_map',
            'text': 'Which ward has the (i) lowest and (ii) highest vulnerability?',
            'instruction': 'You must view the vulnerability map before answering',
            'type': 'textarea',
            'required': True,
            'section': 'concepts',
            'topic': 'Vulnerability Map Interpretation',
            'has_map_link': True,
            # Serve via prepost-safe route (no auth, static content)
            'map_link': '/prepost/map/vulnerability'
        },
        {
            'id': 'concept_top_wards_reprioritization',
            'text': 'Based on the vulnerability map, name the top 5 wards for reprioritization',
            'type': 'textarea',
            'required': True,
            'section': 'concepts',
            'topic': 'Vulnerability Map Interpretation',
            'parent_question': 'concept_vulnerability_map'
        },

        # Question 7: Micro plan definition
        {
            'id': 'concept_micro_plan_definition',
            'text': 'In the context of intervention distribution/delivery how would you define a Micro plan?',
            'type': 'textarea',
            'required': True,
            'section': 'concepts',
            'topic': 'Micro Planning'
        },

        # Question 8: Micro plan process
        {
            'id': 'concept_micro_plan_process',
            'text': 'What is the process of creating a micro plan?',
            'type': 'textarea',
            'required': True,
            'section': 'concepts',
            'topic': 'Micro Planning'
        }
    ]

    # Usability Assessment Questions (Post-Test Only)
    USABILITY_QUESTIONS = [
        # Section Header
        {
            'id': 'usability_header',
            'text': 'System Usability Assessment',
            'instruction': 'Now that you have used ChatMRPT, please help us understand your experience with the system. Rate your agreement with each statement on a scale from 1 (Strongly disagree) to 5 (Strongly agree).',
            'type': 'section_header',
            'required': False,
            'section': 'usability'
        },

        # Subsection: Understanding and Interaction
        {
            'id': 'usability_subsection_understanding',
            'text': 'Understanding and Interaction',
            'type': 'section_header',
            'required': False,
            'section': 'usability'
        },
        {
            'id': 'usability_system_understood_me',
            'text': 'ChatMRPT understood what I was asking',
            'type': 'scale',
            'required': True,
            'section': 'usability',
            'subsection': 'Understanding and Interaction',
            'min': 1,
            'max': 5,
            'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
        },
        {
            'id': 'usability_i_understood_system',
            'text': 'I understood ChatMRPT\'s responses',
            'type': 'scale',
            'required': True,
            'section': 'usability',
            'subsection': 'Understanding and Interaction',
            'min': 1,
            'max': 5,
            'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
        },
        {
            'id': 'usability_learned_about_malaria',
            'text': 'I learned more about urban malaria risk analysis through ChatMRPT',
            'type': 'scale',
            'required': True,
            'section': 'usability',
            'subsection': 'Understanding and Interaction',
            'min': 1,
            'max': 5,
            'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
        },

        # Subsection: Ease of Use
        {
            'id': 'usability_subsection_ease',
            'text': 'Ease of Use',
            'type': 'section_header',
            'required': False,
            'section': 'usability'
        },
        {
            'id': 'usability_learned_quickly',
            'text': 'I learned to use ChatMRPT quickly',
            'type': 'scale',
            'required': True,
            'section': 'usability',
            'subsection': 'Ease of Use',
            'min': 1,
            'max': 5,
            'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
        },

        # Subsection: Recommendation and Engagement
        {
            'id': 'usability_subsection_recommendation',
            'text': 'Recommendation and Engagement',
            'type': 'section_header',
            'required': False,
            'section': 'usability'
        },
        {
            'id': 'usability_recommend_colleague',
            'text': 'I would recommend ChatMRPT to a colleague',
            'type': 'scale',
            'required': True,
            'section': 'usability',
            'subsection': 'Recommendation and Engagement',
            'min': 1,
            'max': 5,
            'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
        },
        {
            'id': 'usability_use_frequently',
            'text': 'I would like to use ChatMRPT frequently in my work',
            'type': 'scale',
            'required': True,
            'section': 'usability',
            'subsection': 'Recommendation and Engagement',
            'min': 1,
            'max': 5,
            'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
        },

        # Subsection: System Complexity and Support
        {
            'id': 'usability_subsection_complexity',
            'text': 'System Complexity and Support',
            'type': 'section_header',
            'required': False,
            'section': 'usability'
        },
        {
            'id': 'usability_unnecessarily_complex',
            'text': 'I found ChatMRPT unnecessarily complex',
            'type': 'scale',
            'required': True,
            'section': 'usability',
            'subsection': 'System Complexity and Support',
            'min': 1,
            'max': 5,
            'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree'],
            'reverse_scored': True  # Negative question
        },
        {
            'id': 'usability_cumbersome',
            'text': 'I found ChatMRPT cumbersome to use',
            'type': 'scale',
            'required': True,
            'section': 'usability',
            'subsection': 'System Complexity and Support',
            'min': 1,
            'max': 5,
            'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree'],
            'reverse_scored': True  # Negative question
        },

        # Subsection: Confidence and Learning Curve
        {
            'id': 'usability_subsection_confidence',
            'text': 'Confidence and Learning Curve',
            'type': 'section_header',
            'required': False,
            'section': 'usability'
        },
        {
            'id': 'usability_felt_confident',
            'text': 'I felt confident using ChatMRPT',
            'type': 'scale',
            'required': True,
            'section': 'usability',
            'subsection': 'Confidence and Learning Curve',
            'min': 1,
            'max': 5,
            'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
        },
        {
            'id': 'usability_learning_requirements',
            'text': 'I needed to learn many things before I could use ChatMRPT effectively',
            'type': 'scale',
            'required': True,
            'section': 'usability',
            'subsection': 'Confidence and Learning Curve',
            'min': 1,
            'max': 5,
            'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree'],
            'reverse_scored': True  # Negative question
        },

        # Subsection: Open Feedback
        {
            'id': 'usability_subsection_feedback',
            'text': 'Open Feedback',
            'type': 'section_header',
            'required': False,
            'section': 'usability'
        },
        {
            'id': 'usability_general_thoughts',
            'text': 'Please share your thoughts about ChatMRPT. What did you like? What could be improved?',
            'type': 'textarea',
            'required': False,
            'section': 'usability',
            'subsection': 'Open Feedback',
            'placeholder': 'Your feedback helps us improve ChatMRPT for future users...'
        },
        {
            'id': 'usability_response_clarity',
            'text': 'What did you think of ChatMRPT\'s responses? Were they clear and helpful, or confusing?',
            'type': 'textarea',
            'required': False,
            'section': 'usability',
            'subsection': 'Open Feedback',
            'placeholder': 'Please describe your experience with the clarity of ChatMRPT\'s responses...'
        }
    ]

    @classmethod
    def get_background_questions(cls) -> List[Dict[str, Any]]:
        """Return background questions (pre-test only)."""
        return cls.BACKGROUND_QUESTIONS.copy()

    @classmethod
    def get_concept_questions(cls) -> List[Dict[str, Any]]:
        """Return concept assessment questions (both pre and post test)."""
        return cls.CONCEPT_QUESTIONS.copy()

    @classmethod
    def get_pre_test_questions(cls) -> List[Dict[str, Any]]:
        """Return all questions for pre-test (background + concepts)."""
        return cls.BACKGROUND_QUESTIONS + cls.CONCEPT_QUESTIONS

    @classmethod
    def get_post_test_questions(cls) -> List[Dict[str, Any]]:
        """Return questions for post-test (concepts + usability, no background)."""
        return cls.CONCEPT_QUESTIONS + cls.USABILITY_QUESTIONS

    @classmethod
    def get_question_by_id(cls, question_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific question by its ID."""
        all_questions = cls.BACKGROUND_QUESTIONS + cls.CONCEPT_QUESTIONS + cls.USABILITY_QUESTIONS
        for question in all_questions:
            if question['id'] == question_id:
                return question
        return None

    @classmethod
    def validate_response(cls, question_id: str, response: Any) -> bool:
        """
        Validate a response based on question type.

        Args:
            question_id: Question identifier
            response: User's response

        Returns:
            bool: True if response is valid
        """
        question = cls.get_question_by_id(question_id)

        if not question:
            return False

        question_type = question.get('type')

        # Validate based on question type
        if question_type == 'text':
            return isinstance(response, str) and len(response.strip()) > 0

        elif question_type == 'textarea':
            return isinstance(response, str) and len(response.strip()) > 0

        elif question_type == 'number':
            try:
                value = int(response)
                min_val = question.get('min', 0)
                max_val = question.get('max', 100)
                return min_val <= value <= max_val
            except (ValueError, TypeError):
                return False

        elif question_type == 'scale':
            try:
                value = int(response)
                min_val = question.get('min', 1)
                max_val = question.get('max', 5)
                return min_val <= value <= max_val
            except (ValueError, TypeError):
                return False

        elif question_type == 'radio':
            # Check if response is a valid option
            options = question.get('options', [])
            if isinstance(response, int):
                return 0 <= response < len(options)
            elif isinstance(response, str):
                return response in options
            return False

        elif question_type == 'checkbox':
            # Response should be a list of selected indices or option strings
            options = question.get('options', [])
            if isinstance(response, list):
                for item in response:
                    if isinstance(item, int):
                        if not (0 <= item < len(options)):
                            return False
                    elif isinstance(item, str):
                        if item not in options:
                            return False
                    else:
                        return False
                return True
            return False

        # Default - accept any non-null response
        return response is not None

    @classmethod
    def get_total_questions(cls, test_type: str = 'pre') -> int:
        """Get total number of questions for a test type."""
        if test_type == 'pre':
            return len(cls.BACKGROUND_QUESTIONS) + len(cls.CONCEPT_QUESTIONS)
        else:  # post
            return len(cls.CONCEPT_QUESTIONS) + len(cls.USABILITY_QUESTIONS)

    @classmethod
    def calculate_score(cls, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate test score from responses.

        Args:
            responses: List of response dictionaries with question_id and response

        Returns:
            Dictionary with score metrics
        """
        concept_responses = [r for r in responses if r.get('section') == 'concepts']

        # Count gradable questions (radio/checkbox with correct answers)
        gradable_questions = [q for q in cls.CONCEPT_QUESTIONS
                            if 'correct_index' in q or 'correct_indices' in q]

        total_gradable = len(gradable_questions)
        correct_answers = 0

        for response in concept_responses:
            question = cls.get_question_by_id(response['question_id'])
            if not question:
                continue

            user_answer = response.get('response')

            # Check radio questions
            if 'correct_index' in question:
                if isinstance(user_answer, int):
                    if user_answer == question['correct_index']:
                        correct_answers += 1
                elif isinstance(user_answer, str):
                    options = question.get('options', [])
                    if user_answer in options:
                        user_index = options.index(user_answer)
                        if user_index == question['correct_index']:
                            correct_answers += 1

            # Check checkbox questions
            elif 'correct_indices' in question:
                if isinstance(user_answer, list):
                    correct_set = set(question['correct_indices'])
                    user_set = set(user_answer) if all(isinstance(x, int) for x in user_answer) else set()
                    if user_set == correct_set:
                        correct_answers += 1

        return {
            'total_questions': len(cls.CONCEPT_QUESTIONS),
            'gradable_questions': total_gradable,
            'answered_questions': len(concept_responses),
            'correct_answers': correct_answers,
            'score_percentage': (correct_answers / total_gradable * 100) if total_gradable > 0 else 0
        }
