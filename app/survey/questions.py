"""
Survey Questions Configuration - Appendix 5 Cognitive Assessment

Modified to include ONLY highlighted questions from Pretest schedule.docx:
- Section 1: General Knowledge of Malaria (2 topics: Urban Microstratification, Reprioritization)
- Section 2: TPR Analysis (1 topic: TPR Calculation)
- Section 3: Visualization (2 topics: EVI/Water Bodies Normalization, Vulnerability Map)
Total: 5 topics (9 topics commented out as non-highlighted)
"""

from typing import Dict, List, Any
import random


class SurveyQuestions:
    """Manages survey questions based on Appendix 5 of the ChatMRPT protocol."""

    # Question bank organized by sections from Appendix 5
    SECTIONS = {
        'general_knowledge': {
            'title': 'General Knowledge of Malaria',
            'topics': {
                # Topic 1: Urban Microstratification
                'urban_microstratification': {
                    'title': 'Urban Microstratification',
                    'questions': {
                        'model_selection': {
                            'id': 'gk1_model',
                            'text': 'What is urban microstratification?',
                            'type': 'model_comparison',
                            'instruction': 'Choose your preferred answer (shows two at a time)'
                        },
                        'reason': {
                            'id': 'gk1_reason',
                            'text': 'What stood out for you in the answer you chose?',
                            'type': 'text',
                            'required': True
                        },
                        'agreement': {
                            'id': 'gk1_agree',
                            'text': 'Does your understanding of urban microstratification match what the tool says?',
                            'type': 'scale',
                            'min': 1,
                            'max': 5,
                            'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
                        },
                        'missing': {
                            'id': 'gk1_missing',
                            'text': 'What aspect of the definition is missing/needs refinements based on your understanding?',
                            'type': 'textarea',
                            'required': False,
                            'placeholder': 'Free-text (1-2 sentences)'
                        },
                        'confidence': {
                            'id': 'gk1_conf',
                            'text': 'How confident are you to explain this to your colleagues?',
                            'type': 'scale',
                            'min': 0,
                            'max': 100,
                            'labels': ['Not confident', 'Very confident']
                        },
                        'teachback': {
                            'id': 'gk1_teach',
                            'text': 'In your own words can you paraphrase the answer the model provided?',
                            'type': 'textarea',
                            'required': True
                        },
                        'quiz': {
                            'id': 'gk1_quiz',
                            'text': 'Microstratification is primarily used to...',
                            'type': 'radio',
                            'options': [
                                'identify within-city risk differences',  # Correct
                                'measure ward population only',
                                'map certainty only'
                            ],
                            'correct': 0
                        }
                    }
                },

                # Topic 2: Within Ward Heterogeneity - COMMENTED OUT (Not highlighted in Pretest schedule.docx)
                # 'ward_heterogeneity': {
                #     'title': 'Within Ward Heterogeneity',
                #     'questions': {
                #         'model_selection': {
                #             'id': 'gk2_model',
                #             'text': 'What is within ward heterogeneity (variation) in the context of urban area settlements?',
                #             'type': 'model_comparison',
                #             'instruction': 'Choose your preferred answer (shows two at a time)'
                #         },
                #         'reason': {
                #             'id': 'gk2_reason',
                #             'text': 'What stood out for you in the answer you chose?',
                #             'type': 'text',
                #             'required': True
                #         },
                #         'agreement': {
                #             'id': 'gk2_agree',
                #             'text': 'Does your understanding of within ward heterogeneity match what the tool says?',
                #             'type': 'scale',
                #             'min': 1,
                #             'max': 5,
                #             'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
                #         },
                #         'missing': {
                #             'id': 'gk2_missing',
                #             'text': 'What aspect of the narrative is missing/needs refinements based on your understanding?',
                #             'type': 'textarea',
                #             'required': False,
                #             'placeholder': 'Free-text (1-2 sentences)'
                #         },
                #         'confidence': {
                #             'id': 'gk2_conf',
                #             'text': 'How confident are you to explain within ward to your colleagues?',
                #             'type': 'scale',
                #             'min': 0,
                #             'max': 100,
                #             'labels': ['Not confident', 'Very confident']
                #         },
                #         'teachback': {
                #             'id': 'gk2_teach',
                #             'text': 'In your own words, what is within-ward heterogeneity in urban areas, and why does it matter for planning?',
                #             'type': 'textarea',
                #             'required': True
                #         },
                #         'quiz': {
                #             'id': 'gk2_quiz',
                #             'text': 'Within ward heterogeneity refers to...',
                #             'type': 'radio',
                #             'options': [
                #                 'variation in risk, population, and context within neighborhoods of the same ward',  # Correct
                #                 'differences between cities',
                #                 'random measurement error only',
                #                 'total population differences across wards'
                #             ],
                #             'correct': 0
                #         }
                #     }
                # },

                # Topic 3: Malaria Risk Score - COMMENTED OUT (Not highlighted in Pretest schedule.docx)
                # 'risk_score': {
                #     'title': 'Malaria Risk Score',
                #     'questions': {
                #         'model_selection': {
                #             'id': 'gk3_model',
                #             'text': 'Define malaria risk score and name two indicators that you could use to create a risk score.',
                #             'type': 'model_comparison',
                #             'instruction': 'Choose your preferred answer (shows two at a time)'
                #         },
                #         'reason': {
                #             'id': 'gk3_reason',
                #             'text': 'What stood out for you in the answer you chose?',
                #             'type': 'text',
                #             'required': True
                #         },
                #         'agreement': {
                #             'id': 'gk3_agree',
                #             'text': 'Does your understanding of malaria risk score match what the tool says?',
                #             'type': 'scale',
                #             'min': 1,
                #             'max': 5,
                #             'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
                #         },
                #         'missing': {
                #             'id': 'gk3_missing',
                #             'text': 'What aspect of the narrative is missing/needs refinements based on your understanding?',
                #             'type': 'textarea',
                #             'required': False,
                #             'placeholder': 'Free-text (1-2 sentences)'
                #         },
                #         'confidence': {
                #             'id': 'gk3_conf',
                #             'text': "How confident are you to explain ChatMRPT's malaria risk score to your colleagues?",
                #             'type': 'scale',
                #             'min': 0,
                #             'max': 100,
                #             'labels': ['Not confident', 'Very confident']
                #         },
                #         'teachback': {
                #             'id': 'gk3_teach',
                #             'text': 'In your own words, what is malaria risk score in urban areas, and why does it matter for planning?',
                #             'type': 'textarea',
                #             'required': True
                #         },
                #         'quiz': {
                #             'id': 'gk3_quiz',
                #             'text': 'A malaria risk score is...',
                #             'type': 'radio',
                #             'options': [
                #                 'a composite of normalized indicators for a ward',  # Correct
                #                 'just the raw TPR percentage',
                #                 "the ward's population size",
                #                 'a measure of model certainty'
                #             ],
                #             'correct': 0
                #         }
                #     }
                # },

                # Topic 4: Reprioritization
                'reprioritization': {
                    'title': 'Reprioritization',
                    'questions': {
                        'model_selection': {
                            'id': 'gk4_model',
                            'text': 'What is reprioritization?',
                            'type': 'model_comparison',
                            'instruction': 'Choose your preferred answer (shows two at a time)'
                        },
                        'reason': {
                            'id': 'gk4_reason',
                            'text': 'What stood out for you in the answer you chose?',
                            'type': 'text',
                            'required': True
                        },
                        'agreement': {
                            'id': 'gk4_agree',
                            'text': 'Does your understanding of reprioritization match what the tool says?',
                            'type': 'scale',
                            'min': 1,
                            'max': 5,
                            'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
                        },
                        'missing': {
                            'id': 'gk4_missing',
                            'text': 'What aspect of the narrative is missing/needs refinements based on your understanding?',
                            'type': 'textarea',
                            'required': False,
                            'placeholder': 'Free-text (1-2 sentences)'
                        },
                        'confidence': {
                            'id': 'gk4_conf',
                            'text': 'How confident are you to explain reprioritization to your colleagues?',
                            'type': 'scale',
                            'min': 0,
                            'max': 100,
                            'labels': ['Not confident', 'Very confident']
                        },
                        'teachback': {
                            'id': 'gk4_teach',
                            'text': 'In your own words, what is reprioritization in urban areas, and why does it matter for planning?',
                            'type': 'textarea',
                            'required': True
                        },
                        'quiz': {
                            'id': 'gk4_quiz',
                            'text': 'Reprioritization mainly means...',
                            'type': 'radio',
                            'options': [
                                'strategically scale down the distribution of bed nets for flagged areas',  # Correct
                                'expanding bed net distribution to all areas equally, regardless of malaria risk',
                                'stopping the distribution of bed nets entirely in all states',
                                'increasing bed net distribution in areas already marked as low risk'
                            ],
                            'correct': 0
                        }
                    }
                },

                # Topic 5: High-Risk Areas Characteristics - COMMENTED OUT (Not highlighted in Pretest schedule.docx)
                # 'high_risk_areas': {
                #     'title': 'High-Risk Areas Characteristics',
                #     'questions': {
                #         'model_selection': {
                #             'id': 'gk5_model',
                #             'text': 'What are the characteristics of high-risk areas/wards in your state and why does it matter for planning?',
                #             'type': 'model_comparison',
                #             'instruction': 'Choose your preferred answer (shows two at a time)'
                #         },
                #         'reason': {
                #             'id': 'gk5_reason',
                #             'text': 'What stood out for you in the answer you chose?',
                #             'type': 'text',
                #             'required': True
                #         },
                #         'agreement': {
                #             'id': 'gk5_agree',
                #             'text': 'Does your understanding of high-risk areas in wards match what the tool says?',
                #             'type': 'scale',
                #             'min': 1,
                #             'max': 5,
                #             'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
                #         },
                #         'missing': {
                #             'id': 'gk5_missing',
                #             'text': 'What aspect of the narrative is missing/needs refinements based on your understanding?',
                #             'type': 'textarea',
                #             'required': False,
                #             'placeholder': 'Free-text (1-2 sentences)'
                #         },
                #         'confidence': {
                #             'id': 'gk5_conf',
                #             'text': 'How confident are you to explain the characteristics of high-risk areas within wards to your colleagues?',
                #             'type': 'scale',
                #             'min': 0,
                #             'max': 100,
                #             'labels': ['Not confident', 'Very confident']
                #         },
                #         'teachback': {
                #             'id': 'gk5_teach',
                #             'text': 'In your own words, what are the characteristics of high-risk areas/wards in your state, and why does it matter for planning?',
                #             'type': 'textarea',
                #             'required': True
                #         },
                #         'quiz': {
                #             'id': 'gk5_quiz',
                #             'text': 'Which pattern most often signals higher risk in urban wards?',
                #             'type': 'radio',
                #             'options': [
                #                 'Dense informal housing near poor drainage/stagnant water/poor housing and near vegetation and water bodies',  # Correct
                #                 'High-elevation windy ridge with no standing water',
                #                 'Recently sprayed area with high ITN coverage',
                #                 'Daytime office district with low nighttime residence'
                #             ],
                #             'correct': 0
                #         }
                #     }
                # }
            }
        },

        'tpr_analysis': {
            'title': 'TPR Analysis',
            'topics': {
                # Topic 1: TPR Calculation
                'tpr_calculation': {
                    'title': 'TPR Calculation',
                    'questions': {
                        'model_selection': {
                            'id': 'tpr1_model',
                            'text': 'How do you calculate test positivity rate (TPR) among under-fives in the low-risk ward?',
                            'type': 'model_comparison',
                            'instruction': 'Choose your preferred answer (shows two at a time)'
                        },
                        'reason': {
                            'id': 'tpr1_reason',
                            'text': 'What stood out to you in the answer you chose?',
                            'type': 'text',
                            'required': True
                        },
                        'agreement': {
                            'id': 'tpr1_agree',
                            'text': 'Does your understanding of TPR among under-fives match what the tool reports for the low-risk ward?',
                            'type': 'scale',
                            'min': 1,
                            'max': 5,
                            'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
                        },
                        'missing': {
                            'id': 'tpr1_missing',
                            'text': "What's missing/needs refinement?",
                            'type': 'textarea',
                            'required': False,
                            'placeholder': '1-2 sentences'
                        },
                        'confidence': {
                            'id': 'tpr1_conf',
                            'text': 'How confident are you reporting under-five TPR calculation?',
                            'type': 'scale',
                            'min': 0,
                            'max': 100,
                            'labels': ['Not confident', 'Very confident']
                        },
                        'teachback': {
                            'id': 'tpr1_teach',
                            'text': 'In your own words, define "TPR among under-fives" and how it\'s shown in ChatMRPT.',
                            'type': 'textarea',
                            'required': True
                        },
                        'quiz': {
                            'id': 'tpr1_quiz',
                            'text': '"Under-five TPR" is...',
                            'type': 'radio',
                            'options': [
                                'Total of positive tests <5 / total tested among children <5',  # Correct
                                'positives / total ward population',
                                'incidence per 1,000 under-fives',
                                'a certainty score'
                            ],
                            'correct': 0
                        }
                    }
                },

                # Topic 2: TPR and Environmental Risk - COMMENTED OUT (Not highlighted in Pretest schedule.docx)
                # 'tpr_environmental': {
                #     'title': 'TPR and Environmental Risk',
                #     'questions': {
                #         'model_selection': {
                #             'id': 'tpr2_model',
                #             'text': 'Provide summary statistics of the variables in the data. Are any wards with high TPR and high environmental risk?',
                #             'type': 'model_comparison',
                #             'instruction': 'Choose your preferred answer (shows two at a time)'
                #         },
                #         'reason': {
                #             'id': 'tpr2_reason',
                #             'text': 'What convinced you this answer was best?',
                #             'type': 'text',
                #             'required': True
                #         },
                #         'agreement': {
                #             'id': 'tpr2_agree',
                #             'text': 'Does your understanding of "high-high" (TPR and environmental risk) match the tool\'s definitions and thresholds?',
                #             'type': 'scale',
                #             'min': 1,
                #             'max': 5,
                #             'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
                #         },
                #         'missing': {
                #             'id': 'tpr2_missing',
                #             'text': "What's unclear?",
                #             'type': 'textarea',
                #             'required': False,
                #             'placeholder': '1-2 sentences'
                #         },
                #         'confidence': {
                #             'id': 'tpr2_conf',
                #             'text': 'How confident are you identifying high-risk wards and explaining your choice to a friend?',
                #             'type': 'scale',
                #             'min': 0,
                #             'max': 100,
                #             'labels': ['Not confident', 'Very confident']
                #         },
                #         'teachback': {
                #             'id': 'tpr2_teach',
                #             'text': 'Explain what "high TPR and high environmental risk" implies for prioritization.',
                #             'type': 'textarea',
                #             'required': True
                #         },
                #         'quiz': {
                #             'id': 'tpr2_quiz',
                #             'text': 'If both TPR and environmental risk are high, the ward...',
                #             'type': 'radio',
                #             'options': [
                #                 'likely warrants priority attention (Consistent signals)',  # Correct
                #                 'should be de-prioritized',
                #                 'indicates a data error by default',
                #                 'has low uncertainty'
                #             ],
                #             'correct': 0
                #         }
                #     }
                # },

                # Topic 3: TPR-Risk Relationship - COMMENTED OUT (Not highlighted in Pretest schedule.docx)
                # 'tpr_risk_relationship': {
                #     'title': 'TPR-Risk Index Relationship',
                #     'questions': {
                #         'model_selection': {
                #             'id': 'tpr3_model',
                #             'text': "What's the overall directional relationship between TPR and risk index?",
                #             'type': 'model_comparison',
                #             'instruction': 'Choose your preferred answer (shows two at a time)'
                #         },
                #         'reason': {
                #             'id': 'tpr3_reason',
                #             'text': 'What made this computation/explanation clearest?',
                #             'type': 'text',
                #             'required': True
                #         },
                #         'agreement': {
                #             'id': 'tpr3_agree',
                #             'text': "Does your understanding of directional relationship between TPR and composite score match the tool's?",
                #             'type': 'scale',
                #             'min': 1,
                #             'max': 5,
                #             'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
                #         },
                #         'missing': {
                #             'id': 'tpr3_missing',
                #             'text': 'Why or why do you agree/disagree with this?',
                #             'type': 'textarea',
                #             'required': False,
                #             'placeholder': '1-2 sentences'
                #         },
                #         'confidence': {
                #             'id': 'tpr3_conf',
                #             'text': "How confident are you in discussing the tool's output to this answer to your workmates or collaborators?",
                #             'type': 'scale',
                #             'min': 0,
                #             'max': 100,
                #             'labels': ['Not confident', 'Very confident']
                #         },
                #         'teachback': {
                #             'id': 'tpr3_teach',
                #             'text': "Describe how you'd investigate the directional relationship of TPR with distance to water bodies (add caveats if any).",
                #             'type': 'textarea',
                #             'required': True
                #         },
                #         'quiz': {
                #             'id': 'tpr3_quiz',
                #             'text': 'What is the overall directional relationship between TPR and risk index?',
                #             'type': 'radio',
                #             'options': [
                #                 'There is a positive relationship with higher risk index values generally corresponding to higher TPRs',  # Correct
                #                 'There is a negative relationship with higher risk index values correspond to lower TPRs',
                #                 'There is no relationship TPR and risk index are unrelated',
                #                 'The relationship is completely random and does not follow any directional pattern'
                #             ],
                #             'correct': 0
                #         }
                #     }
                # },

                # Topic 4: Mean TPR and Outliers - COMMENTED OUT (Not highlighted in Pretest schedule.docx)
                # 'mean_tpr': {
                #     'title': 'Mean TPR and Outliers',
                #     'questions': {
                #         'model_selection': {
                #             'id': 'tpr4_model',
                #             'text': 'What is the mean TPR across all wards and what are the outliers if any?',
                #             'type': 'model_comparison',
                #             'instruction': 'Choose your preferred answer (shows two at a time)'
                #         },
                #         'reason': {
                #             'id': 'tpr4_reason',
                #             'text': 'What made this computation/explanation clearest?',
                #             'type': 'text',
                #             'required': True
                #         },
                #         'agreement': {
                #             'id': 'tpr4_agree',
                #             'text': "Does your understanding of calculating mean TPR wards match the tool's approach?",
                #             'type': 'scale',
                #             'min': 1,
                #             'max': 5,
                #             'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
                #         },
                #         'missing': {
                #             'id': 'tpr4_missing',
                #             'text': 'What would you refine?',
                #             'type': 'textarea',
                #             'required': False,
                #             'placeholder': '1-2 sentences'
                #         },
                #         'confidence': {
                #             'id': 'tpr4_conf',
                #             'text': 'How confident are you teaching this aspect to your colleagues?',
                #             'type': 'scale',
                #             'min': 0,
                #             'max': 100,
                #             'labels': ['Not confident', 'Very confident']
                #         },
                #         'teachback': {
                #             'id': 'tpr4_teach',
                #             'text': 'Describe how the mean TPR was computed across all wards?',
                #             'type': 'textarea',
                #             'required': True
                #         },
                #         'quiz1': {
                #             'id': 'tpr4_quiz1',
                #             'text': 'When TPR values vary a lot (skewed with outliers), which single-number summary is most appropriate?',
                #             'type': 'radio',
                #             'options': [
                #                 'Median',  # Correct
                #                 'Mean',
                #                 'Mode'
                #             ],
                #             'correct': 0
                #         },
                #         'quiz2': {
                #             'id': 'tpr4_quiz2',
                #             'text': 'True or false: If ward test counts differ greatly, report a test-weighted mean alongside the median and include the IQR for spread.',
                #             'type': 'radio',
                #             'options': [
                #                 'True',  # Correct
                #                 'False'
                #             ],
                #             'correct': 0
                #         }
                #     }
                # },

                # Topic 5: TPR Imputation - COMMENTED OUT (Not highlighted in Pretest schedule.docx)
                # 'tpr_imputation': {
                #     'title': 'TPR Imputation',
                #     'questions': {
                #         'model_selection': {
                #             'id': 'tpr5_model',
                #             'text': 'Which wards had missing TPR values and were imputed using spatial mean?',
                #             'type': 'model_comparison',
                #             'instruction': 'Choose your preferred answer (shows two at a time)'
                #         },
                #         'reason': {
                #             'id': 'tpr5_reason',
                #             'text': 'What stood out for you in the model answer chosen?',
                #             'type': 'text',
                #             'required': True
                #         },
                #         'agreement': {
                #             'id': 'tpr5_agree',
                #             'text': "Does your understanding of imputed TPR via spatial mean align with the tool's approach to imputation?",
                #             'type': 'scale',
                #             'min': 1,
                #             'max': 5,
                #             'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
                #         },
                #         'missing': {
                #             'id': 'tpr5_missing',
                #             'text': "What's missing/needs refinement?",
                #             'type': 'textarea',
                #             'required': False,
                #             'placeholder': '1-2 sentences'
                #         },
                #         'confidence': {
                #             'id': 'tpr5_conf',
                #             'text': 'How confident are you explaining imputation flags to colleagues?',
                #             'type': 'scale',
                #             'min': 0,
                #             'max': 100,
                #             'labels': ['Not confident', 'Very confident']
                #         },
                #         'teachback': {
                #             'id': 'tpr5_teach',
                #             'text': 'In your own words, explain how imputed TPR should influence decisions and communication.',
                #             'type': 'textarea',
                #             'required': True
                #         },
                #         'quiz': {
                #             'id': 'tpr5_quiz',
                #             'text': 'For wards with spatial-mean imputed TPR, you should...',
                #             'type': 'radio',
                #             'options': [
                #                 'treat estimates cautiously; flag for monitoring/validation',  # Correct
                #                 'treat them as high-certainty values',
                #                 'convert them to zero',
                #                 'exclude the wards from all analysis by default'
                #             ],
                #             'correct': 0
                #         }
                #     }
                # }
            }
        },

        'visualization': {
            'title': 'Visualization',
            'topics': {
                # Topic 1: TPR Distribution Map - COMMENTED OUT (Not highlighted in Pretest schedule.docx)
                # 'tpr_map': {
                #     'title': 'TPR Distribution Map',
                #     'questions': {
                #         'model_selection': {
                #             'id': 'viz1_model',
                #             'text': 'Plot the TPR distribution map. Using the TPR distribution map, identify one ward in the highest quartile and one in the lowest quartile. Describe the spatial pattern you notice (e.g., clustering, corridors, outliers).',
                #             'type': 'model_comparison',
                #             'instruction': 'Choose your preferred answer (shows two at a time)'
                #         },
                #         'reason': {
                #             'id': 'viz1_reason',
                #             'text': 'What stood out in the answer you chose?',
                #             'type': 'text',
                #             'required': True
                #         },
                #         'agreement': {
                #             'id': 'viz1_agree',
                #             'text': 'Does your understanding of the TPR map match what the tool explains?',
                #             'type': 'scale',
                #             'min': 1,
                #             'max': 5,
                #             'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
                #         },
                #         'missing': {
                #             'id': 'viz1_missing',
                #             'text': "What's missing/needs refinement?",
                #             'type': 'textarea',
                #             'required': False,
                #             'placeholder': '1-2 lines'
                #         },
                #         'confidence': {
                #             'id': 'viz1_conf',
                #             'text': 'How confident are you interpreting and/or describing the TPR map?',
                #             'type': 'scale',
                #             'min': 0,
                #             'max': 100,
                #             'labels': ['Not confident', 'Very confident']
                #         },
                #         'teachback': {
                #             'id': 'viz1_teach',
                #             'text': 'In your own words, how should the TPR distribution map be interpreted and used?',
                #             'type': 'textarea',
                #             'required': True
                #         },
                #         'quiz': {
                #             'id': 'viz1_quiz',
                #             'text': 'A deep-red ward on the TPR map most likely indicates...',
                #             'type': 'radio',
                #             'options': [
                #                 'a high fraction of positive tests among those tested in that ward',  # Correct
                #                 'high population',
                #                 'high certainty',
                #                 'high EVI'
                #             ],
                #             'correct': 0
                #         }
                #     }
                # },

                # Topic 2: EVI and Water Bodies Maps
                'evi_water': {
                    'title': 'EVI and Distance to Water Bodies',
                    'questions': {
                        'model_selection': {
                            'id': 'viz2_model',
                            'text': 'Plot the distance to water bodies and enhanced vegetation index distribution map and also produce the normalized versions of these maps. Compare the EVI and distance to water bodies raw maps. Compare EVI and distance to water bodies normalized maps. Which of the two variables will drive the composite score after normalization? Why do you think normalization is important?',
                            'type': 'model_comparison',
                            'instruction': 'Choose your preferred answer (shows two at a time)'
                        },
                        'reason': {
                            'id': 'viz2_reason',
                            'text': 'What stood out in the answer you chose?',
                            'type': 'text',
                            'required': True
                        },
                        'agreement': {
                            'id': 'viz2_agree',
                            'text': "Does your understanding of EVI vs normalized EVI match the tool's narrative?",
                            'type': 'scale',
                            'min': 1,
                            'max': 5,
                            'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
                        },
                        'missing': {
                            'id': 'viz2_missing',
                            'text': 'What would you refine?',
                            'type': 'textarea',
                            'required': False,
                            'placeholder': '1-2 sentences'
                        },
                        'confidence': {
                            'id': 'viz2_conf',
                            'text': 'How confident are you in explaining the purpose of normalization to your colleagues?',
                            'type': 'scale',
                            'min': 0,
                            'max': 100,
                            'labels': ['Not confident', 'Very confident']
                        },
                        'teachback': {
                            'id': 'viz2_teach',
                            'text': 'Paraphrase what normalization does and how it affects cross variable comparison.',
                            'type': 'textarea',
                            'required': True
                        },
                        'quiz': {
                            'id': 'viz2_quiz',
                            'text': 'Normalization mainly...',
                            'type': 'radio',
                            'options': [
                                'puts indicators on a common scale so they can be compared and combined',  # Correct
                                'removes outliers automatically',
                                'creates a normal (bell-curve) distribution',
                                'fixes missing data'
                            ],
                            'correct': 0
                        }
                    }
                },

                # Topic 3: Vulnerability Map
                'vulnerability_map': {
                    'title': 'Vulnerability Map',
                    'questions': {
                        'model_selection': {
                            'id': 'viz3_model',
                            'text': 'Plot the Vulnerability map (what it shows and how to use it). Find a ward with moderate risk but high vulnerability.',
                            'type': 'model_comparison',
                            'instruction': 'Choose your preferred answer (shows two at a time)'
                        },
                        'reason': {
                            'id': 'viz3_reason',
                            'text': 'What stood out in the answer you chose?',
                            'type': 'text',
                            'required': True
                        },
                        'agreement': {
                            'id': 'viz3_agree',
                            'text': 'Does your understanding of the vulnerability layer match what the tool describes?',
                            'type': 'scale',
                            'min': 1,
                            'max': 5,
                            'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
                        },
                        'missing': {
                            'id': 'viz3_missing',
                            'text': "What's missing?",
                            'type': 'textarea',
                            'required': False,
                            'placeholder': '1-2 sentences'
                        },
                        'confidence': {
                            'id': 'viz3_conf',
                            'text': 'Confidence using vulnerability to adjust actions?',
                            'type': 'scale',
                            'min': 0,
                            'max': 100,
                            'labels': ['Not confident', 'Very confident']
                        },
                        'teachback': {
                            'id': 'viz3_teach',
                            'text': 'Paraphrase how vulnerability differs from risk and how it should influence planning.',
                            'type': 'textarea',
                            'required': True
                        },
                        'quiz': {
                            'id': 'viz3_quiz',
                            'text': 'What does a high vulnerability risk index on the map mean...',
                            'type': 'radio',
                            'options': [
                                'Greater vulnerability of the ward relative to others',  # Correct
                                'measurement certainty',
                                'mosquito abundance only',
                                'the same thing as risk'
                            ],
                            'correct': 0
                        }
                    }
                },

                # Topic 4: ITN Distribution Map - COMMENTED OUT (Not highlighted in Pretest schedule.docx)
                # 'itn_distribution': {
                #     'title': 'ITN Distribution Map',
                #     'questions': {
                #         'model_selection': {
                #             'id': 'viz4_model',
                #             'text': 'Plot the ITN distribution map (highlighting reprioritized vs prioritized states). On the ITN distribution view, find one ward that changed status (reprioritized vs prioritized) after changing the urbanicity index. Describe how its planned nets allocation changed.',
                #             'type': 'model_comparison',
                #             'instruction': 'Choose your preferred answer (shows two at a time)'
                #         },
                #         'reason': {
                #             'id': 'viz4_reason',
                #             'text': 'What stood out in the answer you chose?',
                #             'type': 'text',
                #             'required': True
                #         },
                #         'agreement': {
                #             'id': 'viz4_agree',
                #             'text': "Does your understanding of status changes and ITN allocations match the tool's logic?",
                #             'type': 'scale',
                #             'min': 1,
                #             'max': 5,
                #             'labels': ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
                #         },
                #         'missing': {
                #             'id': 'viz4_missing',
                #             'text': 'What needs refinement?',
                #             'type': 'textarea',
                #             'required': False,
                #             'placeholder': '1-2 sentences'
                #         },
                #         'confidence': {
                #             'id': 'viz4_conf',
                #             'text': 'Confidence explaining how reprioritization affects net counts?',
                #             'type': 'scale',
                #             'min': 0,
                #             'max': 100,
                #             'labels': ['Not confident', 'Very confident']
                #         },
                #         'teachback': {
                #             'id': 'viz4_teach',
                #             'text': 'In your words, how do priority state changes translate into ITN planning?',
                #             'type': 'textarea',
                #             'required': True
                #         },
                #         'quiz': {
                #             'id': 'viz4_quiz',
                #             'text': 'If Ward X shifts from prioritized to reprioritized (scale down), the ITN plan should...',
                #             'type': 'radio',
                #             'options': [
                #                 'decrease planned nets while applying equity safeguards (e.g., protect slum pockets)',  # Correct
                #                 'remove all nets entirely',
                #                 'auto-raise to 100% coverage',
                #                 'only change uncertainty'
                #             ],
                #             'correct': 0
                #         }
                #     }
                # }
            }
        }
    }

    @classmethod
    def get_all_questions(cls) -> List[Dict[str, Any]]:
        """Return all questions in order for the survey."""
        questions = []
        question_number = 1

        for section_key, section_data in cls.SECTIONS.items():
            for topic_key, topic_data in section_data['topics'].items():
                for question_key, question_data in topic_data['questions'].items():
                    question = question_data.copy()
                    question['section'] = section_data['title']
                    question['topic'] = topic_data['title']
                    question['number'] = question_number
                    questions.append(question)
                    question_number += 1

        return questions

    @classmethod
    def get_reduced_questions(cls) -> List[Dict[str, Any]]:
        """
        Return reduced question set for survey.

        Each topic includes:
        1. model_selection (always included)
        2. One randomly selected question from remaining questions

        Total: 28 questions (14 topics × 2 questions each)
        Original: 99 questions
        """
        questions = []
        question_number = 1

        for section_key, section_data in cls.SECTIONS.items():
            for topic_key, topic_data in section_data['topics'].items():
                # 1. Always include model_selection
                if 'model_selection' in topic_data['questions']:
                    model_q = topic_data['questions']['model_selection'].copy()
                    model_q['section'] = section_data['title']
                    model_q['topic'] = topic_data['title']
                    model_q['number'] = question_number
                    questions.append(model_q)
                    question_number += 1

                # 2. Randomly select one additional question
                other_keys = [k for k in topic_data['questions'].keys() if k != 'model_selection']

                if other_keys:
                    random_key = random.choice(other_keys)
                    random_q = topic_data['questions'][random_key].copy()
                    random_q['section'] = section_data['title']
                    random_q['topic'] = topic_data['title']
                    random_q['number'] = question_number
                    questions.append(random_q)
                    question_number += 1

        return questions

    @classmethod
    def get_question_by_id(cls, question_id: str) -> Dict[str, Any]:
        """Get a specific question by its ID."""
        for section_data in cls.SECTIONS.values():
            for topic_data in section_data['topics'].values():
                for question_data in topic_data['questions'].values():
                    if question_data.get('id') == question_id:
                        return question_data
        return None

    @classmethod
    def get_total_questions(cls) -> int:
        """Get total number of questions."""
        total = 0
        for section_data in cls.SECTIONS.values():
            for topic_data in section_data['topics'].values():
                total += len(topic_data['questions'])
        return total

    @classmethod
    def get_section_summary(cls) -> Dict[str, int]:
        """Get summary of questions per section."""
        summary = {}
        for section_key, section_data in cls.SECTIONS.items():
            count = 0
            for topic_data in section_data['topics'].values():
                count += len(topic_data['questions'])
            summary[section_data['title']] = count
        return summary

    @classmethod
    def get_questions_for_trigger(cls, trigger_type: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get questions based on trigger type - returns reduced question set (28 questions)."""
        # Return reduced question set: model_selection + 1 random question per topic
        return cls.get_reduced_questions()

    @classmethod
    def validate_response(cls, question_id: str, response: Any) -> bool:
        """Validate a response based on question type."""
        # Get the question by ID
        question = cls.get_question_by_id(question_id)

        if not question:
            return False

        question_type = question.get('type')

        # Validate based on question type
        if question_type == 'text':
            # Text responses should be non-empty strings
            return isinstance(response, str) and len(response.strip()) > 0

        elif question_type == 'textarea':
            # Textarea responses should be non-empty strings
            return isinstance(response, str) and len(response.strip()) > 0

        elif question_type == 'model_comparison':
            # Model comparison should have text response
            return isinstance(response, str) and len(response.strip()) > 0

        elif question_type == 'scale':
            # Scale responses should be numbers within range
            if not isinstance(response, (int, float)):
                try:
                    response = float(response)
                except (ValueError, TypeError):
                    return False

            min_val = question.get('min', 0)
            max_val = question.get('max', 100)
            return min_val <= response <= max_val

        elif question_type == 'radio':
            # Radio responses should be valid option indices or values
            options = question.get('options', [])
            if isinstance(response, int):
                return 0 <= response < len(options)
            elif isinstance(response, str):
                return response in options
            return False

        elif question_type == 'rating_matrix':
            # Rating matrix should be a dictionary
            return isinstance(response, dict) and len(response) > 0

        # Default validation - accept any non-null response
        return response is not None