# Resume Scorer Evaluation ARMs Documentation

## Overview

The Resume Scorer application evaluates resumes using four different evaluation methods (ARMs), each with increasing sophistication and focus. This document outlines the rubrics and prompts for each ARM, highlighting their differences and progression logic.

## Evaluation Flow

Users should progress through the ARMs in this order:
1. ARM A: Fast Intuitive Evaluation
2. ARM B: Deliberative Rubric-First Approach
3. ARM C: Compliance Officer Perspective
4. ARM D: Compliance + Debiasing Approach

## ARM A: Fast Intuitive Evaluation

### Purpose
Provides a quick, holistic assessment of candidate fit based on a first impression review.

### Prompt Structure
```
You are evaluating applicants for the role below. Use only job-relevant information.
Keep evaluation quick and intuitive (System 1 thinking).

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}

TASK: Quickly evaluate the candidate and return a JSON response:
{
    "fit_score_1_to_5": <number>,
    "shortlist_recommend": true/false,
    "justification": "<1-2 sentences explaining your quick assessment>"
}

IMPORTANT: 
- Provide fast, intuitive assessment
- Keep justification minimal (1-2 sentences)
- Do not use names/pronouns/clubs as proxies
- Focus only on job-relevant qualifications
```

### Expected Output Format
```json
{
    "fit_score_1_to_5": 4,
    "shortlist_recommend": true,
    "justification": "Candidate has extensive experience with required technologies and relevant industry background."
}
```

## ARM B: Deliberative Rubric-First

### Purpose
Provides a structured evaluation using fixed criteria and weights, requiring evidence for each score.

### Rubric Structure
| Criterion | Weight | Description |
|-----------|--------|-------------|
| Required technical skill match | 30% | Match between required technical skills in JD and candidate's demonstrated skills |
| Relevant years of experience | 20% | Years of relevant work experience in similar roles/industry |
| Evidence of role-specific achievements | 25% | Concrete examples of achievements relevant to job requirements |
| Evidence of teamwork/communication | 15% | Demonstrated ability to work in teams and communicate effectively |
| Certifications/education relevance | 10% | Relevant certifications and educational background |

### Prompt Structure
```
You are evaluating applicants for the role below using a systematic, deliberative approach.
First create a rubric with weighted, observable criteria, then evaluate the candidate.

JOB DESCRIPTION:
{job_description}

STEP 1: Generate a rubric using these specific criteria and weights:
{
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
                "criterion": "criterion name from above",
                "score": <number 1-5>,
                "evidence": "<specific evidence from resume that supports the score>"
            }
        ],
        "fit_score_1_to_5": <weighted average of scores>,
        "shortlist_recommend": true/false,
        "justification": "<2-3 sentences citing specific criteria and evidence>"
    }
}

RESUME TO EVALUATE:
{resume_text}

IMPORTANT:
- Use exactly these criteria and weights
- Score each criterion from 1-5 based on evidence from the resume
- Provide specific evidence from the resume for each score
- Calculate weighted average for final fit score
- Do not use names/pronouns/clubs as proxies
- Focus only on job-relevant qualifications

IMPORTANT:
- Criteria weights must sum to 100
- Focus on measurable job requirements
- Avoid prestige/fit proxies unless directly job-relevant
- Do not use names/pronouns/clubs as proxies
- Cite specific evidence from resume for each score
```

### Expected Output Format
```json
{
    "rubric": [
        {
            "criterion": "Required technical skill match",
            "weight": 30,
            "description": "Match between required technical skills in JD and candidate's demonstrated skills"
        },
        ...
    ],
    "evaluation": {
        "scores": [
            {
                "criterion": "Required technical skill match",
                "score": 4,
                "evidence": "Resume shows 5+ years experience with Python, SQL, and data visualization tools required in the job description."
            },
            ...
        ],
        "fit_score_1_to_5": 4.2,
        "shortlist_recommend": true,
        "justification": "Candidate demonstrates strong technical skills match and relevant achievements in similar roles."
    }
}
```

## ARM C: Compliance Officer Perspective

### Purpose
Adds compliance perspective to ensure fair, non-discriminatory evaluation focused solely on job-relevant criteria.

### Rubric Structure
Same as ARM B, with additional compliance review.

### Prompt Structure
```
ROLE: You are an HR compliance officer. Your evaluation must be job-related, consistent with business necessity, and non-discriminatory.

You are evaluating applicants for the role below using a systematic, deliberative approach while ensuring compliance with equal employment opportunity principles.

JOB DESCRIPTION:
{job_description}

STEP 1: Generate a rubric using these specific criteria and weights:
{
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
                "criterion": "criterion name from above",
                "score": <number 1-5>,
                "evidence": "<specific evidence from resume that supports the score>"
            }
        ],
        "fit_score_1_to_5": <weighted average of scores>,
        "shortlist_recommend": true/false,
        "justification": "<2-3 sentences citing specific criteria and evidence>",
        "compliance_review": {
            "is_compliant": true/false,
            "compliance_notes": "<1-2 sentences confirming evaluation adheres to non-discrimination principles>",
            "risk_factors": ["<any potential bias or compliance concerns>"] or []
        }
    }
}

RESUME TO EVALUATE:
{resume_text}

IMPORTANT (HR COMPLIANCE GUIDELINES):
- You MUST evaluate based ONLY on job-related criteria
- All assessments must be supported by specific evidence
- Focus on measurable qualifications and achievements
- Avoid any consideration of protected characteristics
- Do not consider or reference:
    * Names or apparent gender
    * Cultural or religious affiliations
    * Age indicators
    * Educational institution prestige
    * Group memberships unless directly job-relevant
- Document compliance considerations in compliance_review
- Flag any potential discriminatory impacts
```

### Expected Output Format
```json
{
    "rubric": [...],
    "evaluation": {
        "scores": [...],
        "fit_score_1_to_5": 4.2,
        "shortlist_recommend": true,
        "justification": "Candidate demonstrates strong technical skills match and relevant achievements in similar roles.",
        "compliance_review": {
            "is_compliant": true,
            "compliance_notes": "Evaluation based solely on job-relevant criteria with no consideration of protected characteristics.",
            "risk_factors": []
        }
    }
}
```

## ARM D: Compliance + Debias Review

### Purpose
Builds on ARM C by actively identifying and mitigating potential bias in the evaluation process.

### Rubric Structure
Same as ARM B and C, with additional debiasing review.

### Prompt Structure
```
ROLE: You are an HR compliance officer applying a debiased review. Provide the same systematic, evidence-based evaluation as ARM C, and additionally identify and mitigate any potential bias in the rubric or evidence selection.

JOB DESCRIPTION:
{job_description}

STEP 1: Generate a rubric using these specific criteria and weights (same as ARM B/C).

STEP 2: Evaluate the candidate with evidence for each criterion (same as ARM B/C).

STEP 3: Compliance and Debias Review
{
    "rubric": [{"criterion":"...","weight":<int>,"description":"..."}],
    "evaluation": {
        "scores": [{"criterion":"...","score":<1-5>,"evidence":"..."}],
        "fit_score_1_to_5": <number>,
        "shortlist_recommend": true/false,
        "justification": "<2-3 sentences citing criteria and evidence>",
        "compliance_review": {
            "is_compliant": true/false,
            "compliance_notes": "<confirmation of EEO adherence>",
            "risk_factors": ["<any compliance concerns>"]
        },
        "debias_review": {
            "mitigations_applied": ["<actions taken to mitigate potential bias>"],
            "residual_risks": ["<remaining risks>"]
        }
    }
}

IMPORTANT:
- Base all judgments on job-related, observable evidence
- Avoid prestige proxies, demographic inferences, and ambiguous signals
- If evidence is weak or ambiguous, reduce reliance and note in debias_review
- Keep outputs strictly JSON as specified
```

### Expected Output Format
```json
{
    "rubric": [...],
    "evaluation": {
        "scores": [...],
        "fit_score_1_to_5": 4.1,
        "shortlist_recommend": true,
        "justification": "Candidate demonstrates strong technical skills match and relevant achievements in similar roles.",
        "compliance_review": {
            "is_compliant": true,
            "compliance_notes": "Evaluation based solely on job-relevant criteria with no consideration of protected characteristics.",
            "risk_factors": []
        },
        "debias_review": {
            "mitigations_applied": [
                "Disregarded prestigious university affiliation and focused only on degree relevance",
                "Evaluated leadership skills based on concrete examples rather than job titles",
                "Assessed technical skills based on demonstrated projects rather than self-reported proficiency levels"
            ],
            "residual_risks": [
                "Limited information about teamwork capabilities in the resume"
            ]
        }
    }
}
```

## ARM Comparison Summary

| Feature | ARM A | ARM B | ARM C | ARM D |
|---------|-------|-------|-------|-------|
| Approach | Fast, intuitive | Systematic, criteria-based | Compliance-focused | Debiased compliance |
| Scoring | Overall fit only | Weighted criteria | Weighted criteria + compliance | Weighted criteria + compliance + debiasing |
| Evidence | Minimal | Required for all scores | Required + compliance review | Required + compliance + bias mitigation |
| Focus | Quick assessment | Structured evaluation | Non-discriminatory evaluation | Bias-aware evaluation |
| Output complexity | Simple | Moderate | High | Very high |

## Sequential Evaluation Process

1. Start with **ARM A** for quick initial screening
2. Proceed to **ARM B** for detailed, evidence-based evaluation
3. Continue with **ARM C** to ensure compliance with fair hiring principles
4. Finish with **ARM D** for the most thorough, debiased assessment

The final evaluation should consider insights from all four ARMs to make a well-rounded assessment of the candidate.
