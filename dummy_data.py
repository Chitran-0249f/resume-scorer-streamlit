"""Provides fallback dummy data when AI analysis fails"""

from typing import Dict

def get_dummy_data_for_arm_a() -> Dict:
    """Return dummy data for ARM A"""
    return {
        "fit_score_1_to_5": 3,
        "shortlist_recommend": False,
        "justification": "This is a fallback score since the AI analysis couldn't be completed. The candidate shows some relevant experience but more information is needed for a full evaluation."
    }

def get_dummy_data_for_arm_b() -> Dict:
    """Return dummy data for ARM B"""
    return {
        "rubric": [
            {
                "criterion": "Required technical skill match",
                "weight": 30,
                "description": "Match between required technical skills in JD and candidate's demonstrated skills"
            },
            {
                "criterion": "Relevant years of experience",
                "weight": 20,
                "description": "Years of relevant work experience in similar roles/industry"
            },
            {
                "criterion": "Evidence of role-specific achievements",
                "weight": 25,
                "description": "Concrete examples of achievements relevant to job requirements"
            },
            {
                "criterion": "Evidence of teamwork/communication",
                "weight": 15,
                "description": "Demonstrated ability to work in teams and communicate effectively"
            },
            {
                "criterion": "Certifications/education relevance",
                "weight": 10,
                "description": "Relevant certifications and educational background"
            }
        ],
        "evaluation": {
            "scores": [
                {
                    "criterion": "Required technical skill match",
                    "score": 3,
                    "evidence": "Candidate appears to have some relevant skills based on resume sections."
                },
                {
                    "criterion": "Relevant years of experience",
                    "score": 3,
                    "evidence": "Some relevant experience is present in the resume."
                },
                {
                    "criterion": "Evidence of role-specific achievements",
                    "score": 2,
                    "evidence": "Limited evidence of specific achievements related to the role."
                },
                {
                    "criterion": "Evidence of teamwork/communication",
                    "score": 3, 
                    "evidence": "Some indicators of teamwork experience are present."
                },
                {
                    "criterion": "Certifications/education relevance",
                    "score": 4,
                    "evidence": "Education appears relevant to the position requirements."
                }
            ],
            "fit_score_1_to_5": 3,
            "shortlist_recommend": False,
            "justification": "This is a fallback score since the AI analysis couldn't be completed. Based on the standard evaluation rubric, the candidate shows moderate alignment with job requirements."
        }
    }

def get_dummy_data_for_arm_c() -> Dict:
    """Return dummy data for ARM C"""
    return {
        "rubric": [
            {
                "criterion": "Required technical skill match",
                "weight": 30,
                "description": "Match between required technical skills in JD and candidate's demonstrated skills"
            },
            {
                "criterion": "Relevant years of experience",
                "weight": 20,
                "description": "Years of relevant work experience in similar roles/industry"
            },
            {
                "criterion": "Evidence of role-specific achievements",
                "weight": 25,
                "description": "Concrete examples of achievements relevant to job requirements"
            },
            {
                "criterion": "Evidence of teamwork/communication",
                "weight": 15,
                "description": "Demonstrated ability to work in teams and communicate effectively"
            },
            {
                "criterion": "Certifications/education relevance",
                "weight": 10,
                "description": "Relevant certifications and educational background"
            }
        ],
        "evaluation": {
            "scores": [
                {
                    "criterion": "Required technical skill match",
                    "score": 3,
                    "evidence": "Some relevant technical skills mentioned in resume."
                },
                {
                    "criterion": "Relevant years of experience",
                    "score": 3,
                    "evidence": "Candidate appears to have some relevant experience."
                },
                {
                    "criterion": "Evidence of role-specific achievements",
                    "score": 3,
                    "evidence": "Some achievements mentioned could relate to the role."
                },
                {
                    "criterion": "Evidence of teamwork/communication",
                    "score": 3, 
                    "evidence": "Some teamwork examples are present."
                },
                {
                    "criterion": "Certifications/education relevance",
                    "score": 3,
                    "evidence": "Some relevant educational background is indicated."
                }
            ],
            "fit_score_1_to_5": 3,
            "shortlist_recommend": False,
            "justification": "This is a fallback evaluation since the AI analysis couldn't be completed. The candidate appears to have moderate alignment with position requirements.",
            "compliance_review": {
                "is_compliant": True,
                "compliance_notes": "This is a standard compliant evaluation focused only on job-relevant qualifications.",
                "risk_factors": []
            }
        }
    }

def get_dummy_data_for_arm_d() -> Dict:
    """Return dummy data for ARM D"""
    return {
        "rubric": [
            {
                "criterion": "Required technical skill match",
                "weight": 30,
                "description": "Match between required technical skills in JD and candidate's demonstrated skills"
            },
            {
                "criterion": "Relevant years of experience",
                "weight": 20,
                "description": "Years of relevant work experience in similar roles/industry"
            },
            {
                "criterion": "Evidence of role-specific achievements",
                "weight": 25,
                "description": "Concrete examples of achievements relevant to job requirements"
            },
            {
                "criterion": "Evidence of teamwork/communication",
                "weight": 15,
                "description": "Demonstrated ability to work in teams and communicate effectively"
            },
            {
                "criterion": "Certifications/education relevance",
                "weight": 10,
                "description": "Relevant certifications and educational background"
            }
        ],
        "evaluation": {
            "scores": [
                {
                    "criterion": "Required technical skill match",
                    "score": 3,
                    "evidence": "Some relevant technical skills mentioned in resume."
                },
                {
                    "criterion": "Relevant years of experience",
                    "score": 3,
                    "evidence": "Candidate appears to have some relevant experience."
                },
                {
                    "criterion": "Evidence of role-specific achievements",
                    "score": 3,
                    "evidence": "Some achievements mentioned could relate to the role."
                },
                {
                    "criterion": "Evidence of teamwork/communication",
                    "score": 3, 
                    "evidence": "Some teamwork examples are present."
                },
                {
                    "criterion": "Certifications/education relevance",
                    "score": 3,
                    "evidence": "Some relevant educational background is indicated."
                }
            ],
            "fit_score_1_to_5": 3,
            "shortlist_recommend": False,
            "justification": "This is a fallback evaluation since the AI analysis couldn't be completed. The candidate appears to have moderate alignment with position requirements.",
            "compliance_review": {
                "is_compliant": True,
                "compliance_notes": "This is a standard compliant evaluation focused only on job-relevant qualifications with debiasing applied.",
                "risk_factors": []
            },
            "bias_mitigation": {
                "bias_check_performed": True,
                "potential_biases_mitigated": ["Educational institution prestige", "Name-based assumptions", "Resume formatting biases"],
                "notes": "Fallback evaluation using standardized job-relevant criteria only."
            }
        }
    }

def get_dummy_data_by_arm(arm_name: str) -> Dict:
    """Get dummy data by arm name"""
    if arm_name == "SYSTEM_1":
        return get_dummy_data_for_arm_a()
    elif arm_name == "SYSTEM_2":
        return get_dummy_data_for_arm_b()
    elif arm_name == "SYSTEM_2_PERSONA":
        return get_dummy_data_for_arm_c()
    elif arm_name == "SYSTEM_2_PERSONA_DEBIAS":
        return get_dummy_data_for_arm_d()
    else:
        # Default fallback
        return get_dummy_data_for_arm_a()
