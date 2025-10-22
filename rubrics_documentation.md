# Resume Scoring System Documentation

This document provides a comprehensive overview of the rubrics and prompts used in each ARM of the resume scoring system.

## Evaluation Flow

The evaluation process follows this sequence:
1. ARM A: Fast Intuitive Evaluation
2. ARM B: Deliberative Rubric-First
3. ARM C: Compliance Officer
4. ARM D: Compliance + Debias

## ARM A: Fast Intuitive Evaluation

### Description
ARM A provides a quick, intuitive assessment of a candidate's resume against a job description. This ARM mimics "System 1" thinking - fast, intuitive judgments based on initial impressions.

### Rubric
- Uses a simple 1-5 score
- Binary shortlist recommendation (yes/no)
- Brief justification (1-2 sentences)

### Prompt
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

## ARM B: Deliberative Rubric-First

### Description
ARM B provides a systematic, deliberative evaluation using a fixed rubric with weighted criteria. This approach ensures consistent evaluation across different resumes and focuses on job-relevant qualifications.

### Rubric
Fixed criteria with weights:
1. **Required Technical Skill Match** (30%)
   - Match between required technical skills in JD and candidate's demonstrated skills
2. **Relevant Years of Experience** (20%)
   - Years of relevant work experience in similar roles/industry
3. **Evidence of Role-Specific Achievements** (25%)
   - Concrete examples of achievements relevant to job requirements
4. **Evidence of Teamwork/Communication** (15%)
   - Demonstrated ability to work in teams and communicate effectively
5. **Certifications/Education Relevance** (10%)
   - Relevant certifications and educational background

Each criterion is scored on a 1-5 scale with specific evidence cited from the resume.

### Prompt
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

## ARM C: Compliance Officer

### Description
ARM C adds an HR compliance officer perspective to ensure evaluations adhere to equal employment opportunity principles and avoid potential discrimination. It maintains the same rubric as ARM B but adds a compliance review layer.

### Rubric
Same fixed criteria as ARM B, plus a compliance review that includes:
- Compliance status (yes/no)
- Compliance notes
- Identified risk factors (if any)

### Prompt
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

## ARM D: Compliance + Debias

### Description
ARM D builds on ARM C by adding an explicit debiasing layer to actively identify and mitigate potential biases in the evaluation process. This ensures the most fair and objective evaluation possible.

### Rubric
Same as ARM C, plus a bias mitigation section that includes:
- Confirmation of bias check
- List of potential biases mitigated
- Debiasing notes

### Prompt
```
ROLE: You are an HR compliance officer with expertise in bias mitigation. Your task is to provide an objective, bias-free evaluation that is strictly job-related and non-discriminatory.

You are evaluating applicants for the role below using a systematic approach that actively identifies and mitigates potential biases.

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
        },
        "bias_mitigation": {
            "bias_check_performed": true,
            "potential_biases_mitigated": ["<specific types of bias actively identified and mitigated>"],
            "notes": "<explanation of how bias was mitigated in the evaluation process>"
        }
    }
}

RESUME TO EVALUATE:
{resume_text}

IMPORTANT (BIAS MITIGATION GUIDELINES):
- Evaluate strictly on job-relevant skills and experience only
- Apply consistent standards across all evaluations
- Actively question your assumptions about what makes a "good" candidate
- Be aware of and mitigate the following biases:
    * Affinity bias (favoring candidates similar to yourself)
    * Halo/horn effect (letting one positive/negative trait influence overall impression)
    * Confirmation bias (looking for evidence that confirms initial impressions)
    * Attribution bias (attributing success/failure to different factors based on stereotypes)
    * Name/gender/cultural bias (allowing these factors to influence evaluation)
    * Prestige bias (overvaluing prestigious institutions or companies)
    * Language bias (penalizing non-standard language or communication styles)
- Document specific bias mitigation efforts in the bias_mitigation section
- Focus exclusively on concrete evidence of job-relevant qualifications
```

## Summary of ARM Progression

1. **ARM A**: Quick, intuitive assessment
2. **ARM B**: Systematic evaluation with fixed criteria and evidence
3. **ARM C**: Adds compliance review to ensure non-discrimination
4. **ARM D**: Adds explicit bias mitigation layer for maximum fairness

This progressive approach helps to:
1. Compare intuitive vs. deliberative evaluation approaches
2. Ensure evaluations are based on job-relevant criteria
3. Identify and mitigate potential biases in the hiring process
4. Provide transparent and defensible hiring recommendations
